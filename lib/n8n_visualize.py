#!/usr/bin/env python3
"""
n8n-visualize command-line tool.
Creates visualizations of n8n workflow JSON files.
"""
import sys
import argparse
from pathlib import Path
from n8n_visualizer import N8nWorkflowVisualizer

def main():
    parser = argparse.ArgumentParser(description='Create visualizations of n8n workflow JSON files')
    parser.add_argument('input', help='Path to JSON workflow file')
    parser.add_argument('-o', '--output', help='Output image file path (default: same as input with .png extension)')
    parser.add_argument('--no-show', action='store_true', help='Do not show the visualization interactively')
    parser.add_argument('--width', type=int, default=800, help='Image width in pixels (default: 800)')
    parser.add_argument('--height', type=int, default=600, help='Image height in pixels (default: 600)')
    parser.add_argument('--format', choices=['png', 'svg', 'pdf'], default='png', 
                       help='Output format (default: png)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input file does not exist: {input_path}", file=sys.stderr)
        return 1
    
    if not input_path.is_file():
        print(f"Error: Input path is not a file: {input_path}", file=sys.stderr)
        return 1
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(f'.{args.format}')
    
    # Create visualization
    visualizer = N8nWorkflowVisualizer()
    result = visualizer.visualize_file(
        input_path, 
        output_path, 
        show=not args.no_show
    )
    
    if result:
        print(f"Visualization created: {result}")
        return 0
    else:
        print("Failed to create visualization", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())