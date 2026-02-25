"""
Simple Visualizer Plugin implementation.
"""

from typing import Any
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
            "label": "{{ node.label }}"
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    ],
    "edges": [
        {% for edge in edges %}
        {
            "id": "{{ edge.id }}",
            "source": "{{ edge.source }}",
            "target": "{{ edge.target }}"
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    ]
}
</script>
<div id="graph-container-{{ graph_id }}" class="graph-container simple-visualizer" data-graph-id="{{ graph_id }}">
    <!-- D3.js will render SVG here -->
</div>
"""


class SimpleVisualizer(VisualizerPlugin):
    """
    Simple visualizer that displays nodes as circles with ID labels.
    
    Generates HTML structure with embedded JSON data for D3.js rendering.
    The actual SVG rendering is handled by platform JavaScript.
    """
    
    @property
    def name(self) -> str:
        return "Simple Visualizer"
    
    @property
    def description(self) -> str:
        return "Displays nodes as circles with ID/name labels. Clean view of graph structure."
    
    def render(self, graph: Graph) -> str:
        """
        Generate HTML for simple graph visualization.
        
        Args:
            graph: The graph to visualize
            
        Returns:
            HTML string with embedded graph data
        """
        # TODO: Implement rendering
        # 1. Extract node data (id, label from first attribute or id)
        # 2. Extract edge data (source, target)
        # 3. Render template with graph data
        
        template = Template(GRAPH_DATA_TEMPLATE)
        
        nodes = []
        for node_id, node in graph.nodes.items():
            # Use first attribute value as label, or fall back to ID
            label = node_id
            if node.attributes:
                first_attr = next(iter(node.attributes.values()))
                label = str(first_attr)
            nodes.append({"id": node_id, "label": label})
        
        edges = []
        for edge_id, edge in graph.edges.items():
            edges.append({
                "id": edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
            })
        
        return template.render(
            graph_id=id(graph),
            nodes=nodes,
            edges=edges,
        )
