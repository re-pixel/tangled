from django.urls import path

from tangled_django.explorer import views, api_views

urlpatterns = [
    # Page views
    path("", views.index, name="index"),
    path("workspace/new", views.new_workspace, name="new_workspace"),
    path("workspace/<str:workspace_id>", views.workspace, name="workspace"),

    # API endpoints
    path("api/plugins/datasources", api_views.list_data_sources, name="api_datasources"),
    path("api/plugins/visualizers", api_views.list_visualizers, name="api_visualizers"),
    path("api/workspace/<str:workspace_id>/load", api_views.load_data, name="api_load"),
    path("api/workspace/<str:workspace_id>/render", api_views.render_graph, name="api_render"),
    path("api/workspace/<str:workspace_id>/filter", api_views.filter_graph, name="api_filter"),
    path("api/workspace/<str:workspace_id>/search", api_views.search_graph, name="api_search"),
    path("api/workspace/<str:workspace_id>/reset", api_views.reset_graph, name="api_reset"),
    path("api/workspace/<str:workspace_id>/cli", api_views.execute_cli, name="api_cli"),
    path("api/workspace/<str:workspace_id>/graph", api_views.get_graph_data, name="api_graph"),
]
