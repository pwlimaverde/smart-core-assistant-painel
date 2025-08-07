"""Configuração para testes do app Oraculo."""

import os
import django
from django.conf import settings
from django.test.utils import get_runner


def pytest_configure() -> None:
    """Configura o Django para os testes do app Oraculo."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
    django.setup()