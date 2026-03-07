"""
REST API endpoints for graph operations.

Thin Flask wrappers around tangled_web.services.
"""

from flask import Blueprint, request, jsonify, current_app
from tangled_web import services
from tangled_web.services import WorkspaceNotFound

api_bp = Blueprint("api", __name__)


def _platform():
    return current_app.config["PLATFORM"]


def _handle_not_found(func):
    """Decorator that converts WorkspaceNotFound into a 404 JSON response."""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WorkspaceNotFound:
            return jsonify({"error": "Workspace not found"}), 404

    return wrapper


@api_bp.route("/plugins/datasources", methods=["GET"])
def list_data_sources():
    data, status = services.list_data_sources(_platform())
    return jsonify(data), status


@api_bp.route("/plugins/visualizers", methods=["GET"])
def list_visualizers():
    data, status = services.list_visualizers(_platform())
    return jsonify(data), status


@api_bp.route("/workspace/<workspace_id>/load", methods=["POST"])
@_handle_not_found
def load_data(workspace_id: str):
    body = request.get_json()
    data, status = services.load_data(
        _platform(), workspace_id,
        plugin_name=body.get("plugin"),
        params=body.get("params", {}),
    )
    return jsonify(data), status


@api_bp.route("/workspace/<workspace_id>/render", methods=["GET"])
@_handle_not_found
def render_graph(workspace_id: str):
    data, status = services.render_graph(
        _platform(), workspace_id,
        visualizer_name=request.args.get("visualizer", "simple"),
    )
    return jsonify(data), status


@api_bp.route("/workspace/<workspace_id>/filter", methods=["POST"])
@_handle_not_found
def filter_graph(workspace_id: str):
    body = request.get_json()
    data, status = services.filter_graph(
        _platform(), workspace_id,
        query=body.get("query", ""),
    )
    return jsonify(data), status


@api_bp.route("/workspace/<workspace_id>/search", methods=["POST"])
@_handle_not_found
def search_graph(workspace_id: str):
    body = request.get_json()
    data, status = services.search_graph(
        _platform(), workspace_id,
        query=body.get("query", ""),
    )
    return jsonify(data), status


@api_bp.route("/workspace/<workspace_id>/reset", methods=["POST"])
@_handle_not_found
def reset_graph(workspace_id: str):
    data, status = services.reset_graph(_platform(), workspace_id)
    return jsonify(data), status


@api_bp.route("/workspace/<workspace_id>/cli", methods=["POST"])
@_handle_not_found
def execute_cli(workspace_id: str):
    body = request.get_json()
    data, status = services.execute_cli(
        _platform(), workspace_id,
        command=body.get("command", "").strip(),
    )
    return jsonify(data), status


@api_bp.route("/workspace/<workspace_id>/graph", methods=["GET"])
@_handle_not_found
def get_graph_data(workspace_id: str):
    data, status = services.get_graph_data(_platform(), workspace_id)
    return jsonify(data), status
