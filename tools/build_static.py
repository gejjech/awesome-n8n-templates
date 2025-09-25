#!/usr/bin/env python3
"""
Build a static site into dist/ for preview and deployment.

Produces structure:
  dist/
    all_templates.json
    all_templates.csv
    preview/index.html
    <category dirs with .json files...>

Usage:
  python tools/build_static.py --out /workspace/dist
"""

import argparse
import os
import shutil
from pathlib import Path

# Reuse exporter implementation
from export_index import REPO_ROOT, iter_json_files, build_record, write_csv, write_json  # type: ignore


def copy_json_tree(dest_root: Path) -> None:
    """Copy all top-level category directories that contain .json files.

    Excludes the output directory itself and non-category folders like tools, .github, img, preview.
    """
    src_root = Path(REPO_ROOT)
    exclude_names = {
        dest_root.name,
        'tools',
        '.github',
        'img',
        'preview',
        '.git',
        '.venv',
        '__pycache__',
    }

    # Collect top-level directories that contain JSON files, excluding dest_root and excluded dirs
    top_level_dirs = set()
    for abs_path in iter_json_files(REPO_ROOT):
        # Skip any files under the destination directory
        try:
            if Path(abs_path).resolve().is_relative_to(dest_root.resolve()):
                continue
        except AttributeError:
            # Python <3.9 fallback
            abs_res = Path(abs_path).resolve()
            if str(abs_res).startswith(str(dest_root.resolve())):
                continue
        rel = Path(abs_path).resolve().relative_to(src_root.resolve())
        first = rel.parts[0] if rel.parts else ''
        if first and first not in exclude_names:
            top_level_dirs.add(first)

    dest_root.mkdir(parents=True, exist_ok=True)
    for dname in sorted(top_level_dirs):
        src_dir = src_root / dname
        if not src_dir.is_dir():
            continue
        dst_dir = dest_root / dname
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)


def write_preview(dest_root: Path) -> None:
    src_preview = Path(REPO_ROOT) / 'preview' / 'index.html'
    dst_preview_dir = dest_root / 'preview'
    dst_preview_dir.mkdir(parents=True, exist_ok=True)
    if src_preview.exists():
        shutil.copy2(src_preview, dst_preview_dir / 'index.html')


def build_outputs(dest_root: Path) -> int:
    dest_root.mkdir(parents=True, exist_ok=True)
    # Build records
    records = [build_record(p) for p in iter_json_files(REPO_ROOT)]
    # Write indexes
    write_json(records, str(dest_root / 'all_templates.json'))
    write_csv(records, str(dest_root / 'all_templates.csv'))
    # Copy preview and json trees
    write_preview(dest_root)
    copy_json_tree(dest_root)
    return len(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build static site to dist/.')
    parser.add_argument('--out', default=str(Path(REPO_ROOT) / 'dist'), help='Output directory (default: dist)')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out).resolve()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    count = build_outputs(out_dir)
    print(f"Built static site to {out_dir} ({count} templates)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

