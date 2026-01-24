"""
Abstract base classes defining the plugin interfaces.

All plugins must implement these interfaces to integrate with the platform.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from tangled_api.model import Graph


class PluginParameter:
    """
    Describes a required input parameter for a plugin.
    
    Used by the platform to dynamically build UI for plugin configuration.
    """
    
    def __init__(
        self,
        name: str,
        param_type: Type,
        description: str = "",
        required: bool = True,
        default: Any = None,
    ):
        self.name = name
        self.param_type = param_type
        self.description = description
        self.required = required
        self.default = default


class DataSourcePlugin(ABC):
    """
    Abstract base class for data source plugins.
    
    A data source plugin parses a specific data format (JSON, XML, etc.)
    and constructs a Graph from it.
    
    Implementations must:
    - Define required parameters (e.g., file_path, api_url)
    - Parse the data source and return a Graph instance
    - Support cyclic graph structures where applicable
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the plugin."""
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what data this plugin can parse."""
        ...
    
    @property
    @abstractmethod
    def parameters(self) -> List[PluginParameter]:
        """
        List of parameters required by this plugin.
        
        The platform will prompt the user for these values.
        """
        ...
    
    @abstractmethod
    def load(self, **params: Any) -> Graph:
        """
        Parse the data source and construct a graph.
        
        Args:
            **params: Parameter values as defined by `parameters`
            
        Returns:
            A Graph instance representing the parsed data
            
        Raises:
            ValueError: If parameters are invalid
            ParseError: If data cannot be parsed
        """
        ...


class VisualizerPlugin(ABC):
    """
    Abstract base class for visualizer plugins.
    
    A visualizer plugin takes a Graph and generates an HTML string
    representation for display in the web application.
    
    The generated HTML should include all necessary structure for
    the visualization but rely on platform-provided CSS/JS for
    interactivity (pan, zoom, drag-drop, etc.).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the plugin."""
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the visualization style."""
        ...
    
    @abstractmethod
    def render(self, graph: Graph) -> str:
        """
        Generate HTML representation of the graph.
        
        Args:
            graph: The Graph to visualize
            
        Returns:
            HTML string to be embedded in the web page
        """
        ...
