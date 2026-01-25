"""
Tangled Graph Explorer - Flask web application.

This is the main entry point for the web application.
"""

__version__ = "0.1.0"

from tangled_graph_explorer.app import create_app

__all__ = ["create_app"]
