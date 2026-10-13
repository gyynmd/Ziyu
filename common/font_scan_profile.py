#!/usr/bin/env python3
"""Shared OEM classification and bounded, read-only XML discovery."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

REVISION = 1


def getprop(name: str) -> str:
    try:
        return subprocess.run(['getprop', name], capture_output=True, text=True,
                              timeout=2, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def detect(get_property=getprop) -> str:
    # ROM properties win over hardware branding (custom ROMs may retain it).
    if get_property('ro.build.version.oplusrom') or get_property('ro.build.version.opporom'):
        return 'coloros'
    if any(get_property(p) for p in ('ro.vivo.os.name', 'ro.vivo.os.version', 'ro.vivo.rom.version')):
        return 'originos'
    if get_property('ro.mi.os.version.name') or get_property('ro.miui.ui.version.name'):
        return 'hyperos'
    brands = {get_property(p).strip().lower() for p in
              ('ro.product.brand', 'ro.product.manufacturer', 'ro.product.vendor.brand')}
    if brands.intersection({'vivo', 'iqoo'}):
        return 'originos'
    if brands.intersection({'oppo', 'oplus', 'oneplus', 'realme'}):
        return 'coloros'
    return 'generic'


def walk(root: Path, depth: int = 4, limit: int = 8192):
    """Never descend through directory symlinks; bound entries and depth."""
    if not root.is_dir():
        return
    seen = 0
    for directory, directories, files in os.walk(root, followlinks=False):
        distance = len(Path(directory).relative_to(root).parts)
        directories[:] = sorted(d for d in directories
                                if distance < depth and not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            seen += 1
            if seen > limit:
                raise ValueError(f'目录扫描达到 {limit} 项上限：{root}')
            yield Path(directory) / name


def xml_files(root: Path):
    for path in walk(root):
        name = path.name.lower()
        relative = path.relative_to(root)
        if (path.suffix.lower() == '.xml'
                and ('font' in name or any('font' in p.lower() for p in relative.parts[:-1]))):
            yield path


def extra_roots(profile: str, partitions):
    names = ('vivo', 'originos', 'iqoo') if profile == 'originos' else (
        ('oplus', 'oppo', 'coloros', 'oneplus', 'realme') if profile == 'coloros' else ())
    for partition in partitions:
        yield partition, Path('/') / partition / 'etc/fonts'
        for name in names:
            yield partition, Path('/') / partition / name / 'fonts'
            yield partition, Path('/') / partition / name / 'etc'


def rows(path: Path):
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('字体 XML 超过读取上限')
    tree = ET.parse(path)
    local = lambda tag: tag.rsplit('}', 1)[-1].lower()
    for family in tree.getroot().iter():
        if local(family.tag) not in {'family', 'familyset'}:
            continue
        for element in family:
            if local(element.tag) == 'fileset':
                elements = list(element)
            else:
                elements = [element]
            for font in elements:
                if local(font.tag) not in {'font', 'file'}:
                    continue
                reference = (font.text or '').strip()
                if Path(reference).suffix.lower() not in {'.ttf', '.otf', '.ttc', '.otc'}:
                    continue
                axes = ','.join(f"{a.get('tag', '')}={a.get('stylevalue', a.get('value', ''))}"
                                for a in font if local(a.tag) == 'axis')
                fields = (reference, font.get('weight', ''), font.get('style', ''), '0',
                          font.get('index', '0'), axes, family.get('name', ''))
                yield '|'.join(value.replace('|', '?').replace('\n', ' ').replace('\r', ' ')
                               for value in fields)


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'profile':
        print(detect())
    elif len(sys.argv) == 3 and sys.argv[1] == 'xml':
        print('\n'.join(rows(Path(sys.argv[2]))))
    else:
        raise SystemExit('usage: font_scan_profile.py profile | xml <path>')
