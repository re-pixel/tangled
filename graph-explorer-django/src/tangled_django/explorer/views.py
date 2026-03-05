"""
Page views for the Django graph explorer.
"""

from django.shortcuts import render, redirect
from django.urls import reverse

import tangled_django.explorer as mod


def index(request):
    """Home page - list workspaces and available plugins."""
    platform = mod.platform
    return render(request, "explorer/index.html", {
        "data_sources": platform.data_sources,
        "visualizers": platform.visualizers,
        "workspaces": platform.workspaces,
    })


def workspace(request, workspace_id):
    """Workspace view - main visualization interface."""
    platform = mod.platform
    ws = platform.get_workspace(workspace_id)

    if ws is None:
        return redirect(reverse("index"))

    return render(request, "explorer/workspace.html", {
        "workspace": ws,
        "visualizers": platform.visualizers,
    })


def new_workspace(request):
    """Create a new workspace and redirect to it."""
    platform = mod.platform
    ws = platform.create_workspace()
    return redirect(reverse("workspace", kwargs={"workspace_id": ws.id}))
