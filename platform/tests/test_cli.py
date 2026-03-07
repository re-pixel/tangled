"""
Unit tests for platform CLI (tangled_platform.cli).
"""

import pytest

from tangled_api.model import Graph, Node, Edge
from tangled_platform.cli import CLI


class TestCLI:
    """Test platform CLI (graph-based)."""

    def test_help_returns_docstring(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("help")
        assert result
        assert "Error:" not in result

    def test_empty_command_returns_empty(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("")
        assert result == ""

    def test_unknown_command_returns_error(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("fly")
        assert "Error:" in result
        assert "Unknown" in result or "unknown" in result

    def test_create_node_basic(self, empty_graph):
        cli = CLI(empty_graph)
        result = cli.execute("create node --id=x")
        assert "Error:" not in result
        assert "x" in empty_graph.nodes

    def test_create_node_with_properties(self, empty_graph):
        cli = CLI(empty_graph)
        result = cli.execute("create node --id=x --property Name=Alice --property Age=25")
        assert "Error:" not in result
        node = empty_graph.nodes["x"]
        assert node.get_attribute_value("Name") == "Alice"
        assert node.get_attribute_value("Age") == 25

    def test_create_node_duplicate_returns_error(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("create node --id=n1")
        assert "Error:" in result
        assert "already exists" in result

    def test_create_edge_basic(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("create edge --id=e2 n1 n2")
        assert "Error:" not in result
        assert "e2" in simple_graph.edges

    def test_create_edge_missing_id_returns_error(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("create edge n1 n2")
        assert "Error:" in result

    def test_edit_node(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("edit node --id=n1 --property age=99")
        assert "Error:" not in result
        assert simple_graph.nodes["n1"].get_attribute_value("age") == 99

    def test_delete_edge_then_node(self, empty_graph):
        cli = CLI(empty_graph)
        cli.execute("create node --id=x")
        cli.execute("create node --id=y")
        cli.execute("create edge --id=e1 x y")
        cli.execute("delete edge --id=e1")
        result = cli.execute("delete node --id=x")
        assert "Error:" not in result
        assert "x" not in empty_graph.nodes

    def test_delete_node_with_edges_returns_error(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("delete node --id=n1")
        assert "Error:" in result
        assert "edge" in result.lower()

    def test_filter_basic(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("filter age > 26")
        assert "Error:" not in result
        assert "n1" in simple_graph.nodes
        assert "n2" not in simple_graph.nodes

    def test_filter_empty_query_returns_error(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("filter")
        assert "Error:" in result

    def test_search_by_value(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("search Alice")
        assert "Error:" not in result
        assert "n1" in simple_graph.nodes
        assert "n2" not in simple_graph.nodes

    def test_clear_removes_all(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("clear")
        assert "Error:" not in result
        assert len(simple_graph.nodes) == 0
        assert len(simple_graph.edges) == 0

    def test_show_nodes(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("show nodes")
        assert "Error:" not in result
        assert "n1" in result
        assert "n2" in result

    def test_show_edges(self, simple_graph):
        cli = CLI(simple_graph)
        result = cli.execute("show edges")
        assert "Error:" not in result
        assert "e1" in result
