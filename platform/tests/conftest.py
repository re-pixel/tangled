"""
Shared fixtures for platform tests.
"""

import pytest

from tangled_api.model import Graph, Node, Edge


class MockDataSourcePlugin:
    """Minimal DataSourcePlugin implementation for testing."""

    @property
    def name(self) -> str:
        return "Mock Data Source"

    @property
    def description(self) -> str:
        return "Mock for testing"

    @property
    def parameters(self):
        return []

    def load(self, **params) -> Graph:
        graph = Graph(directed=True)
        n1 = Node("n1")
        n1.set_attribute("name", "Alice")
        n1.set_attribute("age", 30)
        n2 = Node("n2")
        n2.set_attribute("name", "Bob")
        n2.set_attribute("age", 25)
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge(Edge("e1", "n1", "n2"))
        return graph


class MockVisualizerPlugin:
    """Minimal VisualizerPlugin implementation for testing."""

    @property
    def name(self) -> str:
        return "Mock Visualizer"

    @property
    def description(self) -> str:
        return "Mock for testing"

    def render(self, graph: Graph) -> str:
        return f"<html>{len(graph.nodes)} nodes, {len(graph.edges)} edges</html>"


@pytest.fixture
def mock_data_source():
    return MockDataSourcePlugin()


@pytest.fixture
def mock_visualizer():
    return MockVisualizerPlugin()


@pytest.fixture
def simple_graph():
    """Graph with 2 nodes and 1 edge for CLI/workspace tests."""
    graph = Graph(directed=True)
    n1 = Node(id="n1")
    n1.set_attribute("name", "Alice")
    n1.set_attribute("age", 30)
    n2 = Node(id="n2")
    n2.set_attribute("name", "Bob")
    n2.set_attribute("age", 25)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="n1", target_id="n2"))
    return graph


@pytest.fixture
def empty_graph():
    """Empty graph for tests."""
    return Graph(directed=True)
