"""
n8n workflow validation and visualization tools.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

class N8nWorkflowValidator:
    """Validates n8n workflow JSON files."""
    
    def __init__(self):
        self.required_fields = ['nodes']  # Only nodes is truly required
        self.node_required_fields = ['id', 'name', 'type', 'position']
        
    def validate_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """
        Validate a single n8n workflow.
        
        Args:
            workflow_data: Parsed JSON workflow data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check for required top-level fields
            for field in self.required_fields:
                if field not in workflow_data:
                    print(f"Missing required field: {field}", file=sys.stderr)
                    return False
            
            # Validate nodes array
            nodes = workflow_data.get('nodes', [])
            if not isinstance(nodes, list):
                print("'nodes' must be an array", file=sys.stderr)
                return False
                
            if len(nodes) == 0:
                print("Workflow must have at least one node", file=sys.stderr)
                return False
            
            # Validate each node
            node_ids = set()
            for i, node in enumerate(nodes):
                if not isinstance(node, dict):
                    print(f"Node {i} must be an object", file=sys.stderr)
                    return False
                
                # Check required node fields
                for field in self.node_required_fields:
                    if field not in node:
                        print(f"Node {i} missing required field: {field}", file=sys.stderr)
                        return False
                
                # Check for duplicate node IDs
                node_id = node.get('id')
                if node_id in node_ids:
                    print(f"Duplicate node ID: {node_id}", file=sys.stderr)
                    return False
                node_ids.add(node_id)
                
                # Validate position array
                position = node.get('position', [])
                if not isinstance(position, list) or len(position) != 2:
                    print(f"Node {i} position must be array of 2 numbers", file=sys.stderr)
                    return False
                
                if not all(isinstance(p, (int, float)) for p in position):
                    print(f"Node {i} position values must be numbers", file=sys.stderr)
                    return False
            
            # Validate meta field if present
            meta = workflow_data.get('meta', {})
            if 'meta' in workflow_data and not isinstance(meta, dict):
                print("'meta' must be an object", file=sys.stderr)
                return False
                
            return True
            
        except Exception as e:
            print(f"Validation error: {str(e)}", file=sys.stderr)
            return False
    
    def validate_file(self, file_path: Path) -> bool:
        """
        Validate a workflow file.
        
        Args:
            file_path: Path to the workflow JSON file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not file_path.exists():
                print(f"File not found: {file_path}", file=sys.stderr)
                return False
                
            if not file_path.suffix.lower() == '.json':
                print(f"Not a JSON file: {file_path}", file=sys.stderr)
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    workflow_data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON in {file_path}: {str(e)}", file=sys.stderr)
                    return False
            
            return self.validate_workflow(workflow_data)
            
        except Exception as e:
            print(f"Error validating {file_path}: {str(e)}", file=sys.stderr)
            return False


def validate_workflows_in_directory(directory: Path, recursive: bool = True) -> bool:
    """
    Validate all n8n workflows in a directory.
    
    Args:
        directory: Directory to search for workflows
        recursive: Whether to search subdirectories
        
    Returns:
        True if all workflows are valid, False otherwise
    """
    validator = N8nWorkflowValidator()
    all_valid = True
    workflow_count = 0
    
    if recursive:
        json_files = list(directory.rglob('*.json'))
    else:
        json_files = list(directory.glob('*.json'))
    
    # Filter out obviously non-workflow files
    workflow_files = []
    for file_path in json_files:
        # Skip files in certain directories that are likely not workflows
        skip_dirs = {'node_modules', '.git', 'workflow-visualizations', '__pycache__'}
        if any(part in skip_dirs for part in file_path.parts):
            continue
        
        # Skip files that are clearly not n8n workflows based on name patterns
        skip_patterns = {'package.json', 'tsconfig.json'}
        # Skip index files but not individual templates
        if file_path.name.startswith('all_templates.'):
            continue
        if file_path.name in skip_patterns:
            continue
            
        workflow_files.append(file_path)
    
    print(f"Found {len(workflow_files)} potential workflow files to validate")
    
    for file_path in workflow_files:
        try:
            # Quick check if this looks like an n8n workflow
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    # Basic heuristic: n8n workflows should have 'nodes' and typically 'meta'
                    if not isinstance(data, dict) or 'nodes' not in data:
                        continue  # Skip files that don't look like n8n workflows
                except json.JSONDecodeError:
                    continue  # Skip invalid JSON files
            
            workflow_count += 1
            print(f"Validating: {file_path}")
            
            if not validator.validate_file(file_path):
                print(f"❌ Validation failed for: {file_path}")
                all_valid = False
            else:
                print(f"✅ Valid workflow: {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
            all_valid = False
    
    print(f"\nValidated {workflow_count} n8n workflows")
    if all_valid:
        print("✅ All workflows are valid!")
    else:
        print("❌ Some workflows failed validation")
        
    return all_valid