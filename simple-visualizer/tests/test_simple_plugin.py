"""
Tests for SimpleVisualizer plugin.
"""

import pytest
from datetime import date

from tangled_api.model import Graph, Node, Edge
from tangled_simple_visualizer import SimpleVisualizer


@pytest.fixture
def visualizer():
    return SimpleVisualizer()


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


def test_render_contains_attribute_value(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "John" in result


def test_render_contains_integer_attribute(visualizer):
    graph = Graph(directed=True)
    node = Node(id="n1")
    node.set_attribute("age", 30)
    graph.add_node(node)

    result = visualizer.render(graph)
    assert "30" in result


# --- Label behavior ---

def test_label_uses_node_id_when_no_attributes(visualizer):
    graph = Graph(directed=True)
    graph.add_node(Node(id="bare-node"))

    result = visualizer.render(graph)
    assert "bare-node" in result


def test_label_uses_first_attribute_when_present(visualizer):
    graph = Graph(directed=True)
    node = Node(id="n1")
    node.set_attribute("title", "Hello")
    graph.add_node(node)

    result = visualizer.render(graph)
    assert "Hello" in result


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


def test_render_date_attribute(visualizer):
    graph = Graph(directed=True)
    node = Node(id="n1")
    node.set_attribute("birthday", date(1990, 5, 15))
    graph.add_node(node)

    result = visualizer.render(graph)
    assert "1990" in result


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


def test_render_edge_ids_in_output(visualizer):
    graph = Graph(directed=True)
    n1 = Node(id="n1")
    n2 = Node(id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="n1", target_id="n2"))

    result = visualizer.render(graph)
    assert "e1" in result


def test_render_edge_source_target_in_output(visualizer):
    graph = Graph(directed=True)
    n1 = Node(id="src-node")
    n2 = Node(id="tgt-node")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="src-node", target_id="tgt-node"))

    result = visualizer.render(graph)
    assert "src-node" in result
    assert "tgt-node" in result


def test_render_undirected_graph(visualizer):
    graph = Graph(directed=False)
    n1 = Node(id="n1")
    n2 = Node(id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="n1", target_id="n2"))

    result = visualizer.render(graph)
    assert isinstance(result, str)


# --- Directed vs undirected arrow markers ---

def test_directed_graph_includes_arrowhead_marker(visualizer):
    graph = Graph(directed=True)
    n1 = Node(id="n1")
    n2 = Node(id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="n1", target_id="n2"))

    result = visualizer.render(graph)
    assert "marker-end" in result


def test_undirected_graph_omits_marker_end(visualizer):
    graph = Graph(directed=False)
    n1 = Node(id="n1")
    n2 = Node(id="n2")
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_edge(Edge(id="e1", source_id="n1", target_id="n2"))

    result = visualizer.render(graph)
    assert "marker-end" not in result


# --- HTML structure ---

def test_render_contains_svg(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "<svg" in result


def test_render_contains_script(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "<script" in result


def test_render_contains_style(visualizer, simple_graph):
    result = visualizer.render(simple_graph)
    assert "<style" in result


# --- Plugin metadata ---

def test_name_property(visualizer):
    assert visualizer.name == "Simple Visualizer"


def test_description_property(visualizer):
    assert isinstance(visualizer.description, str)
    assert len(visualizer.description) > 0
