"""
Tests for BlockVisualizer plugin.
"""

import pytest
from datetime import date

from tangled_api.model import Graph, Node, Edge
from tangled_block_visualizer import BlockVisualizer


@pytest.fixture
def visualizer():
    return BlockVisualizer()


@pytest.fixture
def simple_graph():
    graph = Graph(directed=True)
    node = Node(id="node-1")
    node.set_attribute("name", "John")
    node.set_attribute("age", 30)
    graph.add_node(node)
    return graph


# --- render() base cases ---

def test_render_returns_string(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert isinstance(result, str)


def test_render_empty_graph_does_not_crash(visualizer):
    graph = Graph(directed=True)
    result = visualizer.render(graph)
    assert isinstance(result, str)


def test_render_contains_node_id(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "node-1" in result


def test_render_contains_attribute_name(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "name" in result


def test_render_contains_attribute_value(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "John" in result


def test_render_contains_integer_attribute(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "30" in result


# --- Multiple nodes ---

def test_render_multiple_nodes(visualizer):
    graph = Graph(directed=True)
    for i in range(3):
        node = Node(id=f"node-{i}")
        node.set_attribute("label", f"Label {i}")
        graph.add_node(node)

    result = visualizer.render(graph)

    assert "node-0" in result
    assert "node-1" in result
    assert "node-2" in result


# --- Node without attributes ---

def test_render_node_without_attributes(visualizer):
    graph = Graph(directed=True)
    graph.add_node(Node(id="empty-node"))

    result = visualizer.render(graph)
    assert "empty-node" in result


# --- Different attribute types ---

def test_render_float_attribute(visualizer):
    graph = Graph(directed=True)
    node = Node(id="n1")
    node.set_attribute("score", 9.5)
    graph.add_node(node)

    result = visualizer.render(graph)
    assert "9.5" in result


def test_render_date_attribute_as_iso_string(visualizer):
    graph = Graph(directed=True)
    node = Node(id="n1")
    node.set_attribute("birthday", date(1990, 5, 15))
    graph.add_node(node)

    result = visualizer.render(graph)
    assert "1990-05-15" in result


# --- Edges ---

def test_render_with_edges_does_not_crash(visualizer):
    graph = Graph(directed=True)
    n1 = Node(id="n1")
    n2 = Node(id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="n1", target_id="n2"))

    result = visualizer.render(graph)
    assert isinstance(result, str)


def test_render_undirected_graph(visualizer):
    graph = Graph(directed=False)
    n1 = Node(id="n1")
    n2 = Node(id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="n1", target_id="n2"))

    result = visualizer.render(graph)
    assert isinstance(result, str)


# --- HTML structure ---

def test_render_contains_svg(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "<svg" in result


def test_render_contains_script(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "<script" in result