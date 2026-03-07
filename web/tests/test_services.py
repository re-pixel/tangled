"""
Tests for tangled_web services.

Each service function accepts a Platform and request params, returns (dict, status_code).
"""

import uuid

import pytest

from tangled_api.model import Graph, Node, Edge
from tangled_platform import Workspace
from tangled_web.services import (
    WorkspaceNotFound,
    list_data_sources,
    list_visualizers,
    load_data,
    render_graph,
    filter_graph,
    search_graph,
    reset_graph,
    execute_cli,
    get_graph_data,
)


class MockDataSourcePlugin:
    """Minimal DataSourcePlugin for testing."""

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


class MockVisualizerPlugin:
    """Minimal VisualizerPlugin for testing."""

    @property
    def name(self) -> str:
        return "Mock Visualizer"

    @property
    def description(self) -> str:
        return "Mock for testing"

    def render(self, graph: Graph) -> str:
        return f"<html>{len(graph.nodes)} nodes, {len(graph.edges)} edges</html>"


class FakePlatform:
    """Platform stub for service tests: real Workspace, mock plugins."""

    def __init__(self):
        self._workspaces = {}
        self._data_sources = {"mock": MockDataSourcePlugin()}
        self._visualizers = {"mock": MockVisualizerPlugin()}

    @property
    def data_sources(self):
        return self._data_sources

    @property
    def visualizers(self):
        return self._visualizers

    def get_data_source(self, name: str):
        return self._data_sources.get(name)

    def get_visualizer(self, name: str):
        return self._visualizers.get(name)

    def create_workspace(self, workspace_id: str | None = None) -> Workspace:
        wid = workspace_id or str(uuid.uuid4())
        ws = Workspace(wid)
        self._workspaces[wid] = ws
        return ws

    def get_workspace(self, workspace_id: str):
        return self._workspaces.get(workspace_id)


@pytest.fixture
def platform():
    return FakePlatform()


@pytest.fixture
def workspace_id(platform):
    ws = platform.create_workspace(workspace_id="ws1")
    return ws.id


# ── list_data_sources ────────────────────────────────────────────────────────


def test_list_data_sources_returns_list_and_200(platform):
    data, status = list_data_sources(platform)
    assert status == 200
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "id" in item
    assert "name" in item
    assert "description" in item
    assert "parameters" in item


# ── list_visualizers ─────────────────────────────────────────────────────────


def test_list_visualizers_returns_list_and_200(platform):
    data, status = list_visualizers(platform)
    assert status == 200
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "id" in item
    assert "name" in item
    assert "description" in item


# ── load_data ────────────────────────────────────────────────────────────────


def test_load_data_success(platform, workspace_id):
    data, status = load_data(
        platform, workspace_id,
        plugin_name="mock",
        params={},
    )
    assert status == 200
    assert data["success"] is True
    assert data["node_count"] == 2


def test_load_data_nonexistent_workspace_raises(platform):
    with pytest.raises(WorkspaceNotFound):
        load_data(platform, "nonexistent", plugin_name="mock", params={})


def test_load_data_nonexistent_plugin_returns_404(platform, workspace_id):
    data, status = load_data(
        platform, workspace_id,
        plugin_name="nonexistent",
        params={},
    )
    assert status == 404
    assert "error" in data


def test_load_data_sets_cli_cleared_false(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    ws = platform.get_workspace(workspace_id)
    assert ws._cli_cleared is False


# ── render_graph ─────────────────────────────────────────────────────────────


def test_render_graph_success(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = render_graph(platform, workspace_id, visualizer_name="mock")
    assert status == 200
    assert "html" in data
    assert "<html>" in data["html"]
    assert "2 nodes" in data["html"]


def test_render_graph_nonexistent_workspace_raises(platform):
    with pytest.raises(WorkspaceNotFound):
        render_graph(platform, "nonexistent", visualizer_name="mock")


def test_render_graph_nonexistent_visualizer_returns_404(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = render_graph(
        platform, workspace_id,
        visualizer_name="nonexistent",
    )
    assert status == 404
    assert "error" in data


# ── filter_graph ─────────────────────────────────────────────────────────────


def test_filter_graph_success(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = filter_graph(platform, workspace_id, query="age > 26")
    assert status == 200
    assert data["success"] is True
    assert data["node_count"] == 1


def test_filter_graph_nonexistent_workspace_raises(platform):
    with pytest.raises(WorkspaceNotFound):
        filter_graph(platform, "nonexistent", query="age > 26")


def test_filter_graph_invalid_query_returns_400(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = filter_graph(platform, workspace_id, query="invalidquery")
    assert status == 400
    assert "error" in data


# ── search_graph ─────────────────────────────────────────────────────────────


def test_search_graph_success(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = search_graph(platform, workspace_id, query="Alice")
    assert status == 200
    assert data["success"] is True


def test_search_graph_nonexistent_workspace_raises(platform):
    with pytest.raises(WorkspaceNotFound):
        search_graph(platform, "nonexistent", query="x")


# ── reset_graph ──────────────────────────────────────────────────────────────


def test_reset_graph_success(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    filter_graph(platform, workspace_id, query="age > 26")
    data, status = reset_graph(platform, workspace_id)
    assert status == 200
    assert data["success"] is True


def test_reset_graph_restores_node_count(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    filter_graph(platform, workspace_id, query="age > 26")
    ws = platform.get_workspace(workspace_id)
    assert len(ws.graph.nodes) == 1
    reset_graph(platform, workspace_id)
    assert len(ws.graph.nodes) == 2


def test_reset_graph_sets_cli_cleared_false(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    ws = platform.get_workspace(workspace_id)
    ws._cli_cleared = True
    reset_graph(platform, workspace_id)
    assert ws._cli_cleared is False


def test_reset_graph_nonexistent_workspace_raises(platform):
    with pytest.raises(WorkspaceNotFound):
        reset_graph(platform, "nonexistent")


# ── get_graph_data ───────────────────────────────────────────────────────────


def test_get_graph_data_success(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = get_graph_data(platform, workspace_id)
    assert status == 200
    assert "nodes" in data
    assert "edges" in data
    assert "directed" in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


def test_get_graph_data_nonexistent_workspace_raises(platform):
    with pytest.raises(WorkspaceNotFound):
        get_graph_data(platform, "nonexistent")


def test_get_graph_data_empty_workspace_returns_empty(platform, workspace_id):
    data, status = get_graph_data(platform, workspace_id)
    assert status == 200
    assert data["nodes"] == []
    assert data["edges"] == []


# ── execute_cli ──────────────────────────────────────────────────────────────


def test_execute_cli_success(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = execute_cli(
        platform, workspace_id,
        command="show nodes",
    )
    assert status == 200
    assert "result" in data


def test_execute_cli_empty_command_returns_400(platform, workspace_id):
    load_data(platform, workspace_id, plugin_name="mock", params={})
    data, status = execute_cli(platform, workspace_id, command="")
    assert status == 400
    assert "error" in data


def test_execute_cli_nonexistent_workspace_raises(platform):
    with pytest.raises(WorkspaceNotFound):
        execute_cli(platform, "nonexistent", command="show nodes")
