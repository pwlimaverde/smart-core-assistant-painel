"""
Core app para Smart Core Assistant.
Inicializa Celery quando Django carrega.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
