"""
Tests for tangled_web CLI.
"""

import pytest
from datetime import date

from tangled_api.model import Graph, Node, Edge
from tangled_web.cli import CLI, CLIResult


class FakeWorkspace:
    """Minimal workspace stub for CLI tests."""

    def __init__(self, graph: Graph):
        self._original_graph = graph
        self._current_graph = graph
        self._cli_cleared = False

    @property
    def graph(self) -> Graph:
        return self._current_graph

    def filter(self, query: str) -> None:
        self._current_graph = self._current_graph.filter_by_query(query)

    def search(self, query: str) -> None:
        query_lower = query.lower()
        matching_ids = [
            node_id for node_id, node in self._current_graph.nodes.items()
            if any(
                query_lower in k.lower() or query_lower in str(v.value).lower()
                for k, v in node.attributes.items()
            )
        ]
        self._current_graph = self._current_graph.create_subgraph(matching_ids)

    def reset(self) -> None:
        self._current_graph = self._original_graph


@pytest.fixture
def empty_graph():
    return Graph(directed=True)


@pytest.fixture
def simple_graph():
    graph = Graph(directed=True)
    n1 = Node(id="n1")
    n1.set_attribute("name", "Alice")
    n1.set_attribute("age", 30)
    n2 = Node(id="n2")
    n2.set_attribute("name", "Bob")
    n2.set_attribute("age", 25)
    graph.add_node(n1)
    graph.add_node(n2)
    edge = Edge(id="e1", source_id="n1", target_id="n2")
    edge.set_attribute("label", "knows")
    graph.add_edge(edge)
    return graph


@pytest.fixture
def ws(simple_graph):
    return FakeWorkspace(simple_graph)


@pytest.fixture
def cli(ws):
    return CLI(ws)


@pytest.fixture
def empty_ws(empty_graph):
    return FakeWorkspace(empty_graph)


@pytest.fixture
def empty_cli(empty_ws):
    return CLI(empty_ws)


def test_cli_result_ok():
    r = CLIResult.ok("done")
    assert r.output == "done"
    assert r.error == ""
    assert r.changed is False


def test_cli_result_ok_changed():
    r = CLIResult.ok("done", changed=True)
    assert r.changed is True


def test_cli_result_err():
    r = CLIResult.err("oops")
    assert r.error == "oops"
    assert r.output == ""


def test_empty_command_returns_empty(cli):
    r = cli.execute("")
    assert r.output == ""
    assert not r.error


def test_whitespace_command_returns_empty(cli):
    r = cli.execute("   ")
    assert r.output == ""
    assert not r.error


def test_unknown_command_returns_error(cli):
    r = cli.execute("fly")
    assert r.error
    assert "unknown" in r.error.lower()


def test_help_returns_output(cli):
    r = cli.execute("help")
    assert r.output
    assert not r.error


def test_create_node_basic(empty_cli, empty_ws):
    r = empty_cli.execute("create node --id=x")
    assert not r.error
    assert r.changed
    assert "x" in empty_ws.graph.nodes


def test_create_node_with_properties(empty_cli, empty_ws):
    r = empty_cli.execute("create node --id=x --property Name=Alice --property Age=25")
    assert not r.error
    node = empty_ws.graph.nodes["x"]
    assert node.get_attribute_value("Name") == "Alice"
    assert node.get_attribute_value("Age") == 25


def test_create_node_integer_type_inferred(empty_cli, empty_ws):
    empty_cli.execute("create node --id=x --property score=42")
    from tangled_api.model.attribute import AttributeValue
    attr = empty_ws.graph.nodes["x"].get_attribute("score")
    assert attr.type == AttributeValue.INTEGER
    assert attr.value == 42


def test_create_node_float_type_inferred(empty_cli, empty_ws):
    empty_cli.execute("create node --id=x --property ratio=3.14")
    from tangled_api.model.attribute import AttributeValue
    attr = empty_ws.graph.nodes["x"].get_attribute("ratio")
    assert attr.type == AttributeValue.FLOAT


def test_create_node_date_type_inferred(empty_cli, empty_ws):
    empty_cli.execute("create node --id=x --property dob=2000-01-01")
    from tangled_api.model.attribute import AttributeValue
    attr = empty_ws.graph.nodes["x"].get_attribute("dob")
    assert attr.type == AttributeValue.DATE
    assert attr.value == date(2000, 1, 1)


def test_create_node_missing_id_returns_error(empty_cli):
    r = empty_cli.execute("create node")
    assert r.error


def test_create_node_duplicate_id_returns_error(cli):
    r = cli.execute("create node --id=n1")
    assert r.error
    assert "already exists" in r.error.lower()


def test_create_edge_basic(cli, ws):
    r = cli.execute("create edge --id=e2 n1 n2")
    assert not r.error
    assert r.changed
    assert "e2" in ws.graph.edges


def test_create_edge_with_property(cli, ws):
    r = cli.execute("create edge --id=e2 n1 n2 --property weight=5")
    assert not r.error
    assert ws.graph.edges["e2"].get_attribute_value("weight") == 5


def test_create_edge_missing_id_returns_error(cli):
    r = cli.execute("create edge n1 n2")
    assert r.error


def test_create_edge_missing_nodes_returns_error(cli):
    r = cli.execute("create edge --id=e2")
    assert r.error


def test_create_edge_nonexistent_source_returns_error(cli):
    r = cli.execute("create edge --id=e2 ghost n2")
    assert r.error
    assert "does not exist" in r.error.lower()


def test_create_edge_nonexistent_target_returns_error(cli):
    r = cli.execute("create edge --id=e2 n1 ghost")
    assert r.error


def test_create_edge_duplicate_id_returns_error(cli):
    r = cli.execute("create edge --id=e1 n1 n2")
    assert r.error
    assert "already exists" in r.error.lower()


def test_edit_node_changes_attribute(cli, ws):
    r = cli.execute("edit node --id=n1 --property age=99")
    assert not r.error
    assert r.changed
    assert ws.graph.nodes["n1"].get_attribute_value("age") == 99


def test_edit_node_preserves_type(cli, ws):
    r = cli.execute("edit node --id=n1 --property age=50")
    assert not r.error
    from tangled_api.model.attribute import AttributeValue
    assert ws.graph.nodes["n1"].get_attribute("age").type == AttributeValue.INTEGER


def test_edit_node_missing_id_returns_error(cli):
    r = cli.execute("edit node --property age=5")
    assert r.error


def test_edit_node_no_properties_returns_error(cli):
    r = cli.execute("edit node --id=n1")
    assert r.error


def test_edit_node_nonexistent_returns_error(cli):
    r = cli.execute("edit node --id=ghost --property age=5")
    assert r.error
    assert "does not exist" in r.error.lower()


def test_edit_edge_changes_attribute(cli, ws):
    r = cli.execute("edit edge --id=e1 --property label=friends")
    assert not r.error
    assert r.changed
    assert ws.graph.edges["e1"].get_attribute_value("label") == "friends"


def test_edit_edge_nonexistent_returns_error(cli):
    r = cli.execute("edit edge --id=ghost --property label=x")
    assert r.error


def test_delete_node_with_no_edges(empty_cli, empty_ws):
    empty_cli.execute("create node --id=x")
    r = empty_cli.execute("delete node --id=x")
    assert not r.error
    assert r.changed
    assert "x" not in empty_ws.graph.nodes


def test_delete_node_with_edges_returns_error(cli):
    r = cli.execute("delete node --id=n1")
    assert r.error
    assert "edge" in r.error.lower()


def test_delete_node_nonexistent_returns_error(cli):
    r = cli.execute("delete node --id=ghost")
    assert r.error


def test_delete_node_missing_id_returns_error(cli):
    r = cli.execute("delete node")
    assert r.error


def test_delete_edge_basic(cli, ws):
    r = cli.execute("delete edge --id=e1")
    assert not r.error
    assert r.changed
    assert "e1" not in ws.graph.edges


def test_delete_edge_nonexistent_returns_error(cli):
    r = cli.execute("delete edge --id=ghost")
    assert r.error


def test_delete_edge_missing_id_returns_error(cli):
    r = cli.execute("delete edge")
    assert r.error


def test_filter_basic(cli, ws):
    r = cli.execute("filter age > 26")
    assert not r.error
    assert r.changed
    assert "n1" in ws.graph.nodes
    assert "n2" not in ws.graph.nodes


def test_filter_no_query_returns_error(cli):
    r = cli.execute("filter")
    assert r.error


def test_filter_invalid_format_returns_error(cli):
    r = cli.execute("filter invalidquery")
    assert r.error


def test_filter_wrong_type_returns_error(cli):
    r = cli.execute("filter age > notanumber")
    assert r.error


def test_search_by_value(cli, ws):
    r = cli.execute("search Alice")
    assert not r.error
    assert r.changed
    assert "n1" in ws.graph.nodes
    assert "n2" not in ws.graph.nodes


def test_search_no_query_returns_error(cli):
    r = cli.execute("search")
    assert r.error


def test_search_no_match_returns_empty_graph(cli, ws):
    r = cli.execute("search zzznomatch")
    assert not r.error
    assert len(ws.graph.nodes) == 0


def test_reset_restores_original_graph(cli, ws):
    cli.execute("filter age > 26")
    assert len(ws.graph.nodes) == 1
    r = cli.execute("reset")
    assert not r.error
    assert r.changed
    assert len(ws.graph.nodes) == 2


def test_reset_clears_cleared_flag(cli, ws):
    cli.execute("clear")
    assert ws._cli_cleared is True
    cli.execute("reset")
    assert ws._cli_cleared is False


def test_clear_sets_cleared_flag(cli, ws):
    r = cli.execute("clear")
    assert not r.error
    assert r.changed
    assert ws._cli_cleared is True


def test_cleared_blocks_commands(cli):
    cli.execute("clear")
    r = cli.execute("create node --id=x")
    assert r.error
    assert "cleared" in r.error.lower()


def test_cleared_allows_help(cli):
    cli.execute("clear")
    r = cli.execute("help")
    assert not r.error


def test_cleared_allows_show(cli):
    cli.execute("clear")
    r = cli.execute("show nodes")
    assert not r.error


def test_show_nodes(cli):
    r = cli.execute("show nodes")
    assert not r.error
    assert "n1" in r.output
    assert "n2" in r.output


def test_show_edges(cli):
    r = cli.execute("show edges")
    assert not r.error
    assert "e1" in r.output


def test_show_nodes_empty(empty_cli):
    r = empty_cli.execute("show nodes")
    assert not r.error
    assert "no nodes" in r.output.lower()


def test_show_edges_empty(empty_cli):
    r = empty_cli.execute("show edges")
    assert not r.error
    assert "no edges" in r.output.lower()


def test_show_invalid_kind_returns_error(cli):
    r = cli.execute("show everything")
    assert r.error


def test_show_no_args_returns_error(cli):
    r = cli.execute("show")
    assert r.error


def test_filter_then_search(cli, ws):
    cli.execute("filter age >= 25")
    assert len(ws.graph.nodes) == 2
    cli.execute("search Alice")
    assert len(ws.graph.nodes) == 1
    assert "n1" in ws.graph.nodes


def test_create_then_delete_node(empty_cli, empty_ws):
    empty_cli.execute("create node --id=x")
    empty_cli.execute("create node --id=y")
    empty_cli.execute("create edge --id=e1 x y")
    empty_cli.execute("delete edge --id=e1")
    r = empty_cli.execute("delete node --id=x")
    assert not r.error
    assert "x" not in empty_ws.graph.nodes