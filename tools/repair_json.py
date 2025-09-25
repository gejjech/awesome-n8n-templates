#!/usr/bin/env python3
"""
Attempt to auto-repair malformed JSON files in-place.

Strategies:
- If file is empty or only whitespace: write []
- Try json.loads as-is; if ok, do nothing
- If parse fails: find the last closing brace '}' or ']' and try to parse the slice up to there
- If that works, write the repaired JSON back (pretty-printed, UTF-8)

Usage:
  python tools/repair_json.py <file1> <file2> ...
"""

import json
import sys
from pathlib import Path

def try_load(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def repair_json_text(text: str):
    stripped = text.strip()
    if not stripped:
        return []
    data = try_load(text)
    if data is not None:
        return data
    # Attempt: trim to last closing brace or bracket
    last_brace = stripped.rfind('}')
    last_bracket = stripped.rfind(']')
    cut = max(last_brace, last_bracket)
    if cut != -1:
        candidate = stripped[: cut + 1]
        data2 = try_load(candidate)
        if data2 is not None:
            return data2
    # Attempt: use streaming raw_decode to grab first complete top-level JSON value
    try:
        decoder = json.JSONDecoder()
        obj, end = decoder.raw_decode(stripped)
        data3 = try_load(stripped[:end])
        if data3 is not None:
            return data3
    except Exception:
        pass
    # Give up
    return None


def main(argv):
    if len(argv) < 1:
        print('Usage: repair_json.py <files...>')
        return 2
    exit_code = 0
    for arg in argv:
        path = Path(arg)
        try:
            original = path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f'FAIL: {path} -> cannot read: {e}')
            exit_code = 1
            continue
        fixed = repair_json_text(original)
        if fixed is None:
            print(f'NOFIX: {path} -> could not auto-repair')
            exit_code = 1
            continue
        try:
            # Write pretty-printed but compact enough
            path.write_text(json.dumps(fixed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(f'FIXED: {path}')
        except Exception as e:
            print(f'FAIL: {path} -> cannot write: {e}')
            exit_code = 1
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))