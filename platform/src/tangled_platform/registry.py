"""
Plugin discovery and registration.

Uses entry points to discover installed plugins automatically.
"""

from typing import Dict, List, Type, Optional
import importlib.metadata

from tangled_api.plugins import DataSourcePlugin, VisualizerPlugin


class PluginRegistry:
    """
    Discovers and manages installed plugins.
    
    Plugins register themselves via entry points:
    - tangled.datasource: Data source plugins
    - tangled.visualizer: Visualizer plugins
    """
    
    def __init__(self):
        self._data_sources: Dict[str, DataSourcePlugin] = {}
        self._visualizers: Dict[str, VisualizerPlugin] = {}
        self._discover_plugins()
    
    def _discover_plugins(self) -> None:
        """Discover installed plugins via entry points."""
        # Discover data source plugins
        for ep in importlib.metadata.entry_points(group="tangled.datasource"):
            try:
                plugin_class = ep.load()
                plugin = plugin_class()
                self._data_sources[ep.name] = plugin
            except Exception as e:
                # TODO: Log warning about failed plugin load
                pass
        
        # Discover visualizer plugins
        for ep in importlib.metadata.entry_points(group="tangled.visualizer"):
            try:
                plugin_class = ep.load()
                plugin = plugin_class()
                self._visualizers[ep.name] = plugin
            except Exception as e:
                # TODO: Log warning about failed plugin load
                pass
    
    @property
    def data_sources(self) -> Dict[str, DataSourcePlugin]:
        """All registered data source plugins."""
        return self._data_sources
    
    @property
    def visualizers(self) -> Dict[str, VisualizerPlugin]:
        """All registered visualizer plugins."""
        return self._visualizers
    
    def get_data_source(self, name: str) -> Optional[DataSourcePlugin]:
        """Get a data source plugin by name."""
        return self._data_sources.get(name)
    
    def get_visualizer(self, name: str) -> Optional[VisualizerPlugin]:
        """Get a visualizer plugin by name."""
        return self._visualizers.get(name)
