#!/usr/bin/env python3
"""
Search n8n workflow templates in this repository by keyword and category.

Examples:
  - Search everywhere for "telegram":
      python tools/search_templates.py -q telegram

  - Search only in the Telegram category and show 5 results:
      python tools/search_templates.py -c Telegram -q bot -n 5

  - Print only matching file paths (absolute):
      python tools/search_templates.py -q gmail --paths-only
"""

import argparse
import fnmatch
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


@dataclass
class TemplateHit:
    absolute_path: str
    relative_path: str
    title: str
    category: str
    matched: List[str]
    nodes_count: Optional[int]
    file_size_bytes: int
    modified_iso: str


def iter_json_files(root_dir: str) -> Iterable[str]:
    for current_dir, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if fnmatch.fnmatch(filename, '*.json'):
                yield os.path.join(current_dir, filename)


def safe_read_text(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ''


def try_parse_json(path: str) -> Optional[dict]:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def extract_title_and_nodes_count(path: str, data: Optional[dict]) -> Tuple[str, Optional[int]]:
    title = os.path.splitext(os.path.basename(path))[0]
    nodes_count: Optional[int] = None
    if isinstance(data, dict):
        # Common n8n workflow structure: { name: str, nodes: [...] }
        name = data.get('name')
        if isinstance(name, str) and name.strip():
            title = name.strip()
        nodes = data.get('nodes')
        if isinstance(nodes, list):
            nodes_count = len(nodes)
    return title, nodes_count


def matches_query(text: str, keywords: List[str]) -> List[str]:
    lowered = text.lower()
    matched: List[str] = []
    for kw in keywords:
        if kw in lowered:
            matched.append(kw)
    # Require all keywords to be present
    return matched if len(matched) == len(keywords) else []


def build_hit(path: str, keywords: List[str], search_content: bool) -> Optional[TemplateHit]:
    rel = os.path.relpath(path, REPO_ROOT)
    category = rel.split(os.sep)[0] if os.sep in rel else ''

    # Aggregate searchable text: filename, relpath, JSON-derived title, and optionally content
    data = try_parse_json(path)
    title, nodes_count = extract_title_and_nodes_count(path, data)

    parts = [
        os.path.basename(path),
        rel,
        title,
    ]

    if search_content:
        parts.append(safe_read_text(path))

    aggregate_text = '\n'.join(parts)
    matched = matches_query(aggregate_text, keywords)
    if not matched:
        return None

    stat = os.stat(path)
    return TemplateHit(
        absolute_path=os.path.abspath(path),
        relative_path=rel,
        title=title,
        category=category,
        matched=matched,
        nodes_count=nodes_count,
        file_size_bytes=stat.st_size,
        modified_iso=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec='seconds'),
    )


def search_templates(
    categories: List[str],
    keywords: List[str],
    limit: int,
    search_content: bool,
) -> List[TemplateHit]:
    hits: List[TemplateHit] = []
    for path in iter_json_files(REPO_ROOT):
        rel = os.path.relpath(path, REPO_ROOT)
        category = rel.split(os.sep)[0] if os.sep in rel else ''
        if categories and category not in categories:
            continue
        hit = build_hit(path, keywords, search_content)
        if hit is not None:
            hits.append(hit)
            if 0 < limit <= len(hits):
                break
    return hits


def print_hits(hits: List[TemplateHit], paths_only: bool) -> None:
    if paths_only:
        for h in hits:
            print(h.absolute_path)
        return

    for h in hits:
        nodes_info = f" | nodes={h.nodes_count}" if h.nodes_count is not None else ""
        print(f"{h.relative_path} | {h.title} | category={h.category}{nodes_info} | matched={','.join(h.matched)} | mtime={h.modified_iso}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Search n8n workflow templates in this repo.')
    parser.add_argument('-q', '--query', type=str, default='', help='Space-separated keywords (case-insensitive).')
    parser.add_argument('-c', '--category', action='append', default=[], help='Restrict search to a category directory (can be used multiple times).')
    parser.add_argument('-n', '--limit', type=int, default=25, help='Maximum number of results to print (default: 25).')
    parser.add_argument('--paths-only', action='store_true', help='Print only absolute file paths.')
    parser.add_argument('--filenames', action='store_true', help='Search only filenames/title (skip file content).')
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    keywords = [kw.strip().lower() for kw in args.query.split() if kw.strip()]
    if not keywords:
        print('Please provide at least one keyword with -q/--query.', file=sys.stderr)
        return 2

    categories = args.category or []
    hits = search_templates(categories=categories, keywords=keywords, limit=args.limit, search_content=not args.filenames)
    if not hits:
        print('No results found.', file=sys.stderr)
        return 1
    print_hits(hits, paths_only=args.paths_only)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

