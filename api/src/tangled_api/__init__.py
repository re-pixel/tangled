"""
Tangled API - Core abstractions for graph visualization platform.

This package provides:
- Graph data model (Node, Edge, Graph)
- Plugin interfaces (DataSourcePlugin, VisualizerPlugin)
"""

__version__ = "0.1.0"

from tangled_api.model import Graph, Node, Edge
from tangled_api.plugins import DataSourcePlugin, VisualizerPlugin

__all__ = [
    "Graph",
    "Node",
    "Edge",
    "DataSourcePlugin",
    "VisualizerPlugin",
]
