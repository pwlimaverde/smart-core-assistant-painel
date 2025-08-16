"""Configuração global para testes pytest com Django."""

import os
import sys
import django
from pathlib import Path


def pytest_configure() -> None:
    """Configura o Django para os testes.

    - Garante que a raiz do projeto e o diretório src estejam no sys.path.
    - Respeita DJANGO_SETTINGS_MODULE se já estiver definido (pytest.ini/ambiente).
    - Usa settings_test como padrão para alinhar com execução no Docker.
    """
    # Garante que a raiz do projeto e o diretório src estejam no sys.path
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    ui_dir = src_dir / "smart_core_assistant_painel" / "app" / "ui"
    for p in (str(repo_root), str(src_dir), str(ui_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)

    # Define o DJANGO_SETTINGS_MODULE respeitando o que já vier do ambiente
    settings_module = os.environ.get(
        "DJANGO_SETTINGS_MODULE",
        "smart_core_assistant_painel.app.ui.core.settings_test",
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    django.setup()