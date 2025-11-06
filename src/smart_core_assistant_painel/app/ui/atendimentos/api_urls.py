"""URLs de API pública para Atendimentos."""

from __future__ import annotations

from django.urls import path

from .views_api import (
    kanban_departamento_public,
    atendimento_detalhe_public,
    mensagens_list_public,
)

app_name: str = "atendimentos_api"

urlpatterns = [
    path(
        "kanban/<slug:departamento_slug>/",
        kanban_departamento_public,
        name="kanban-departamento",
    ),
    path(
        "<int:atendimento_id>/",
        atendimento_detalhe_public,
        name="atendimento-detalhe",
    ),
    path(
        "<int:atendimento_id>/mensagens/",
        mensagens_list_public,
        name="mensagens-list",
    ),
]
