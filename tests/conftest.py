"""Configuração global para testes pytest com Django."""

import os
import sys
import django
from pathlib import Path


def pytest_configure() -> None:
    """Configura o Django para os testes."""
    # Adiciona o diretório da aplicação Django ao PYTHONPATH
    project_root = Path(__file__).parent.parent
    django_app_path = project_root / "src" / "smart_core_assistant_painel" / "app" / "ui"
    
    if str(django_app_path) not in sys.path:
        sys.path.insert(0, str(django_app_path))
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()