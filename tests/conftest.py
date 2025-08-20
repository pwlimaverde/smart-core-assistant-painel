"""Configuração global para testes pytest com Django."""

import os
import sys
from pathlib import Path
import django
from typing import Any

# Ensure the src directory is in the path
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Set the Django settings module
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings_test"
)

# Initialize Django
django.setup()

# Configure pytest-django
import pytest

@pytest.fixture(scope='session')
def django_db_setup():
    pass  # Use the settings from settings_test.py