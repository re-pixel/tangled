"""
Tangled Platform - Core orchestration for graph visualization.

This package provides:
- Plugin discovery and management
- Workspace management (multiple graphs, filters, searches)
- Search and filter operations on graphs
- CLI for graph manipulation
"""

__version__ = "0.1.0"

from tangled_platform.core import Platform
from tangled_platform.workspace import Workspace
from tangled_platform.registry import PluginRegistry

__all__ = [
    "Platform",
    "Workspace",
    "PluginRegistry",
]
