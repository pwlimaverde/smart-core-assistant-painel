from __future__ import annotations

from django.urls import path

from . import views

app_name: str = "appflowy_adapter"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("workspaces/", views.workspaces, name="workspaces"),
    path("grids/<uuid:grid_id>/schema/", views.grid_schema, name="grid-schema"),
    path(
        "grids/<uuid:grid_id>/rows/",
        views.rows_list_or_create,
        name="rows-list-create",
    ),
    path(
        "grids/<uuid:grid_id>/rows/<uuid:row_id>/",
        views.row_update_or_delete,
        name="row-update-delete",
    ),
]