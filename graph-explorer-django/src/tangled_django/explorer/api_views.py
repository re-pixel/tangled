"""
REST API views for the Django graph explorer.

Thin wrappers around tangled_web.services.
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from tangled_web import services
from tangled_web.services import WorkspaceNotFound

import tangled_django.explorer as mod


def _platform():
    return mod.platform


def _handle_not_found(func):
    """Decorator that converts WorkspaceNotFound into a 404 JSON response."""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WorkspaceNotFound:
            return JsonResponse({"error": "Workspace not found"}, status=404)

    return wrapper


@require_GET
def list_data_sources(request):
    data, status = services.list_data_sources(_platform())
    return JsonResponse(data, safe=False, status=status)


@require_GET
def list_visualizers(request):
    data, status = services.list_visualizers(_platform())
    return JsonResponse(data, safe=False, status=status)


@csrf_exempt
@require_POST
@_handle_not_found
def load_data(request, workspace_id):
    body = json.loads(request.body)
    data, status = services.load_data(
        _platform(), workspace_id,
        plugin_name=body.get("plugin"),
        params=body.get("params", {}),
    )
    return JsonResponse(data, status=status)


@require_GET
@_handle_not_found
def render_graph(request, workspace_id):
    data, status = services.render_graph(
        _platform(), workspace_id,
        visualizer_name=request.GET.get("visualizer", "simple"),
    )
    return JsonResponse(data, status=status)


@csrf_exempt
@require_POST
@_handle_not_found
def filter_graph(request, workspace_id):
    body = json.loads(request.body)
    data, status = services.filter_graph(
        _platform(), workspace_id,
        query=body.get("query", ""),
    )
    return JsonResponse(data, status=status)


@csrf_exempt
@require_POST
@_handle_not_found
def search_graph(request, workspace_id):
    body = json.loads(request.body)
    data, status = services.search_graph(
        _platform(), workspace_id,
        query=body.get("query", ""),
    )
    return JsonResponse(data, status=status)


@csrf_exempt
@require_POST
@_handle_not_found
def reset_graph(request, workspace_id):
    data, status = services.reset_graph(_platform(), workspace_id)
    return JsonResponse(data, status=status)


@csrf_exempt
@require_POST
@_handle_not_found
def execute_cli(request, workspace_id):
    body = json.loads(request.body)
    data, status = services.execute_cli(
        _platform(), workspace_id,
        command=body.get("command", "").strip(),
    )
    return JsonResponse(data, status=status)


@require_GET
@_handle_not_found
def get_graph_data(request, workspace_id):
    data, status = services.get_graph_data(_platform(), workspace_id)
    return JsonResponse(data, status=status)
