"""
Unit tests for PluginRegistry (tangled_platform.registry).
"""

import pytest

from tangled_platform import PluginRegistry


class TestPluginRegistry:
    """Test PluginRegistry class."""

    def test_registry_initializes(self):
        registry = PluginRegistry()
        assert registry is not None

    def test_data_sources_is_dict(self):
        registry = PluginRegistry()
        assert isinstance(registry.data_sources, dict)

    def test_visualizers_is_dict(self):
        registry = PluginRegistry()
        assert isinstance(registry.visualizers, dict)

    def test_get_data_source_nonexistent_returns_none(self):
        registry = PluginRegistry()
        result = registry.get_data_source("nonexistent_plugin_xyz")
        assert result is None

    def test_get_visualizer_nonexistent_returns_none(self):
        registry = PluginRegistry()
        result = registry.get_visualizer("nonexistent_visualizer_xyz")
        assert result is None

    def test_get_data_source_json_when_installed(self):
        """When json-datasource is installed, get_data_source('json') returns plugin."""
        registry = PluginRegistry()
        result = registry.get_data_source("json")
        if result is not None:
            assert result.name == "JSON Data Source"

    def test_get_visualizer_simple_when_installed(self):
        """When simple-visualizer is installed, get_visualizer('simple') returns plugin."""
        registry = PluginRegistry()
        result = registry.get_visualizer("simple")
        if result is not None:
            assert "Simple" in result.name
