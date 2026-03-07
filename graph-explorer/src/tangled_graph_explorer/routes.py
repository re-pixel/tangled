"""
Main view routes for the web application.
"""

from flask import Blueprint, render_template, current_app, redirect, url_for

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home page - list workspaces and available plugins."""
    platform = current_app.config["PLATFORM"]
    return render_template(
        "index.html",
        data_sources=platform.data_sources,
        visualizers=platform.visualizers,
        workspaces=platform.workspaces,
    )


@main_bp.route("/workspace/<workspace_id>")
def workspace(workspace_id: str):
    """
    Workspace view - main visualization interface.
    
    Shows Main View, Tree View, Bird View, search/filter controls, and CLI.
    """
    platform = current_app.config["PLATFORM"]
    ws = platform.get_workspace(workspace_id)
    
    if ws is None:
        return redirect(url_for("main.index"))
    
    return render_template(
        "workspace.html",
        workspace=ws,
        visualizers=platform.visualizers,
    )


@main_bp.route("/workspace/new")
def new_workspace():
    """Create a new workspace and redirect to it."""
    platform = current_app.config["PLATFORM"]
    ws = platform.create_workspace()
    return redirect(url_for("main.workspace", workspace_id=ws.id))
