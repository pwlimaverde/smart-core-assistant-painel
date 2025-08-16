"""Configuração para testes do app Oraculo."""

import os
import django


def pytest_configure() -> None:
    """Configura o Django para os testes do app Oraculo.

    Utiliza o caminho absoluto do módulo de settings para evitar
    erros de import (ex.: ModuleNotFoundError: core) quando os
    testes são executados em ambientes diferentes (local/Docker).
    """
    os.environ["DJANGO_SETTINGS_MODULE"] = (
        "smart_core_assistant_painel.app.ui.core.settings_test"
    )
    django.setup()
