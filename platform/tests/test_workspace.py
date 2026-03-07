"""
Unit tests for Workspace (tangled_platform.workspace).
"""

import pytest

from tangled_platform import Workspace


class TestWorkspace:
    """Test Workspace class."""

    def test_workspace_has_id(self):
        ws = Workspace(workspace_id="w1")
        assert ws.id == "w1"

    def test_graph_initially_none(self):
        ws = Workspace(workspace_id="w1")
        assert ws.graph is None
        assert ws.original_graph is None

    def test_load_data_populates_graph(self, mock_data_source):
        ws = Workspace(workspace_id="w1")
        ws.load_data(mock_data_source)
        assert ws.graph is not None
        assert len(ws.graph.nodes) == 2
        assert len(ws.graph.edges) == 1
        assert ws.original_graph is ws.graph

    def test_filter_reduces_graph(self, mock_data_source):
        ws = Workspace(workspace_id="w1")
        ws.load_data(mock_data_source)
        ws.filter("age > 26")
        assert len(ws.graph.nodes) == 1
        assert "n1" in ws.graph.nodes

    def test_filter_without_graph_raises(self):
        ws = Workspace(workspace_id="w1")
        with pytest.raises(ValueError, match="No graph loaded"):
            ws.filter("age > 25")

    def test_reset_restores_original(self, mock_data_source):
        ws = Workspace(workspace_id="w1")
        ws.load_data(mock_data_source)
        ws.filter("age > 26")
        assert len(ws.graph.nodes) == 1
        ws.reset()
        assert len(ws.graph.nodes) == 2
        assert ws.graph is ws.original_graph

    def test_render_returns_html(self, mock_data_source, mock_visualizer):
        ws = Workspace(workspace_id="w1")
        ws.load_data(mock_data_source)
        html = ws.render(mock_visualizer)
        assert "<html>" in html
        assert "2 nodes" in html or "2" in html

    def test_render_empty_graph_returns_empty_string(self, mock_visualizer):
        ws = Workspace(workspace_id="w1")
        html = ws.render(mock_visualizer)
        assert html == ""
