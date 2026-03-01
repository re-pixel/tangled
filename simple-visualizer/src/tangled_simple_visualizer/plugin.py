"""
Simple Visualizer Plugin implementation.
"""

from typing import Any
from jinja2 import Template, Environment, FileSystemLoader
import os

from tangled_api.model import Graph
from tangled_api.plugins import VisualizerPlugin


class SimpleVisualizer(VisualizerPlugin):
    """
    Simple visualizer that displays nodes as circles with ID labels.
    
    Generates HTML structure with embedded JSON data for D3.js rendering.
    The actual SVG rendering is handled by platform JavaScript.
    """
    def __init__(self) -> None:
        template_path = os.path.join(os.path.dirname(__file__))
        environment = Environment(
            loader=FileSystemLoader(template_path + "/template"))
        self.template = environment.get_template(
            "template.html")
    
    @property
    def name(self) -> str:
        return "Simple Visualizer"
    
    @property
    def description(self) -> str:
        return "Displays nodes as circles with ID/name labels. Clean view of graph structure."
    
    def render(self, graph: Graph) -> str:
        nodes = []
        for node_id, node in graph.nodes.items():
            label = node_id
            if node.attributes:
                first_attr = next(iter(node.attributes.values()))
                label = str(first_attr)

            nodes.append({
                "id": node_id,
                "label": label
            })
            print(node)

        edges = []
        for edge_id, edge in graph.edges.items():
            edges.append({
                "id": edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
            })

        directed = graph.directed

        return self.template.render(
            name=id(graph),
            nodes=nodes,
            edges=edges,
            directed=directed
        )
