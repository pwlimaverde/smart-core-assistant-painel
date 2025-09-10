"""Configuração de URLs para o aplicativo Treinamento."""

from django.urls import path

from . import views

app_name = "treinamento"

urlpatterns = [
    path("treinar_ia", views.treinar_ia, name="treinar_ia"),
    path(
        "pre-processamento/<int:id>/",
        views.pre_processamento,
        name="pre_processamento",
    ),
    path(
        "verificar_treinamentos/",
        views.verificar_treinamentos_vetorizados,
        name="verificar_treinamentos_vetorizados",
    ),
    path(
        "cadastrar_query_compose",
        views.cadastrar_query_compose,
        name="cadastrar_query_compose",
    ),
]