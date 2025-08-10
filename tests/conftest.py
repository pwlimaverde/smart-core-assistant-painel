"""Configuração global para testes pytest com Django."""

import os
import sys
import django
from pathlib import Path


def pytest_configure() -> None:
    """Configura o Django para os testes."""
    # Garante que a raiz do projeto e o diretório src estejam no sys.path
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    ui_dir = src_dir / "smart_core_assistant_painel" / "app" / "ui"
    for p in (str(repo_root), str(src_dir), str(ui_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)

    # Força o DJANGO_SETTINGS_MODULE para o caminho absoluto do settings
    os.environ["DJANGO_SETTINGS_MODULE"] = (
        "smart_core_assistant_painel.app.ui.core.settings"
    )

    django.setup()