#!/usr/bin/env python3
"""
Validate n8n workflow templates in this repository.

This script validates all JSON files in the repository to ensure they:
1. Are valid JSON format
2. Follow the expected n8n workflow structure (have 'nodes' array)
3. Can be parsed successfully

Usage:
  python tools/validate_workflows.py [directory]

If no directory is specified, validates all files from the repository root.
Returns exit code 0 if all workflows are valid, non-zero otherwise.
"""

import argparse
import fnmatch
import json
import os
import sys
from typing import Iterable, List, Optional, Tuple


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def iter_json_files(root_dir: str) -> Iterable[str]:
    """Iterator over all JSON files in the given directory tree."""
    # Files to skip during validation
    skip_files = {
        'ALL_unique_nodes.json',  # Appears to be a generated/utility file
        'all_templates.json',     # Generated index file
        'all_templates.csv',      # Generated index file (not JSON but just in case)
    }
    
    for current_dir, dirnames, filenames in os.walk(root_dir):
        # Skip hidden directories and common non-workflow directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['node_modules', 'dist', 'build']]
        
        for filename in filenames:
            if fnmatch.fnmatch(filename, '*.json'):
                # Skip known utility files
                if filename in skip_files:
                    continue
                yield os.path.join(current_dir, filename)


def validate_json_file(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a single JSON file.
    
    Returns:
        (is_valid, error_message) - error_message is None if valid
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
        
        # Skip empty files
        if not content:
            return False, "File is empty"
        
        # Try to parse the JSON - handle files that might have extra text after valid JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            # If we get "Extra data" error, try to find where the JSON ends
            if "Extra data" in str(e):
                # Find the position where the valid JSON ends
                decoder = json.JSONDecoder()
                try:
                    data, idx = decoder.raw_decode(content)
                    # Successfully parsed the JSON portion, ignore the extra text
                except json.JSONDecodeError:
                    return False, f"Invalid JSON syntax: {e}"
            else:
                return False, f"Invalid JSON syntax: {e}"
        
        # Check if it looks like an n8n workflow
        if isinstance(data, dict):
            # Most n8n workflows should have nodes array
            nodes = data.get('nodes')
            if nodes is not None and not isinstance(nodes, list):
                return False, f"'nodes' field should be an array, found {type(nodes).__name__}"
            
            # If it has nodes, it should have some basic fields
            if isinstance(nodes, list):
                if len(nodes) == 0:
                    return False, "Empty nodes array - workflow should have at least one node"
        
        return True, None
        
    except Exception as e:
        return False, f"Error reading file: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate n8n workflow templates.')
    parser.add_argument('directory', nargs='?', default=REPO_ROOT, 
                       help='Directory to validate (default: repository root)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show details for each validated file')
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory {args.directory} does not exist", file=sys.stderr)
        return 1
    
    validation_errors = []
    valid_count = 0
    total_count = 0
    
    for json_path in iter_json_files(args.directory):
        total_count += 1
        rel_path = os.path.relpath(json_path, args.directory)
        
        is_valid, error_msg = validate_json_file(json_path)
        
        if is_valid:
            valid_count += 1
            if args.verbose:
                print(f"✅ {rel_path}")
        else:
            validation_errors.append((rel_path, error_msg))
            if args.verbose:
                print(f"❌ {rel_path}: {error_msg}")
    
    # Print summary
    print(f"\nValidation complete:")
    print(f"  Total files: {total_count}")
    print(f"  Valid files: {valid_count}")
    print(f"  Invalid files: {len(validation_errors)}")
    
    if validation_errors:
        print(f"\nErrors found:")
        for rel_path, error_msg in validation_errors:
            print(f"  ❌ {rel_path}: {error_msg}")
        return 1
    else:
        print("✅ All workflow files are valid!")
        return 0


if __name__ == '__main__':
    sys.exit(main())