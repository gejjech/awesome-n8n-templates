#!/usr/bin/env python3
"""
Export an index of all n8n workflow templates in this repository.

Outputs CSV and/or JSON inventories with metadata:
- absolute_path, relative_path, title, category, nodes_count,
  file_size_bytes, modified_iso

Usage examples:
  python tools/export_index.py --csv /workspace/all_templates.csv
  python tools/export_index.py --json /workspace/all_templates.json
  python tools/export_index.py --csv /workspace/all_templates.csv --json /workspace/all_templates.json
"""

import argparse
import csv
import fnmatch
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def iter_json_files(root_dir: str) -> Iterable[str]:
    for current_dir, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if fnmatch.fnmatch(filename, '*.json'):
                yield os.path.join(current_dir, filename)


def try_parse_json(path: str) -> Optional[dict]:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return json.load(f)
    except Exception:
        return None


def extract_title_and_nodes_count(path: str, data: Optional[dict]) -> Tuple[str, Optional[int]]:
    title = os.path.splitext(os.path.basename(path))[0]
    nodes_count: Optional[int] = None
    if isinstance(data, dict):
        name = data.get('name')
        if isinstance(name, str) and name.strip():
            title = name.strip()
        nodes = data.get('nodes')
        if isinstance(nodes, list):
            nodes_count = len(nodes)
    return title, nodes_count


@dataclass
class TemplateRecord:
    absolute_path: str
    relative_path: str
    title: str
    category: str
    nodes_count: Optional[int]
    file_size_bytes: int
    modified_iso: str


def build_record(path: str) -> TemplateRecord:
    rel = os.path.relpath(path, REPO_ROOT)
    category = rel.split(os.sep)[0] if os.sep in rel else ''

    data = try_parse_json(path)
    title, nodes_count = extract_title_and_nodes_count(path, data)

    stat = os.stat(path)
    return TemplateRecord(
        absolute_path=os.path.abspath(path),
        relative_path=rel,
        title=title,
        category=category,
        nodes_count=nodes_count,
        file_size_bytes=stat.st_size,
        modified_iso=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds'),
    )


def write_csv(records: List[TemplateRecord], csv_path: str) -> None:
    fieldnames = [
        'absolute_path',
        'relative_path',
        'title',
        'category',
        'nodes_count',
        'file_size_bytes',
        'modified_iso',
    ]
    csv_dir = os.path.dirname(csv_path)
    if csv_dir:
        os.makedirs(csv_dir, exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(asdict(r))


def write_json(records: List[TemplateRecord], json_path: str) -> None:
    json_dir = os.path.dirname(json_path)
    if json_dir:
        os.makedirs(json_dir, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Export an index of n8n workflow templates.')
    parser.add_argument('--csv', dest='csv_path', type=str, default='', help='Path to write CSV output.')
    parser.add_argument('--json', dest='json_path', type=str, default='', help='Path to write JSON output.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.csv_path and not args.json_path:
        print('Please provide at least one of --csv or --json output paths.')
        return 2

    records: List[TemplateRecord] = []
    for path in iter_json_files(REPO_ROOT):
        records.append(build_record(path))

    if args.csv_path:
        write_csv(records, args.csv_path)
        print(f"Wrote CSV: {args.csv_path} ({len(records)} records)")

    if args.json_path:
        write_json(records, args.json_path)
        print(f"Wrote JSON: {args.json_path} ({len(records)} records)")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

