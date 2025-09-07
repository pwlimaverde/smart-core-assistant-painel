"""Signals para o aplicativo Atendimentos."""

from datetime import timedelta
from typing import Any

from django.dispatch import Signal, receiver
from django.utils import timezone
from django_q.models import Schedule
from loguru import logger

from smart_core_assistant_painel.modules.services import SERVICEHUB

mensagem_bufferizada = Signal()


@receiver(mensagem_bufferizada)
def signal_agendar_processamento_mensagens(
    sender: Any, phone: str, **kwargs: Any
) -> None:
    """Agenda o processamento de mensagens em buffer."""
    try:
        schedule_name = f"process_msg_{phone}"
        next_run = timezone.now() + timedelta(seconds=SERVICEHUB.TIME_CACHE)
        __limpar_schedules_telefone(phone)
        Schedule.objects.create(
            name=schedule_name,
            func="smart_core_assistant_painel.app.ui.atendimentos.utils.send_message_response",
            args=phone,
            schedule_type=Schedule.ONCE,
            next_run=next_run,
        )
    except Exception as e:
        logger.error(
            f"Erro ao agendar processamento para {phone}: {e}", exc_info=True
        )


def __limpar_schedules_telefone(phone: str) -> None:
    """Remove agendamentos pendentes para um telefone específico."""
    try:
        schedule_name = f"process_msg_{phone}"
        Schedule.objects.filter(
            name=schedule_name, next_run__gt=timezone.now()
        ).delete()
    except Exception as e:
        logger.warning(f"Erro ao limpar schedules para {phone}: {e}")
