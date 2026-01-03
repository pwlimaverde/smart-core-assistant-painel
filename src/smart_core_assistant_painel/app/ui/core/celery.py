"""
Configuração do Celery para Smart Core Assistant.
Dimensionado para Hostinger KVM 2 (2 vCPU, 8GB RAM) com 10 tenants.
"""

import os

from celery import Celery
from django.conf import settings

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)

app = Celery("smart_core")

# Configurações via Django settings com prefixo CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-descoberta de tasks nos apps Django
app.autodiscover_tasks()

# Filas por Prioridade e Tipo de Workload
app.conf.task_queues = {
    "webhooks": {
        "exchange": "webhooks",
        "routing_key": "webhooks",
    },
    "ai_processing": {
        "exchange": "ai",
        "routing_key": "ai",
    },
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
}

# Roteamento automático de tasks
app.conf.task_routes = {
    # Webhooks - Prioridade máxima, baixa latência
    "evolution_sync.tasks.*": {"queue": "webhooks"},
    "trello_sync.tasks.process_webhook_*": {"queue": "webhooks"},
    # IA - Alto consumo de recursos
    "treinamento.tasks.*": {"queue": "ai_processing"},
    # Todo o resto
    "*": {"queue": "default"},
}
