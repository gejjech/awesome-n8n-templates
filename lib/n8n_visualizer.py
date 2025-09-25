"""
n8n workflow visualization tools.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image, ImageDraw, ImageFont
import io

class N8nWorkflowVisualizer:
    """Creates visualizations of n8n workflows."""
    
    def __init__(self):
        self.node_colors = {
            'trigger': '#ff6b6b',
            'action': '#4ecdc4', 
            'condition': '#ffe66d',
            'function': '#a8e6cf',
            'default': '#95a5a6'
        }
        
    def _get_node_color(self, node_type: str) -> str:
        """Get color for a node based on its type."""
        if 'trigger' in node_type.lower():
            return self.node_colors['trigger']
        elif 'if' in node_type.lower() or 'switch' in node_type.lower():
            return self.node_colors['condition']
        elif 'function' in node_type.lower() or 'code' in node_type.lower():
            return self.node_colors['function']
        elif any(term in node_type.lower() for term in ['http', 'webhook', 'email', 'slack', 'telegram']):
            return self.node_colors['action']
        else:
            return self.node_colors['default']
    
    def create_workflow_graph(self, workflow_data: Dict[str, Any]) -> nx.DiGraph:
        """
        Create a NetworkX graph from n8n workflow data.
        
        Args:
            workflow_data: Parsed n8n workflow JSON
            
        Returns:
            NetworkX directed graph representing the workflow
        """
        G = nx.DiGraph()
        
        nodes = workflow_data.get('nodes', [])
        connections = workflow_data.get('connections', {})
        
        # Add nodes
        for node in nodes:
            node_id = node.get('id')
            node_name = node.get('name', 'Unnamed')
            node_type = node.get('type', 'unknown')
            position = node.get('position', [0, 0])
            
            G.add_node(
                node_id,
                label=node_name,
                type=node_type,
                pos=(position[0]/100, -position[1]/100),  # Scale and invert Y for better layout
                color=self._get_node_color(node_type)
            )
        
        # Add edges based on connections
        for source_node, source_outputs in connections.items():
            for output_type, output_connections in source_outputs.items():
                if isinstance(output_connections, list):
                    for connection_list in output_connections:
                        if isinstance(connection_list, list):
                            for connection in connection_list:
                                if isinstance(connection, dict):
                                    target_node = connection.get('node')
                                    if target_node and G.has_node(source_node) and G.has_node(target_node):
                                        G.add_edge(source_node, target_node)
        
        return G
    
    def visualize_workflow_matplotlib(
        self, 
        workflow_data: Dict[str, Any], 
        output_path: Optional[Path] = None,
        figsize: Tuple[int, int] = (12, 8),
        show: bool = False
    ) -> Optional[Path]:
        """
        Create a matplotlib visualization of the workflow.
        
        Args:
            workflow_data: Parsed n8n workflow JSON
            output_path: Path to save the visualization
            figsize: Figure size tuple
            show: Whether to show the plot interactively
            
        Returns:
            Path to saved file if output_path provided, None otherwise
        """
        try:
            G = self.create_workflow_graph(workflow_data)
            
            if len(G.nodes()) == 0:
                print("No nodes found in workflow", file=sys.stderr)
                return None
            
            plt.figure(figsize=figsize)
            
            # Use positions from n8n if available, otherwise use spring layout
            try:
                pos = nx.get_node_attributes(G, 'pos')
                if not pos or len(pos) == 0:
                    pos = nx.spring_layout(G, k=2, iterations=50)
            except:
                pos = nx.spring_layout(G, k=2, iterations=50)
            
            # Get node colors
            node_colors = [G.nodes[node].get('color', self.node_colors['default']) for node in G.nodes()]
            
            # Get node labels
            labels = {node: G.nodes[node].get('label', node[:8] + '...') if len(G.nodes[node].get('label', node)) > 10 else G.nodes[node].get('label', node) for node in G.nodes()}
            
            # Draw the graph
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, alpha=0.9)
            nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20, alpha=0.6)
            nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
            
            # Add title
            workflow_name = workflow_data.get('name', 'n8n Workflow')
            plt.title(f'n8n Workflow: {workflow_name}', fontsize=16, fontweight='bold', pad=20)
            
            # Remove axes
            plt.axis('off')
            
            # Add legend
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                          markersize=10, label=node_type.title())
                for node_type, color in self.node_colors.items() if node_type != 'default'
            ]
            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
            
            plt.tight_layout()
            
            if output_path:
                plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                print(f"Visualization saved to: {output_path}")
            
            if show:
                plt.show()
            else:
                plt.close()
            
            return output_path
            
        except Exception as e:
            print(f"Error creating visualization: {str(e)}", file=sys.stderr)
            return None
    
    def create_simple_diagram(
        self, 
        workflow_data: Dict[str, Any], 
        output_path: Path,
        width: int = 800,
        height: int = 600
    ) -> bool:
        """
        Create a simple diagram using PIL when matplotlib fails.
        
        Args:
            workflow_data: Parsed n8n workflow JSON
            output_path: Path to save the image
            width: Image width
            height: Image height
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a blank image
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            nodes = workflow_data.get('nodes', [])
            if not nodes:
                return False
            
            # Try to load a font, fallback to default if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            except:
                font = ImageFont.load_default()
                title_font = font
            
            # Draw title
            workflow_name = workflow_data.get('name', 'n8n Workflow')
            title_text = f"n8n Workflow: {workflow_name}"
            draw.text((10, 10), title_text, fill='black', font=title_font)
            
            # Calculate positions for nodes
            node_width = 120
            node_height = 40
            margin = 20
            start_y = 60
            
            cols = max(1, (width - 2 * margin) // (node_width + margin))
            
            for i, node in enumerate(nodes[:20]):  # Limit to first 20 nodes
                col = i % cols
                row = i // cols
                
                x = margin + col * (node_width + margin)
                y = start_y + row * (node_height + margin)
                
                # Draw node rectangle
                node_type = node.get('type', 'unknown')
                color = self._get_node_color(node_type)
                
                # Convert hex color to RGB
                if color.startswith('#'):
                    color = tuple(int(color[j:j+2], 16) for j in (1, 3, 5))
                else:
                    color = (149, 165, 166)  # Default gray
                
                draw.rectangle([x, y, x + node_width, y + node_height], 
                             fill=color, outline='black', width=2)
                
                # Draw node name
                node_name = node.get('name', 'Unnamed')
                if len(node_name) > 15:
                    node_name = node_name[:12] + '...'
                
                # Center text in rectangle
                text_bbox = draw.textbbox((0, 0), node_name, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x + (node_width - text_width) // 2
                text_y = y + (node_height - text_height) // 2
                
                draw.text((text_x, text_y), node_name, fill='white', font=font)
            
            # Add footer info
            footer_text = f"Contains {len(nodes)} nodes"
            draw.text((10, height - 30), footer_text, fill='gray', font=font)
            
            img.save(output_path)
            print(f"Simple diagram saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error creating simple diagram: {str(e)}", file=sys.stderr)
            return False
    
    def visualize_file(
        self, 
        file_path: Path, 
        output_path: Optional[Path] = None,
        show: bool = False
    ) -> Optional[Path]:
        """
        Create a visualization from a workflow file.
        
        Args:
            file_path: Path to the workflow JSON file
            output_path: Path to save the visualization
            show: Whether to show the plot interactively
            
        Returns:
            Path to saved file if successful, None otherwise
        """
        try:
            if not file_path.exists():
                print(f"File not found: {file_path}", file=sys.stderr)
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            # Generate output path if not provided
            if output_path is None:
                output_path = file_path.with_suffix('.png')
            
            # Try matplotlib first, fallback to simple diagram
            result = self.visualize_workflow_matplotlib(workflow_data, output_path, show=show)
            if result is None:
                # Fallback to simple diagram
                if self.create_simple_diagram(workflow_data, output_path):
                    return output_path
                else:
                    return None
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {file_path}: {str(e)}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error visualizing {file_path}: {str(e)}", file=sys.stderr)
            return None