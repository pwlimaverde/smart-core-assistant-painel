"""Configuração do aplicativo de usuários.

Este módulo define a configuração do aplicativo Django para o gerenciamento
de usuários.
"""
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Configuração para o aplicativo de usuários."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "smart_core_assistant_painel.app.ui.usuarios"
