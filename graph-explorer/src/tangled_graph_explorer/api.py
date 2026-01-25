"""
REST API endpoints for graph operations.

All graph manipulation (search, filter, CRUD, CLI) happens through these endpoints.
Frontend JavaScript calls these APIs and updates the views accordingly.
"""

from flask import Blueprint, request, jsonify, current_app

api_bp = Blueprint("api", __name__)


@api_bp.route("/plugins/datasources", methods=["GET"])
def list_data_sources():
    """List all available data source plugins."""
    platform = current_app.config["PLATFORM"]
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
    return jsonify(sources)


@api_bp.route("/plugins/visualizers", methods=["GET"])
def list_visualizers():
    """List all available visualizer plugins."""
    platform = current_app.config["PLATFORM"]
    visualizers = []
    for name, plugin in platform.visualizers.items():
        visualizers.append({
            "id": name,
            "name": plugin.name,
            "description": plugin.description,
        })
    return jsonify(visualizers)


@api_bp.route("/workspace/<workspace_id>/load", methods=["POST"])
def load_data(workspace_id: str):
    """
    Load data into a workspace using a data source plugin.
    
    Request body:
    {
        "plugin": "json",
        "params": {"file_path": "/path/to/file.json"}
    }
    """
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return jsonify({"error": "Workspace not found"}), 404
    
    data = request.get_json()
    plugin_name = data.get("plugin")
    params = data.get("params", {})
    
    plugin = platform.get_data_source(plugin_name)
    if plugin is None:
        return jsonify({"error": f"Plugin '{plugin_name}' not found"}), 404
    
    try:
        ws.load_data(plugin, **params)
        return jsonify({"success": True, "node_count": len(ws.graph.nodes)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/workspace/<workspace_id>/render", methods=["GET"])
def render_graph(workspace_id: str):
    """
    Render the current graph using a visualizer plugin.
    
    Query params:
    - visualizer: Plugin name (default: "simple")
    """
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return jsonify({"error": "Workspace not found"}), 404
    
    visualizer_name = request.args.get("visualizer", "simple")
    visualizer = platform.get_visualizer(visualizer_name)
    
    if visualizer is None:
        return jsonify({"error": f"Visualizer '{visualizer_name}' not found"}), 404
    
    html = ws.render(visualizer)
    return jsonify({"html": html})


@api_bp.route("/workspace/<workspace_id>/filter", methods=["POST"])
def filter_graph(workspace_id: str):
    """
    Apply a filter to the current graph.
    
    Request body:
    {
        "query": "age > 25"
    }
    """
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return jsonify({"error": "Workspace not found"}), 404
    
    data = request.get_json()
    query = data.get("query", "")
    
    try:
        ws.filter(query)
        return jsonify({"success": True, "node_count": len(ws.graph.nodes)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/workspace/<workspace_id>/search", methods=["POST"])
def search_graph(workspace_id: str):
    """
    Apply a search to the current graph.
    
    Request body:
    {
        "query": "John"
    }
    """
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return jsonify({"error": "Workspace not found"}), 404
    
    data = request.get_json()
    query = data.get("query", "")
    
    try:
        ws.search(query)
        return jsonify({"success": True, "node_count": len(ws.graph.nodes)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/workspace/<workspace_id>/reset", methods=["POST"])
def reset_graph(workspace_id: str):
    """Reset workspace to original graph (clear all filters/searches)."""
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return jsonify({"error": "Workspace not found"}), 404
    
    ws.reset()
    return jsonify({"success": True})


@api_bp.route("/workspace/<workspace_id>/cli", methods=["POST"])
def execute_cli(workspace_id: str):
    """
    Execute a CLI command on the workspace graph.
    
    Request body:
    {
        "command": "create node --id=1 --property Name=Alice"
    }
    """
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return jsonify({"error": "Workspace not found"}), 404
    
    data = request.get_json()
    command = data.get("command", "")
    
    # TODO: Implement CLI execution
    # from tangled_platform.cli import CLI
    # cli = CLI(ws.graph)
    # result = cli.execute(command)
    
    return jsonify({"error": "CLI not yet implemented"}), 501


@api_bp.route("/workspace/<workspace_id>/graph", methods=["GET"])
def get_graph_data(workspace_id: str):
    """
    Get raw graph data for Tree View and other uses.
    
    Returns nodes and edges as JSON.
    """
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return jsonify({"error": "Workspace not found"}), 404
    
    if ws.graph is None:
        return jsonify({"nodes": [], "edges": []})
    
    nodes = []
    for node_id, node in ws.graph.nodes.items():
        nodes.append({
            "id": node_id,
            "attributes": {k: str(v) for k, v in node.attributes.items()},
        })
    
    edges = []
    for edge_id, edge in ws.graph.edges.items():
        edges.append({
            "id": edge_id,
            "source": edge.source_id,
            "target": edge.target_id,
            "directed": edge.directed,
            "attributes": {k: str(v) for k, v in edge.attributes.items()},
        })
    
    return jsonify({"nodes": nodes, "edges": edges})
