"""URLs HTML do Workspace de Atendimento Unificado."""

from __future__ import annotations

from django.urls import include, path

from . import views, views_sse

app_name = "atendimento_unificado"

urlpatterns = [
    path("", views.WorkspaceView.as_view(), name="workspace"),
    path(
        "api/",
        include(
            (
                "smart_core_assistant_painel.app.atendimento_unificado."
                "api_urls",
                "atendimento_unificado_api",
            )
        ),
    ),
    path("events/", views_sse.workspace_events, name="workspace_events"),
]
