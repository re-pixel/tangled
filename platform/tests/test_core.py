"""
Unit tests for Platform (tangled_platform.core).
"""

import pytest

from tangled_platform import Platform


class TestPlatform:
    """Test Platform class."""

    def test_create_workspace_returns_workspace(self):
        platform = Platform()
        ws = platform.create_workspace()
        assert ws is not None
        assert ws.id is not None

    def test_create_workspace_with_id(self):
        platform = Platform()
        ws = platform.create_workspace(workspace_id="my-id")
        assert ws.id == "my-id"

    def test_get_workspace_returns_created_workspace(self):
        platform = Platform()
        ws = platform.create_workspace(workspace_id="w1")
        retrieved = platform.get_workspace("w1")
        assert retrieved is ws

    def test_get_workspace_nonexistent_returns_none(self):
        platform = Platform()
        assert platform.get_workspace("nonexistent") is None

    def test_delete_workspace_removes_workspace(self):
        platform = Platform()
        platform.create_workspace(workspace_id="w1")
        deleted = platform.delete_workspace("w1")
        assert deleted is True
        assert platform.get_workspace("w1") is None

    def test_delete_workspace_nonexistent_returns_false(self):
        platform = Platform()
        deleted = platform.delete_workspace("nonexistent")
        assert deleted is False

    def test_workspaces_property(self):
        platform = Platform()
        ws1 = platform.create_workspace(workspace_id="w1")
        ws2 = platform.create_workspace(workspace_id="w2")
        workspaces = platform.workspaces
        assert "w1" in workspaces
        assert "w2" in workspaces
        assert workspaces["w1"] is ws1
        assert workspaces["w2"] is ws2

    def test_data_sources_property(self):
        platform = Platform()
        sources = platform.data_sources
        assert isinstance(sources, dict)

    def test_visualizers_property(self):
        platform = Platform()
        visualizers = platform.visualizers
        assert isinstance(visualizers, dict)
