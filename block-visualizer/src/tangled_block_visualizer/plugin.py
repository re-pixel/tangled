"""
Block Visualizer Plugin implementation.
"""

from typing import Any, Dict, List
from jinja2 import Environment, FileSystemLoader
import os

from tangled_api.model import Graph
from tangled_api.plugins import VisualizerPlugin


class BlockVisualizer(VisualizerPlugin):
    """
    Block visualizer that displays nodes as rectangles with all attributes.

    Generates HTML structure with embedded JSON data for D3.js rendering.
    The actual SVG rendering is handled by platform JavaScript.
    """

    def __init__(self) -> None:
        template_path = os.path.join(os.path.dirname(__file__))
        environment = Environment(
            loader=FileSystemLoader(template_path + "/template"))
        self.template = environment.get_template("template.html")

    @property
    def name(self) -> str:
        return "Block Visualizer"

    @property
    def description(self) -> str:
        return "Displays nodes as rectangles with ID and all attributes listed."

    def render(self, graph: Graph) -> str:
        nodes = []
        for node_id, node in graph.nodes.items():
            label = node_id
            if node.attributes:
                first_attr = next(iter(node.attributes.values()))
                label = str(first_attr.value)

            attributes = []
            for attr_name, attr in node.attributes.items():
                value = attr.value
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                attributes.append({
                    "name": attr_name,
                    "value": str(value),
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
                value = attr.value
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                edge_attrs.append({
                    "name": attr_name,
                    "value": str(value),
                })

            edges.append({
                "id": edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "attributes": edge_attrs,
            })

        return self.template.render(
            name=id(graph),
            nodes=nodes,
            edges=edges,
            directed=graph.directed,
        )