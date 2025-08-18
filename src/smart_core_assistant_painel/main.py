"""Ponto de entrada principal da aplicação.

Este script inicializa os serviços necessários e, em seguida, inicia a
aplicação Django.
"""
from smart_core_assistant_painel.app.ui.manage import start_app
from smart_core_assistant_painel.modules.initial_loading import (
    start_initial_loading,
)
from smart_core_assistant_painel.modules.services import start_services

if __name__ == "__main__":
    start_initial_loading()
    start_services()
    start_app()
