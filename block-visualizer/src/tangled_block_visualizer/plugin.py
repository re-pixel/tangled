"""
Block Visualizer Plugin implementation.
"""

from typing import Any, Dict, List
from jinja2 import Template

from tangled_api.model import Graph
from tangled_api.plugins import VisualizerPlugin


# Template for generating graph data structure for D3.js
GRAPH_DATA_TEMPLATE = """
<script type="application/json" id="graph-data-{{ graph_id }}">
{
    "nodes": [
        {% for node in nodes %}
        {
            "id": "{{ node.id }}",
            "label": "{{ node.label }}",
            "attributes": [
                {% for attr in node.attributes %}
                {"name": "{{ attr.name }}", "value": "{{ attr.value }}", "type": "{{ attr.type }}"}{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    ],
    "edges": [
        {% for edge in edges %}
        {
            "id": "{{ edge.id }}",
            "source": "{{ edge.source }}",
            "target": "{{ edge.target }}",
            "attributes": [
                {% for attr in edge.attributes %}
                {"name": "{{ attr.name }}", "value": "{{ attr.value }}"}{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    ]
}
</script>
<div id="graph-container-{{ graph_id }}" class="graph-container block-visualizer" data-graph-id="{{ graph_id }}">
    <!-- D3.js will render SVG here -->
</div>
"""


class BlockVisualizer(VisualizerPlugin):
    """
    Block visualizer that displays nodes as rectangles with all attributes.
    
    Generates HTML structure with embedded JSON data for D3.js rendering.
    The actual SVG rendering is handled by platform JavaScript.
    """
    
    @property
    def name(self) -> str:
        return "Block Visualizer"
    
    @property
    def description(self) -> str:
        return "Displays nodes as rectangles with ID and all attributes listed."
    
    def render(self, graph: Graph) -> str:
        """
        Generate HTML for block graph visualization.
        
        Args:
            graph: The graph to visualize
            
        Returns:
            HTML string with embedded graph data
        """
        template = Template(GRAPH_DATA_TEMPLATE)
        
        nodes = []
        for node_id, node in graph.nodes.items():
            # Get label from first attribute or ID
            label = node_id
            if node.attributes:
                first_attr = next(iter(node.attributes.values()))
                label = str(first_attr.value)
            
            # Collect all attributes with type info
            attributes = []
            for attr_name, attr in node.attributes.items():
                attributes.append({
                    "name": attr_name,
                    "value": str(attr.value),
                    "type": attr.type.value,
                })
            
            nodes.append({
                "id": node_id,
                "label": label,
                "attributes": attributes,
            })
        
        edges = []
        for edge_id, edge in graph.edges.items():
            edge_attrs = []
            for attr_name, attr in edge.attributes.items():
                edge_attrs.append({
                    "name": attr_name,
                    "value": str(attr.value),
                })
            
            edges.append({
                "id": edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "attributes": edge_attrs,
            })
        
        return template.render(
            graph_id=id(graph),
            nodes=nodes,
            edges=edges,
        )
