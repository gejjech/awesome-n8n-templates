#!/usr/bin/env python3
"""
n8n-validate command-line tool.
Validates n8n workflow JSON files.
"""
import sys
import argparse
from pathlib import Path
from n8n_validator import N8nWorkflowValidator, validate_workflows_in_directory

def main():
    parser = argparse.ArgumentParser(description='Validate n8n workflow JSON files')
    parser.add_argument('path', help='Path to JSON file or directory to validate')
    parser.add_argument('--recursive', '-r', action='store_true', 
                       help='Recursively validate all JSON files in subdirectories')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        return 1
    
    if path.is_file():
        # Validate single file
        validator = N8nWorkflowValidator()
        if validator.validate_file(path):
            if args.verbose:
                print(f"✅ Valid workflow: {path}")
            return 0
        else:
            print(f"❌ Invalid workflow: {path}", file=sys.stderr)
            return 1
    
    elif path.is_dir():
        # Validate directory
        if validate_workflows_in_directory(path, recursive=args.recursive):
            return 0
        else:
            return 1
    
    else:
        print(f"Error: Invalid path type: {path}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())