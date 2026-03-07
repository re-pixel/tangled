"""
Core platform functionality.

The Platform class is the main entry point for using Tangled.
"""

from typing import Dict, Optional
import uuid

from tangled_platform.registry import PluginRegistry
from tangled_platform.workspace import Workspace


class Platform:
    """
    Main platform class - orchestrates plugins and workspaces.
    
    Usage:
        platform = Platform()
        workspace = platform.create_workspace()
        workspace.load_data(platform.get_data_source("json"), file_path="data.json")
        html = workspace.render(platform.get_visualizer("simple"))
    """
    
    def __init__(self):
        self._registry = PluginRegistry()
        self._workspaces: Dict[str, Workspace] = {}
    
    @property
    def data_sources(self) -> Dict[str, any]:
        """All available data source plugins."""
        return self._registry.data_sources
    
    @property
    def visualizers(self) -> Dict[str, any]:
        """All available visualizer plugins."""
        return self._registry.visualizers
    
    def get_data_source(self, name: str):
        """Get a data source plugin by name."""
        return self._registry.get_data_source(name)
    
    def get_visualizer(self, name: str):
        """Get a visualizer plugin by name."""
        return self._registry.get_visualizer(name)
    
    def create_workspace(self, workspace_id: Optional[str] = None) -> Workspace:
        """
        Create a new workspace.
        
        Args:
            workspace_id: Optional ID for the workspace. Auto-generated if not provided.
            
        Returns:
            A new Workspace instance
        """
        if workspace_id is None:
            workspace_id = str(uuid.uuid4())
        
        workspace = Workspace(workspace_id)
        self._workspaces[workspace_id] = workspace
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get an existing workspace by ID."""
        return self._workspaces.get(workspace_id)
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace. Returns True if deleted, False if not found."""
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            return True
        return False
    
    @property
    def workspaces(self) -> Dict[str, Workspace]:
        """All active workspaces."""
        return self._workspaces
