"""Validate SFNT tables and mapped outline glyphs without a font size heuristic."""
from pathlib import Path
import argparse
import os
import struct


def table_directory_tags(path):
    """Read SFNT records rather than searching binary strings or decoding glyphs."""
    path = Path(path)
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        file_size = before.st_size

        def read_at(offset, count):
            if offset < 0 or count < 0 or offset + count > file_size:
                raise ValueError("字体表目录越过文件边界")
            stream.seek(offset)
            data = stream.read(count)
            if len(data) != count:
                raise ValueError("字体表目录读取不完整")
            return data

        magic = read_at(0, 4)
        if magic == b"ttcf":
            version, face_count = struct.unpack(">II", read_at(4, 8))
            if version not in (0x00010000, 0x00020000) or not 1 <= face_count <= 128:
                raise ValueError("字体集合头无效")
            offsets = struct.unpack(f">{face_count}I", read_at(12, face_count * 4))
            if version == 0x00020000:
                dsig_tag, dsig_size, dsig_offset = struct.unpack(">III", read_at(12 + face_count * 4, 12))
                if dsig_size and (dsig_tag != 0x44534947 or dsig_offset + dsig_size > file_size):
                    raise ValueError("字体集合签名表越过文件边界")
        else:
            offsets = (0,)

        tags = set()
        for face_index, offset in enumerate(offsets):
            header = read_at(offset, 12)
            if header[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO", b"\x00\x02\x00\x00"):
                raise ValueError(f"第 {face_index + 1} 个字体面格式无效")
            count = struct.unpack(">H", header[4:6])[0]
            if not 1 <= count <= 4096:
                raise ValueError("字体表数量无效")
            records = read_at(offset + 12, count * 16)
            face_tags = set()
            for tag, _checksum, table_offset, length in struct.iter_unpack(">4sIII", records):
                if tag in face_tags:
                    raise ValueError("字体表目录包含重复标签")
                if table_offset + length > file_size:
                    raise ValueError("字体表目录越过文件边界")
                face_tags.add(tag)
            if magic == b"ttcf" and not {b"head", b"cmap", b"maxp"}.issubset(face_tags):
                raise ValueError(f"第 {face_index + 1} 个字体面缺少 head/cmap/maxp 表")
            tags.update(face_tags)
        after = os.fstat(stream.fileno())
        current = path.stat()
        identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        if identity(before) != identity(after) or identity(after) != identity(current):
            raise ValueError("字体文件在表目录检查期间发生变化")
    known = {b"cmap": "cmap", b"head": "head", b"maxp": "maxp", b"fvar": "fvar",
             b"COLR": "COLR", b"CBDT": "CBDT", b"sbix": "sbix", b"SVG ": "SVG_"}
    return sorted(known[tag] for tag in tags if tag in known)


def validate_font(font, file_size=None, *, decode_all=True):
    from fontTools.pens.recordingPen import RecordingPen
    required = {"head", "maxp", "cmap", "hhea", "hmtx"}
    if not required.issubset(font.keys()):
        raise ValueError("字体缺少必要的 SFNT 表")
    if file_size is not None:
        for entry in font.reader.tables.values():
            if entry.offset < 0 or entry.length < 0 or entry.offset + entry.length > file_size:
                raise ValueError("字体表目录越过文件边界")
    # Force decoding, including loca/glyf, to reject valid-looking directory text
    # containing truncated or malformed table data.
    if decode_all:
        font.ensureDecompiled()
    order = font.getGlyphOrder()
    if font["maxp"].numGlyphs != len(order) or not order:
        raise ValueError("字体字形数量无效")
    cmap = font.getBestCmap() or {}
    if not cmap:
        raise ValueError("字体没有 Unicode 字符映射")
    glyphs = font.getGlyphSet()
    for name in set(cmap.values()):
        if name == ".notdef" or name not in glyphs:
            raise ValueError("字符映射指向缺失字形")
        if decode_all:
            glyphs[name].draw(RecordingPen())
    return cmap


def validate(path):
    from fontTools.ttLib import TTFont, TTCollection
    path = Path(path)
    with path.open("rb") as stream:
        collection = stream.read(4) == b"ttcf"
    owner = TTCollection(path, lazy=False) if collection else TTFont(path, lazy=False)
    try:
        if collection and not 1 <= len(owner.fonts) <= 128:
            raise ValueError("字体集合的字体面数量无效")
        for font in owner.fonts if collection else [owner]:
            validate_font(font, path.stat().st_size)
    finally:
        owner.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("font")
    parser.add_argument("--tables", action="store_true", help="Read bounded SFNT/TTC table directories only")
    args = parser.parse_args()
    try:
        if args.tables:
            print("|".join(table_directory_tags(args.font)) + "|")
        else:
            validate(args.font)
    except Exception as error:
        print(str(error) or error.__class__.__name__)
        raise SystemExit(1)
