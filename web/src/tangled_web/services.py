"""
Framework-agnostic service functions for the graph explorer.

Each function accepts a Platform (and request parameters) and returns
``(response_dict, status_code)``.  The web layer (Flask / Django) converts
these into framework-specific responses.
"""

from __future__ import annotations

from tangled_web.cli import CLI
from tangled_web.serializers import serialize_graph


class WorkspaceNotFound(Exception):
    """Raised when a workspace ID does not exist."""


# ── helpers ──────────────────────────────────────────────────────────────

def _get_workspace(platform, workspace_id: str):
    ws = platform.get_workspace(workspace_id)
    if ws is None:
        raise WorkspaceNotFound(workspace_id)
    return ws


# ── service functions ────────────────────────────────────────────────────

def list_data_sources(platform) -> tuple[list, int]:
    sources = []
    for name, plugin in platform.data_sources.items():
        sources.append({
            "id": name,
            "name": plugin.name,
            "description": plugin.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type.__name__,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                }
                for p in plugin.parameters
            ],
        })
    return sources, 200


def list_visualizers(platform) -> tuple[list, int]:
    visualizers = []
    for name, plugin in platform.visualizers.items():
        visualizers.append({
            "id": name,
            "name": plugin.name,
            "description": plugin.description,
        })
    return visualizers, 200


def load_data(platform, workspace_id: str, plugin_name: str, params: dict) -> tuple[dict, int]:
    ws = _get_workspace(platform, workspace_id)

    plugin = platform.get_data_source(plugin_name)
    if plugin is None:
        return {"error": f"Plugin '{plugin_name}' not found"}, 404

    try:
        ws.load_data(plugin, **params)
        ws._cli_cleared = False
        return {"success": True, "node_count": len(ws.graph.nodes)}, 200
    except Exception as e:
        return {"error": str(e)}, 400


def render_graph(platform, workspace_id: str, visualizer_name: str = "simple") -> tuple[dict, int]:
    ws = _get_workspace(platform, workspace_id)

    visualizer = platform.get_visualizer(visualizer_name)
    if visualizer is None:
        return {"error": f"Visualizer '{visualizer_name}' not found"}, 404

    html = ws.render(visualizer)
    return {"html": html}, 200


def filter_graph(platform, workspace_id: str, query: str) -> tuple[dict, int]:
    ws = _get_workspace(platform, workspace_id)

    try:
        ws.filter(query)
        return {"success": True, "node_count": len(ws.graph.nodes)}, 200
    except Exception as e:
        return {"error": str(e)}, 400


def search_graph(platform, workspace_id: str, query: str) -> tuple[dict, int]:
    ws = _get_workspace(platform, workspace_id)

    try:
        ws.search(query)
        return {"success": True, "node_count": len(ws.graph.nodes)}, 200
    except Exception as e:
        return {"error": str(e)}, 400


def reset_graph(platform, workspace_id: str) -> tuple[dict, int]:
    ws = _get_workspace(platform, workspace_id)
    ws.reset()
    ws._cli_cleared = False
    return {"success": True}, 200


def execute_cli(platform, workspace_id: str, command: str) -> tuple[dict, int]:
    ws = _get_workspace(platform, workspace_id)

    if not command:
        return {"error": "No command provided"}, 400

    cli = CLI(ws)
    result = cli.execute(command)

    if result.error:
        return {"error": result.error}, 400

    return {"result": result.output, "changed": result.changed}, 200


def get_graph_data(platform, workspace_id: str) -> tuple[dict, int]:
    ws = _get_workspace(platform, workspace_id)
    return serialize_graph(ws.graph), 200
