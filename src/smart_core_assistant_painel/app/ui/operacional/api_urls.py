"""URLs de API pública para Operacional."""

from __future__ import annotations

from django.urls import path

from .views_api import (
    departamentos_public,
    fluxo_departamento_public,
)

app_name: str = "operacional_api"

urlpatterns = [
    path("departamentos/", departamentos_public, name="departamentos"),
    path(
        "departamentos/<slug:departamento_slug>/fluxo/",
        fluxo_departamento_public,
        name="fluxo-departamento",
    ),
]
