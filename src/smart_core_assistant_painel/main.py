"""Ponto de entrada principal da aplicação.

Este script inicializa os serviços necessários e, em seguida, inicia a aplicação Django.
"""
import os
from pathlib import Path

from smart_core_assistant_painel.app.ui.manage import start_app
from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import (
    start_initial_loading,
)
from smart_core_assistant_painel.modules.services.start_services import start_services


def _resolve_firebase_credentials_path() -> None:
    """Resolve o caminho para o arquivo de credenciais do Firebase.

    Verifica a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS e, se ela
    contiver um caminho relativo, o converte para um caminho absoluto baseado
    na raiz do projeto.
    """
    credentials_path_str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path_str:
        print("Aviso: GOOGLE_APPLICATION_CREDENTIALS não está definida.")
        return

    credentials_path = Path(credentials_path_str)
    if not credentials_path.is_absolute():
        # O __file__ aponta para src/smart_core_assistant_painel/main.py
        # A raiz do projeto está 3 níveis acima.
        project_root = Path(__file__).resolve().parents[3]
        absolute_path = project_root / credentials_path

        if absolute_path.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(absolute_path)
            print(
                "Caminho do GOOGLE_APPLICATION_CREDENTIALS resolvido para: "
                f"{absolute_path}"
            )
        else:
            print(
                "Aviso: O arquivo de credenciais não foi encontrado em: "
                f"{absolute_path}"
            )


def main() -> None:
    """Ponto de entrada principal."""
    _resolve_firebase_credentials_path()
    print("Iniciando serviços e configurações iniciais...")
    start_initial_loading()
    start_services()
    print("Serviços iniciados com sucesso.")

    print("Iniciando a aplicação Django...")
    start_app()


if __name__ == "__main__":
    main()
