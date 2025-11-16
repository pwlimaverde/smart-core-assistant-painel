from django.urls import path

from . import views

app_name = "atendimentos"

urlpatterns = [
    path(
        "kanban/<int:departamento_id>/",
        views.kanban_departamento,
        name="kanban_departamento",
    ),
    path(
        "kanban-public/<int:departamento_id>/",
        views.kanban_departamento_public,
        name="kanban_departamento_public",
    ),
]
