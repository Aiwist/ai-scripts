#!/usr/bin/env python3
"""Собрать общий индекс ReaPack для репозитория Aiwist/ai-scripts.

Источник — готовые index.xml отдельных проектов (их создаёт сборка проекта,
например `python tools/reapack.py prepare` в Ai Transcriber).
Скрипт переносит блоки <category> в один индекс и следит за конфликтами имён.

Использование:
    python tools/build_index.py "../Ai Transcriber/index.xml" [ещё index.xml ...]
    python tools/build_index.py --check-only "../Ai Transcriber/index.xml"
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'index.xml'
INDEX_NAME = 'Aiwist'  # имя индекса задаёт папку Scripts/Aiwist в REAPER: не менять без причины


def load(path):
    root = ET.parse(path).getroot()
    if root.tag != 'index':
        raise ValueError(f'{path}: это не индекс ReaPack')
    categories = root.findall('category')
    if not categories:
        raise ValueError(f'{path}: нет ни одной категории')
    return categories


def build(sources):
    root = ET.Element('index', {'version': '1', 'name': INDEX_NAME})
    seen = {}
    for path, categories in sources:
        for category in categories:
            name = category.get('name')
            if name in seen:
                raise ValueError(
                    f'категория «{name}» уже взята из {seen[name]}, повтор в {path}')
            seen[name] = path
            root.append(category)
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def report(data):
    root = ET.fromstring(data)
    packages = root.findall('.//reapack')
    print(f'пакетов: {len(packages)}')
    total = 0
    for package in packages:
        versions = package.findall('version')
        files = sum(len(v.findall('source')) for v in versions)
        total += files
        names = ', '.join(v.get('name') for v in versions)
        print(f'  {package.get("name")}: версии {names}, файлов {files}')
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', nargs='+', type=Path)
    parser.add_argument('--check-only', action='store_true',
                        help='только проверить сборку, файл не записывать')
    args = parser.parse_args()
    data = build([(path, load(path)) for path in args.sources])
    report(data)
    if args.check_only:
        return 0
    TARGET.write_bytes(data)
    print(f'записан {TARGET}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, ET.ParseError) as error:
        sys.exit(f'Ошибка: {error}')
