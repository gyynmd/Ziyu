#!/usr/bin/env python3
"""Build an index-preserving CJK collection inside a finite font task.

Each stock face remains the base: cmap/UVS, glyph IDs, layout tables, names,
style and line metrics stay at their original indexes. Supported donor outlines
replace existing encoded slots. Specialized faces and uncovered glyphs stay stock.
No system XML, live font, user source or mounting implementation is modified.

Adapted from LuoShu's composite_collection_build.py (GPL-3.0); Ziyu integration
uses byte-verified stock snapshots and the selected, already-instanced mix donor.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTCollection, TTFont, TTLibError
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib.builder import buildVarData, buildVarIdxMap

from composite_collection_contract import collection_faces
import composite_collection_contract
from composite_font import LATIN_CODEPOINTS, DIGIT_CODEPOINTS, _pick_face, _progress
import font_inventory as stock_inventory
import font_source_profile
import stock_font_snapshot

SCHEMA = 'composite-collection-build-v1'
PROTECTED = ('cmap', 'GSUB', 'GPOS', 'GDEF', 'name', 'hhea', 'OS/2', 'vhea', 'vmtx', 'VORG',
             'fvar', 'avar', 'STAT', 'MVAR', 'BASE', 'cvar', 'VVAR')
CJK_RANGES = ((0x2E80, 0x31EF), (0x3400, 0x9FFF), (0xF900, 0xFAFF),
              (0xFF00, 0xFFEF), (0x20000, 0x323AF))
MAX_COLLECTION_TARGETS = 16
MAX_COLLECTION_BYTES = 384 * 1024 * 1024
MAX_COLLECTION_FACE_TOTAL = 512
MAX_STOCK_FILE_BYTES = 128 * 1024 * 1024
MAX_MIX_SOURCE_BYTES = 128 * 1024 * 1024
PROOF_DIRECTORY = '.luoshu-collection-proofs'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def identity(path):
    value = Path(path).stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def role(cp):
    if cp in DIGIT_CODEPOINTS:
        return 'digit'
    if cp in LATIN_CODEPOINTS:
        return 'latin'
    return 'cjk' if any(lo <= cp <= hi for lo, hi in CJK_RANGES) else None


def protected(font):
    recalc = font.recalcBBoxes
    font.recalcBBoxes = False
    try:
        return _protected(font)
    finally:
        font.recalcBBoxes = recalc


def _protected(font):
    # Canonical compiled bytes survive a FontTools round trip. Keeping the
    # original glyph order makes the retained layout/UVS indexes meaningful.
    # getTableData returns original bytes for lazy tables, compiled bytes for
    # loaded ones. Load every protected table before hashing either snapshot.
    for tag in PROTECTED:
        if tag in font:
            font[tag]
    tables = {}
    for tag in PROTECTED:
        if tag not in font:
            continue
        if tag == 'vmtx' and 'glyf' in font:
            # TrueType vertical origins are yMax + top side bearing. A new
            # outline needs a different bearing to keep that same origin.
            glyf = font['glyf']
            tables[tag] = canonical({name: [advance, getattr(glyf[name], 'yMax', 0) + bearing]
                                     for name, (advance, bearing) in font['vmtx'].metrics.items()})
            continue
        data = font.getTableData(tag)
        # Metric serialization may change its run-length compression count.
        # Every other header field still binds the original line metrics.
        if tag in ('hhea', 'vhea'):
            data = data[:-2]
        tables[tag] = hashlib.sha256(data).hexdigest()
    return {'tables': tables, 'glyphOrder': canonical(font.getGlyphOrder()),
            'frame': [font['head'].unitsPerEm, font['head'].xMin, font['head'].yMin,
                      font['head'].xMax, font['head'].yMax]}


def specialized(font):
    # Color glyphs can draw from auxiliary tables or embedded bitmap/SVG
    # assets. Replacing only their base outline would silently change the
    # glyph while leaving those color layers stale, so preserve the OEM face.
    if any(tag in font for tag in font_source_profile.COLOR_TABLES):
        return True
    names = font['name'] if 'name' in font else None
    label = ' '.join(filter(None, (names.getDebugName(i) for i in (1, 2, 16, 17)))) if names else ''
    return (bool(font['post'].isFixedPitch) if 'post' in font else False) or any(
        word in label.lower() for word in ('mono', 'serif', 'emoji', 'symbol', 'icon')) or bool(
        font['head'].macStyle & 2 or ('OS/2' in font and font['OS/2'].fsSelection & 1))


def target_weight(font):
    return font_source_profile._weight(font)


def face_identity(font):
    return {
        'weight': target_weight(font),
        'style': font_source_profile._best_subfamily(font),
        'axes': font_source_profile._axes(font),
    }


def draw_record(glyphs, name):
    pen = DecomposingRecordingPen(glyphs)
    glyphs[name].draw(pen)
    return pen


def guard_retained_components(font, mapping):
    if 'glyf' in font:
        glyf = font['glyf']
        for name in font.getGlyphOrder():
            if name in mapping:
                continue  # Its complete outline will be replaced.
            raw = getattr(glyf.glyphs[name], 'data', None)
            if raw is not None and (len(raw) < 2 or int.from_bytes(raw[:2], 'big', signed=True) >= 0):
                continue
            glyph = glyf[name]
            if glyph.isComposite() and any(component.glyphName in mapping for component in glyph.components):
                raise ValueError('原厂保留组合字形依赖被替换槽，当前不能保持其完整形状与边界')
    elif 'CFF ' in font and not hasattr(font['CFF '].cff.topDictIndex[0], 'ROS'):
        # Non-CID CFF can have seac components addressed by standard names.
        glyphs = font.getGlyphSet()
        for name in font.getGlyphOrder():
            if name in mapping:
                continue
            pen = RecordingPen()
            glyphs[name].draw(pen)
            if any(operation == 'addComponent' and arguments[0] in mapping
                   for operation, arguments in pen.value):
                raise ValueError('原厂保留 CFF 组合字形依赖被替换槽，当前不能保持其完整形状与边界')


def freeze_horizontal_variations(font, mapping):
    """Detach only replaced slots from stock width/side-bearing variation data.

    Keep the existing store and each retained glyph's exact indices. In
    particular, an implicit advance mapping must be expanded before changing
    selected slots; editing a shared delta row would corrupt uncovered glyphs.
    """
    if 'HVAR' not in font:
        return
    table = font['HVAR'].table
    store = table.VarStore
    if len(store.VarData) >= 65535:
        raise ValueError('水平变化存储没有可用索引')
    zero = len(store.VarData) << 16
    store.VarData.append(buildVarData([], [[]], optimize=False))
    store.VarDataCount = len(store.VarData)
    order = font.getGlyphOrder()
    for field in ('AdvWidthMap', 'LsbMap', 'RsbMap'):
        old = getattr(table, field, None)
        if old is None and field != 'AdvWidthMap':
            continue
        indices = [zero if name in mapping else (old.mapping[name] if old else index)
                   for index, name in enumerate(order)]
        setattr(table, field, buildVarIdxMap(indices, order))


def retained_vertical_deltas(font, name):
    if 'gvar' not in font or 'vmtx' not in font:
        return []
    if 'VVAR' in font and getattr(font['VVAR'].table, 'TsbMap', None) is not None:
        raise ValueError('可变 TrueType 垂直侧距映射需要独立重编译，不能沿用旧轮廓数据')
    coordinates, controls = font['glyf']._getCoordinatesAndControls(
        name, font['hmtx'].metrics, font['vmtx'].metrics)
    from copy import deepcopy
    values = []
    for original in font['gvar'].variations.get(name, []):
        variation = deepcopy(original)
        variation.calcInferredDeltas(coordinates, controls.endPts)
        top, bottom = variation.coordinates[-2:]
        if any(top) or any(bottom):
            values.append((variation.axes, top, bottom))
    return values


def replace_face(font, donor, recordings):
    target = face_identity(font)
    donor_info = face_identity(donor)
    donor_info['weight'] = target_weight(donor)
    donor_info['axes'] = font_source_profile._axes(donor)
    donor_report = {
        'targetWeight': target['weight'], 'targetStyle': target['style'],
        'donorWeight': donor_info['weight'], 'donorAxes': donor_info['axes'],
        'selectedAxesTraceable': False,
        'selectedAxesNote': '组合产物已静态绑定生成时的选择；原始选轴值未保存在组合库清单中',
    }
    kind = 'glyf' if 'glyf' in font else 'CFF ' if 'CFF ' in font else 'CFF2' if 'CFF2' in font else None
    if specialized(font):
        return {'mode': 'retained-specialized', 'replaced': {}, 'uncovered': 0,
                'outline': kind, **donor_report, 'targetStylePreserved': True}
    if kind is None:
        raise ValueError('本机 CJK 集合包含不支持的轮廓')
    cmap, source = font.getBestCmap() or {}, donor.getBestCmap() or {}
    source_glyphs = donor.getGlyphSet()
    mapping, counts, uncovered = {}, dict(cjk=0, latin=0, digit=0), 0
    for cp, target_name in sorted(cmap.items()):
        category = role(cp)
        if not category:
            continue
        source_name = source.get(cp)
        if not source_name:
            uncovered += 1
            continue
        if target_name in mapping and mapping[target_name] != source_name:
            previous = mapping[target_name]
            for name in (previous, source_name):
                if name not in recordings:
                    recordings[name] = draw_record(source_glyphs, name)
            if (recordings[previous].value != recordings[source_name].value or
                    donor['hmtx'][previous] != donor['hmtx'][source_name]):
                raise ValueError(f'原厂共享字形 U+{cp:04X} 对应不同来源轮廓，不能安全覆盖')
        mapping[target_name] = source_name
        counts[category] += 1
    # A covered character can share its glyph ID with an uncovered character
    # (or a character outside these roles). Keep that whole slot stock.
    blocked = {name for table in font['cmap'].tables
               if table.isUnicode() and table.format != 14
               for cp, name in table.cmap.items() if not role(cp) or cp not in source}
    # Preserve every UVS target as well as the format-14 table bytes. A default
    # UVS entry points through the base cmap; a non-default entry names its own
    # glyph. Neither glyph may be changed behind the unchanged UVS mapping.
    base_cmap = font.getBestCmap() or {}
    for table in font['cmap'].tables:
        if table.format != 14:
            continue
        for entries in getattr(table, 'uvsDict', {}).values():
            for codepoint, glyph_name in entries:
                resolved = glyph_name or base_cmap.get(codepoint)
                if resolved:
                    blocked.add(resolved)
    retained_shared = len(blocked.intersection(mapping))
    for name in blocked:
        mapping.pop(name, None)
    counts = {category: sum(role(cp) == category and name in mapping for cp, name in cmap.items())
              for category in counts}
    if not counts['cjk']:
        return {'mode': 'retained-no-cjk-match', 'replaced': counts, 'uncovered': uncovered,
                **donor_report, 'targetStylePreserved': True}
    if '.notdef' in mapping:
        raise ValueError('原厂编码映射指向缺字槽，不能覆盖 .notdef')
    guard_retained_components(font, mapping)
    scale = font['head'].unitsPerEm / donor['head'].unitsPerEm
    frame = font['head']
    converted = {}
    for target_name, source_name in mapping.items():
        if source_name not in recordings:
            recordings[source_name] = draw_record(source_glyphs, source_name)
        recording = recordings[source_name]
        bounds = BoundsPen(None)
        recording.replay(bounds)
        # Keep the stock line frame. A donor outside it fails before publication;
        # arbitrary per-glyph shrinking would change the requested typeface.
        if bounds.bounds is not None:
            x0, y0, x1, y1 = (coordinate * scale for coordinate in bounds.bounds)
            if x0 < frame.xMin - 1 or y0 < frame.yMin - 1 or x1 > frame.xMax + 1 or y1 > frame.yMax + 1:
                raise ValueError(f'来源字形 {source_name} 超出本机原厂字体面边界')
        width, bearing = donor['hmtx'][source_name]
        width, bearing = round(width * scale), round(bearing * scale)
        if not 0 <= width <= 65535 or not -32768 <= bearing <= 32767:
            raise ValueError('来源水平度量超出 SFNT 范围')
        header = font['hhea']
        outline_width = 0 if bounds.bounds is None else (bounds.bounds[2] - bounds.bounds[0]) * scale
        if (width > header.advanceWidthMax or bearing < header.minLeftSideBearing or
                width - bearing - outline_width < header.minRightSideBearing - 1 or
                bearing + outline_width > header.xMaxExtent + 1):
            raise ValueError(f'来源字形 {source_name} 水平度量超出本机原厂字体面边界')
        if kind == 'glyf':
            key = (source_name,)
            if key not in converted:
                pen = TTGlyphPen(None)
                output = Cu2QuPen(pen, max_err=max(0.5, frame.unitsPerEm / 2000),
                                  reverse_direction='glyf' not in donor)
                recording.replay(TransformPen(output, (scale, 0, 0, scale, 0, 0)))
                converted[key] = pen.glyph()
            glyph = converted[key]
            vertical = retained_vertical_deltas(font, target_name)
            old_origin = None
            if 'vmtx' in font:
                old_advance, old_bearing = font['vmtx'][target_name]
                old_origin = getattr(font['glyf'][target_name], 'yMax', 0) + old_bearing
            font['glyf'][target_name] = glyph
            glyph.recalcBounds(font['glyf'])
            if not hasattr(glyph, 'xMin'):
                glyph.xMin = glyph.yMin = glyph.xMax = glyph.yMax = 0
            # recalcBBoxes=False keeps the stock frame but also disables maxp
            # recomputation. Retain stock interpreter limits while reserving
            # enough point/contour capacity for the newly imported outlines.
            maxp = font['maxp']
            maxp.maxPoints = max(maxp.maxPoints, len(glyph.getCoordinates(font['glyf'])[0]))
            maxp.maxContours = max(maxp.maxContours, glyph.numberOfContours)
            if 'fvar' in font and bearing != glyph.xMin:
                raise ValueError('可变 TrueType 的来源侧距必须等于轮廓 xMin')
            if old_origin is not None:
                new_bearing = old_origin - glyph.yMax
                if not -32768 <= new_bearing <= 32767:
                    raise ValueError('原厂垂直原点无法保持在 SFNT 度量范围内')
                header = font['vhea']
                height = glyph.yMax - glyph.yMin
                if (new_bearing < header.minTopSideBearing or
                        old_advance - new_bearing - height < header.minBottomSideBearing or
                        new_bearing + height > header.yMaxExtent):
                    raise ValueError('来源字形垂直度量超出本机原厂字体面边界')
                font['vmtx'][target_name] = (old_advance, new_bearing)
            if 'gvar' in font:
                points = len(glyph.getCoordinates(font['glyf'])[0])
                font['gvar'].variations[target_name] = [
                    TupleVariation(axes, [(0, 0)] * (points + 2) + [top, bottom])
                    for axes, top, bottom in vertical]
        else:
            if kind == 'CFF2' and 'vmtx' in font and 'VORG' not in font:
                raise ValueError('CFF2 集合缺少独立垂直原点，不能沿用旧轮廓的垂直侧距')
            cff = font[kind].cff
            top = cff.topDictIndex[0]
            _, selector = top.CharStrings.getItemAndSelector(target_name)
            private = top.FDArray[selector or 0].Private if hasattr(top, 'FDArray') else top.Private
            key = (source_name, selector, width)
            if key not in converted:
                encoded_width = None if kind == 'CFF2' or width == private.defaultWidthX else width - private.nominalWidthX
                pen = T2CharStringPen(encoded_width, None, CFF2=kind == 'CFF2')
                output = Qu2CuPen(pen, max_err=max(0.5, frame.unitsPerEm / 2000),
                                  all_cubic=True, reverse_direction='glyf' in donor)
                recording.replay(TransformPen(output, (scale, 0, 0, scale, 0, 0)))
                char = pen.getCharString(private=private, globalSubrs=cff.GlobalSubrs)
                if selector is not None:
                    char.fdSelectIndex = selector
                converted[key] = char
            top.CharStrings[target_name] = converted[key]
        font['hmtx'][target_name] = (width, bearing)
    freeze_horizontal_variations(font, mapping)
    for tag in ('DSIG', 'LTSH', 'hdmx', 'VDMX'):
        if tag in font:
            del font[tag]
    return {'mode': 'compiled', 'replaced': counts, 'uncovered': uncovered,
            'retainedSharedSlots': retained_shared, 'retainedUnencodedGlyphs': True,
            'outline': kind, 'retainedVariationAxes': 'fvar' in font,
            'replacementVariation': 'selected-fixed-weight',
            **donor_report, 'targetStylePreserved': True}


def inspect_donor(source):
    source = Path(source)
    face_index = _pick_face(source, 'cjk', 400, None)
    kwargs = {'fontNumber': face_index} if face_index >= 0 else {}
    with TTFont(source, lazy=True, recalcTimestamp=False, **kwargs) as donor:
        cmap = donor.getBestCmap() or {}
        if any(cp not in cmap for cp in map(ord, '中ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')):
            raise ValueError('组合来源缺少必需的中文、英文字母或数字')
        tables = font_source_profile._table_contract(donor)
        axes = font_source_profile._axes(donor)
        coverage = font_source_profile._coverage(donor)
        capabilities = font_source_profile._capabilities(
            coverage, tables, axes, font_source_profile._fixed_pitch(donor))
        if not capabilities.get('globalUiCandidate'):
            raise ValueError('组合来源能力不足以覆盖通用系统文字槽')
        return {'face': face_index, 'weight': target_weight(donor), 'axes': axes,
                'tables': tables, 'capabilities': capabilities}


def build(source, stock, output, workspace, request, target, progress=None,
          source_identity=None, source_sha256=None, stock_sha256=None,
          verify_source_hash=True, donor_facts=None):
    source, stock, output = map(Path, (source, stock, output))
    if source.resolve() == output.resolve() or stock.resolve() == output.resolve():
        raise ValueError('集合输出不能覆盖来源或原厂文件')
    if source.stat().st_size <= 0 or source.stat().st_size > MAX_MIX_SOURCE_BYTES:
        raise ValueError('组合字体大小超出集合生成限制')
    if stock.stat().st_size <= 0 or stock.stat().st_size > MAX_STOCK_FILE_BYTES:
        raise ValueError('原厂集合大小超出安全限制')
    source_stat = identity(source)
    if source_identity is not None and source_stat != source_identity:
        raise ValueError('组合来源在集合生成前已变化')
    before = (source_stat, identity(stock))
    source_hash = source_sha256 or sha(source)
    stock_hash = stock_sha256 or sha(stock)
    count = collection_faces(stock)
    donor_facts = donor_facts or inspect_donor(source)
    face_index = donor_facts['face']
    kwargs = {'fontNumber': face_index} if face_index >= 0 else {}
    report = {'schema': SCHEMA, 'requestId': request, 'target': target,
              'sourceSha256': source_hash, 'stockSha256': stock_hash,
              'sourceFace': face_index, 'stockFaces': count, 'faces': [],
              'selectionModel': 'selected-fixed-weight',
              'targetStylePolicy': 'preserve-stock-style-and-weight-metadata',
              'selectedAxesTraceable': False,
              'selectedAxesNote': '静态组合产物哈希绑定实际输出；组合库未保存源选轴数值'}
    with tempfile.TemporaryDirectory(prefix='collection-', dir=workspace) as temporary:
        temporary = Path(temporary)
        face_paths = []
        with TTFont(source, lazy=True, recalcTimestamp=False, **kwargs) as donor:
            cmap = donor.getBestCmap() or {}
            if any(cp not in cmap for cp in map(ord, '中ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')):
                raise ValueError('组合来源缺少必需的中文、英文字母或数字')
            if not any(tag in donor for tag in ('glyf', 'CFF ', 'CFF2')):
                raise ValueError('组合来源不包含可用轮廓')
            donor_tables = donor_facts['tables']
            donor_axes = donor_facts['axes']
            donor_capabilities = donor_facts['capabilities']
            report['donor'] = {
                'weight': donor_facts['weight'], 'axes': donor_axes,
                'outline': donor_tables['outline'],
                'capabilities': donor_capabilities,
            }
            recordings = {}
            for index in range(count):
                _progress(progress, 'collection', f'正在编译本机 CJK 集合面 {index + 1}/{count}', 95)
                face_path = temporary / f'face-{index}.font'
                with TTFont(stock, fontNumber=index, lazy=True, recalcBBoxes=False,
                            recalcTimestamp=False) as font:
                    original = protected(font)
                    details = replace_face(font, donor, recordings)
                    if protected(font) != original:
                        raise ValueError(f'集合面 {index} 的原厂布局契约已变化')
                    if details['mode'] == 'compiled':
                        font.save(face_path, reorderTables=False)
                    else:
                        # Retained faces need no expensive outline round trip.
                        with TTFont(stock, fontNumber=index, lazy=True, recalcBBoxes=False,
                                    recalcTimestamp=False) as untouched:
                            untouched.save(face_path, reorderTables=False)
                with TTFont(face_path, lazy=True, recalcTimestamp=False) as check:
                    if protected(check) != original:
                        raise ValueError(f'集合面 {index} 序列化后布局契约已变化')
                report['faces'].append(dict(index=index, contract=original, **details))
                face_paths.append(face_path)
                del font, check
                gc.collect()
        if not any(face['mode'] == 'compiled' for face in report['faces']):
            # The requested alias may already contain a generated single-face
            # font from the ROM mapper. Preserve the real OEM collection there
            # even when every OEM face is specialized or has no safe CJK slot.
            report['result'] = 'PASS'
            report['mode'] = 'retained-original-collection'
            report['outputSha256'] = stock_hash
            _check_sources(source, stock, before, source_hash, stock_hash,
                           verify_source_hash=verify_source_hash)
            _atomic_copy(stock, output, expected_hash=stock_hash,
                         precommit=lambda: _check_sources(source, stock, before,
                                                          source_hash, stock_hash,
                                                          verify_source_hash=verify_source_hash))
            return report
        collection = TTCollection()
        collection.fonts = [TTFont(path, lazy=True, recalcBBoxes=False, recalcTimestamp=False)
                            for path in face_paths]
        staged = temporary / 'compiled.ttc'
        try:
            collection.save(staged, shareTables=True)
        finally:
            collection.close()
        if collection_faces(staged) != count:
            raise ValueError('生成后的集合面数量变化')
        for index, face in enumerate(report['faces']):
            with TTFont(staged, fontNumber=index, lazy=True, recalcTimestamp=False) as check:
                if protected(check) != face['contract']:
                    raise ValueError(f'集合面 {index} 合集后布局契约已变化')
        if staged.stat().st_size > MAX_STOCK_FILE_BYTES:
            raise ValueError('生成后的字体集合超出单文件大小限制')
        _check_sources(source, stock, before, source_hash, stock_hash,
                       verify_source_hash=verify_source_hash)
        report['outputSha256'] = sha(staged)
        report['result'] = 'PASS'
        output.parent.mkdir(parents=True, exist_ok=True)
        # Rename on the output filesystem; keep the old alias until all checks pass.
        _atomic_copy(staged, output, expected_hash=report['outputSha256'],
                     precommit=lambda: _check_sources(source, stock, before,
                                                      source_hash, stock_hash,
                                                      verify_source_hash=verify_source_hash))
    return report


def _check_sources(source, stock, before, source_hash, stock_hash,
                   verify_source_hash=True):
    if (before != (identity(source), identity(stock))
            or (verify_source_hash and sha(source) != source_hash)
            or sha(stock) != stock_hash):
        raise ValueError('原厂集合或组合来源在编译期间发生变化')


def _atomic_copy(source, output, expected_hash=None, precommit=None):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.collection-', dir=output.parent)
    try:
        with os.fdopen(fd, 'wb') as stream, Path(source).open('rb') as data:
            shutil.copyfileobj(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o644)
        if expected_hash is not None and sha(name) != expected_hash:
            raise ValueError('集合暂存字节与验证后的输出哈希不符')
        if precommit is not None:
            precommit()
        os.replace(name, output)
    finally:
        Path(name).unlink(missing_ok=True)


def stock_path(module, target):
    logical = str(target)
    path = PurePosixPath(logical)
    if (not path.is_absolute() or len(path.parts) != 4 or path.parts[0] != '/'
            or path.parts[2] != 'fonts' or path.suffix.lower() not in ('.ttc', '.otc')):
        raise ValueError('集合目标必须是准确的系统字体路径')
    allowed = dict(stock_inventory.LOGICAL_FONT_ROOTS)
    if path.parts[1] not in allowed:
        raise ValueError('集合目标分区不受支持')
    stock = stock_font_snapshot.resolve(logical, Path(module))
    if stock is None:
        raise ValueError(f'缺少可验证的本机原厂字体快照：{logical}')
    return stock


def _snapshot_digest(module, logical, stock):
    entry = stock_font_snapshot.load(Path(module)).get('files', {}).get(logical)
    digest = entry.get('sha256', '') if isinstance(entry, dict) else ''
    if (isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest)
            and entry.get('size') == Path(stock).stat().st_size):
        return digest
    return sha(stock)


def owned_workspace():
    """Scratch space inside the finite supervisor's own task directory.

    The supervisor removes LUOSHU_TASK_SCOPE_TMPDIR when the task ends, so a
    killed build cannot leave a resident or orphaned workspace behind.
    """
    raw = os.environ.get('LUOSHU_TASK_SCOPE_TMPDIR', '')
    scope = Path(raw)
    if not raw or not scope.is_absolute() or scope.is_symlink() or not scope.is_dir():
        raise ValueError('缺少任务专属字体工作区')
    scope = scope.resolve()
    return Path(tempfile.mkdtemp(prefix='collection-build.', dir=scope)), scope


def _valid_request(value):
    return bool(value and len(value) <= 160 and re.fullmatch(r'[A-Za-z0-9_.:-]+', value))


def _inventory_targets(module):
    path = Path(module) / 'config/device_font_inventory.json'
    data = stock_inventory.load_inventory(path)
    candidates = []
    for logical, entry in data['slots'].items():
        logical_path = PurePosixPath(logical)
        if logical_path.suffix.lower() not in ('.ttc', '.otc'):
            continue
        if not (entry.get('uiEligible') is True or entry.get('source') == 'verified-scan'):
            continue
        candidates.append(logical)
    candidates = sorted(set(candidates))
    if len(candidates) > MAX_COLLECTION_TARGETS:
        raise ValueError(f'本机 UI 字体集合目标过多：{len(candidates)}')
    return candidates


def _payload_output(payload, logical):
    relative = Path(logical.lstrip('/'))
    if relative.is_absolute() or '..' in relative.parts or len(relative.parts) != 3:
        raise ValueError(f'字体集合暂存路径无效：{logical}')
    if relative.parts[1] != 'fonts' or relative.suffix.lower() not in ('.ttc', '.otc'):
        raise ValueError(f'字体集合不在受支持的分区 fonts 目录：{logical}')
    output = Path(payload) / relative
    root = Path(payload).resolve()
    parent = output.parent.resolve()
    if not parent.is_relative_to(root) or output.is_symlink() or output.is_dir():
        raise ValueError(f'字体集合输出路径越界或包含链接：{logical}')
    return output


def _write_proof(payload, relative, report):
    root = Path(payload) / PROOF_DIRECTORY
    if root.is_symlink():
        raise ValueError('字体集合证明目录不能是符号链接')
    root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(relative.encode('utf-8')).hexdigest() + '.json'
    target = root / key
    fd, temporary = tempfile.mkstemp(prefix='.proof-', dir=root)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=True, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _read_mix_manifest(path, source):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024:
        raise ValueError('组合字体清单不存在或无效')
    fields = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        if key in fields:
            raise ValueError('组合字体清单包含重复字段')
        fields[key] = value
    if fields.get('combination') != 'true':
        raise ValueError('所选字体不是已保存的组合字体')
    try:
        files = json.loads(fields.get('files', '[]'))
    except json.JSONDecodeError as error:
        raise ValueError('组合字体文件清单无效') from error
    if (not isinstance(files, list) or not files or len(files) > 64
            or any(not isinstance(name, str) or Path(name).name != name for name in files)
            or source.name not in files):
        raise ValueError('组合字体来源与已保存清单不符')
    return {'mixRequestId': fields.get('request', ''),
            'sourceIds': {role: fields.get(role + '_source_id', '')
                          for role in ('cjk', 'latin', 'digit')}}


def build_payload(module, payload, source, request, task_workspace, mix_config):
    module, payload, source = map(Path, (module, payload, source))
    if not _valid_request(request):
        raise ValueError('字体集合请求标识无效')
    if not payload.is_dir() or payload.is_symlink():
        raise ValueError('字体切换暂存负载不存在或包含链接')
    if not source.is_file() or source.is_symlink() or source.stat().st_size <= 0:
        raise ValueError('已保存组合字体不存在或无效')
    mix = _read_mix_manifest(mix_config, source)
    workspace = Path(task_workspace)
    if not workspace.is_absolute() or workspace.is_symlink() or not workspace.is_dir():
        raise ValueError('缺少任务专属字体工作区')
    workspace = workspace.resolve()
    payload_root = payload.resolve()
    if not payload_root.is_relative_to(module.resolve()):
        raise ValueError('字体切换暂存负载不属于当前模块')
    proof_root = payload / PROOF_DIRECTORY
    if proof_root.is_symlink():
        raise ValueError('字体集合证明目录不能是符号链接')
    if proof_root.exists():
        shutil.rmtree(proof_root)

    targets = _inventory_targets(module)
    total_stock = 0
    report = {'schema': 'composite-collection-payload-v1', 'requestId': request,
              'mixRequestId': mix['mixRequestId'], 'result': 'PASS',
              'built': [], 'skipped': []}
    source_before = identity(source)
    source_hash = sha(source)
    donor_facts = inspect_donor(source)
    total_faces = 0
    total_output = 0
    for logical in targets:
        stock = stock_path(module, logical)
        size = stock.stat().st_size
        if size <= 0 or size > MAX_STOCK_FILE_BYTES:
            raise ValueError(f'原厂集合大小超出安全限制：{logical}')
        total_stock += size
        if total_stock > MAX_COLLECTION_BYTES:
            raise ValueError('原厂字体集合总大小超出安全限制')
        faces = collection_faces(stock)
        total_faces += faces
        if total_faces > MAX_COLLECTION_FACE_TOTAL:
            raise ValueError('本次字体集合总字体面数量超出安全限制')
        output = _payload_output(payload, logical)
        relative = output.relative_to(payload).as_posix()
        result = build(source, stock, output, workspace, request, logical,
                       str(module / 'config/composite_progress.json'),
                       source_identity=source_before, source_sha256=source_hash,
                       stock_sha256=_snapshot_digest(module, logical, stock),
                       verify_source_hash=False, donor_facts=donor_facts)
        _write_proof(payload, relative, result)
        total_output += output.stat().st_size
        if total_output > MAX_COLLECTION_BYTES:
            raise ValueError('本次生成的字体集合总大小超出安全限制')
        report['built'].append({'path': relative, 'faces': result['stockFaces'],
                                'outputSha256': result['outputSha256'],
                                'mode': result.get('mode', 'compiled-or-retained'),
                                'donor': result.get('donor', {})})
    if identity(source) != source_before or sha(source) != source_hash:
        raise ValueError('组合字体在集合生成期间发生变化')
    return report


def _parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    build_parser = sub.add_parser('build')
    build_parser.add_argument('--module', type=Path, required=True)
    build_parser.add_argument('--payload', type=Path, required=True)
    build_parser.add_argument('--source', type=Path, required=True)
    build_parser.add_argument('--mix-config', type=Path, required=True)
    build_parser.add_argument('--request', required=True)
    validate_parser = sub.add_parser('validate')
    validate_parser.add_argument('--module', type=Path, required=True)
    validate_parser.add_argument('--payload', type=Path, required=True)
    validate_parser.add_argument('--request', required=True)
    validate_parser.add_argument('--require-proof', action='store_true')
    validate_parser.add_argument('--cleanup-proofs', action='store_true')
    return parser


def main():
    args = _parser().parse_args()
    workspace = None
    try:
        if args.command == 'build':
            workspace, _scope = owned_workspace()
            result = build_payload(args.module, args.payload, args.source,
                                   args.request, workspace, args.mix_config)
        else:
            contract = composite_collection_contract.validate(
                args.payload, args.request, args.module,
                require_proof=args.require_proof)
            if contract['result'] != 'PASS':
                raise ValueError('字体集合输出契约校验失败')
            result = contract
            if args.cleanup_proofs:
                proof_root = args.payload / PROOF_DIRECTORY
                if proof_root.exists() and not proof_root.is_symlink():
                    shutil.rmtree(proof_root)
        print(json.dumps({'status': 'ok', 'data': result}, ensure_ascii=False,
                         separators=(',', ':')))
        return 0
    except (OSError, ValueError, RuntimeError, TTLibError,
            stock_inventory.InventoryError) as error:
        print('[MIX] CJK 集合生成失败：' + str(error), flush=True)
        return 1
    finally:
        if workspace is not None:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == '__main__':
    raise SystemExit(main())
