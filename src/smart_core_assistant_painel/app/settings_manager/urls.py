"""Configuração de URLs para o módulo de configurações."""

from django.urls import path

from . import views

app_name = "configuracoes"

urlpatterns = [
    path(
        "",
        views.configuracoes_index,
        name="index",
    ),
    path(
        "whitelist/",
        views.configuracoes_whitelist,
        name="whitelist",
    ),
    path(
        "whitelist/adicionar/",
        views.whitelist_adicionar,
        name="whitelist_adicionar",
    ),
    path(
        "whitelist/<int:pk>/editar/",
        views.whitelist_editar,
        name="whitelist_editar",
    ),
    path(
        "whitelist/<int:pk>/excluir/",
        views.whitelist_excluir,
        name="whitelist_excluir",
    ),
    path(
        "whitelist/<int:pk>/toggle/",
        views.whitelist_toggle,
        name="whitelist_toggle",
    ),
]
