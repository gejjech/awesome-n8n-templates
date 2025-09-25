#!/usr/bin/env python3
"""
Validate all template JSON files in the repository.

Checks:
- Valid JSON parse
- Optional n8n structure checks: `nodes` is a list if present, `name` is a non-empty string if present
- For each node (if present): `name` (str), `type` (str) are recommended

Exit codes:
- 0: all good
- 1: validation errors found

Usage:
  python tools/validate_templates.py
  python tools/validate_templates.py --strict  # enforce recommended fields
"""

import argparse
import fnmatch
import json
import os
from dataclasses import dataclass
from typing import List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


EXCLUDE_DIRS = {
    '.git', '.github', 'tools', 'dist', 'preview', '__pycache__', '.venv', 'node_modules'
}


@dataclass
class Issue:
    path: str
    message: str


def iter_json_files() -> List[str]:
    results: List[str] = []
    for current_dir, dirnames, filenames in os.walk(REPO_ROOT):
        # mutate dirnames in-place to prune traversal
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if fnmatch.fnmatch(filename, '*.json'):
                results.append(os.path.join(current_dir, filename))
    return results


def safe_load(path: str) -> Optional[dict]:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return json.load(f)
    except Exception:
        return None


def validate(path: str, strict: bool) -> List[Issue]:
    issues: List[Issue] = []
    data = safe_load(path)
    if data is None:
        issues.append(Issue(path, 'Invalid JSON (failed to parse).'))
        return issues

    # Optional structure checks for common n8n workflow format
    if 'nodes' in data and not isinstance(data['nodes'], list):
        issues.append(Issue(path, '`nodes` must be a list when present.'))

    if 'name' in data:
        name = data.get('name')
        if not (isinstance(name, str) and name.strip()):
            issues.append(Issue(path, '`name` present but empty or not a string.'))

    if strict and isinstance(data.get('nodes'), list):
        for idx, node in enumerate(data['nodes']):
            if not isinstance(node, dict):
                issues.append(Issue(path, f'nodes[{idx}] is not an object.'))
                continue
            n_name = node.get('name')
            n_type = node.get('type')
            if not (isinstance(n_name, str) and n_name.strip()):
                issues.append(Issue(path, f'nodes[{idx}].name missing or empty.'))
            if not (isinstance(n_type, str) and n_type.strip()):
                issues.append(Issue(path, f'nodes[{idx}].type missing or empty.'))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate template JSON files.')
    parser.add_argument('--strict', action='store_true', help='Enable stricter checks for node fields.')
    args = parser.parse_args()

    paths = iter_json_files()
    all_issues: List[Issue] = []
    for p in sorted(paths):
        all_issues.extend(validate(p, strict=args.strict))

    if all_issues:
        for issue in all_issues:
            print(f"ERROR: {os.path.relpath(issue.path, REPO_ROOT)} -> {issue.message}")
        print(f"\nFound {len(all_issues)} validation error(s) across {len(paths)} files.")
        return 1

    print(f"All {len(paths)} JSON files are valid.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

