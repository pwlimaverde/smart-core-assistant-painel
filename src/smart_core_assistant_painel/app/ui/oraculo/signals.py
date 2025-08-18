"""Signals para o aplicativo Oráculo.

Este módulo define os signals e receivers para lidar com eventos assíncronos,
como o treinamento da IA após salvar um treinamento e o agendamento do
processamento de mensagens em buffer.
"""

from datetime import timedelta
from typing import Any

from django.db.models.signals import post_save, pre_delete
from django.dispatch import Signal, receiver
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import async_task
from loguru import logger

from smart_core_assistant_painel.modules.services import SERVICEHUB

from .models import Treinamentos

mensagem_bufferizada = Signal()


@receiver(post_save, sender=Treinamentos)
def signals_treinamento_ia(
    sender: Any, instance: Treinamentos, created: bool, **kwargs: Any
) -> None:
    """Executa o treinamento da IA de forma assíncrona após salvar um treinamento.

    Args:
        sender (Any): O remetente do signal.
        instance (Treinamentos): A instância do modelo de treinamento.
        created (bool): True se um novo registro foi criado.
        **kwargs (Any): Argumentos de palavra-chave adicionais.
    """
    try:
        if instance.treinamento_finalizado:
            async_task(__task_treinar_ia, instance.id)
    except Exception as e:
        logger.error(f"Erro ao processar signal de treinamento: {e}")


@receiver(mensagem_bufferizada)
def signal_agendar_processamento_mensagens(
    sender: Any, phone: str, **kwargs: Any
) -> None:
    """Agenda o processamento de mensagens em buffer.

    Args:
        sender (Any): O remetente do signal.
        phone (str): O número de telefone para o qual agendar o processamento.
        **kwargs (Any): Argumentos de palavra-chave adicionais.
    """
    try:
        schedule_name = f"process_msg_{phone}"
        next_run = timezone.now() + timedelta(seconds=SERVICEHUB.TIME_CACHE)
        __limpar_schedules_telefone(phone)
        Schedule.objects.create(
            name=schedule_name,
            func="smart_core_assistant_painel.app.ui.oraculo.utils.send_message_response",
            args=phone,
            schedule_type=Schedule.ONCE,
            next_run=next_run,
        )
    except Exception as e:
        logger.error(f"Erro ao agendar processamento para {phone}: {e}", exc_info=True)


def __limpar_schedules_telefone(phone: str) -> None:
    """Remove agendamentos pendentes para um telefone específico.

    Args:
        phone (str): O número de telefone.
    """
    try:
        schedule_name = f"process_msg_{phone}"
        Schedule.objects.filter(
            name=schedule_name, next_run__gt=timezone.now()
        ).delete()
    except Exception as e:
        logger.warning(f"Erro ao limpar schedules para {phone}: {e}")


def __task_treinar_ia(instance_id: int) -> None:
    """Tarefa para treinar a IA com os documentos de um treinamento.

    Args:
        instance_id (int): O ID da instância de Treinamento.
    """
    try:
        instance = Treinamentos.objects.get(id=instance_id)
        SERVICEHUB.vetor_storage.remove_by_metadata("id_treinamento", str(instance_id))
        documentos = instance.get_documentos()
        if documentos:
            SERVICEHUB.vetor_storage.write(documentos)
    except Treinamentos.DoesNotExist:
        logger.error(f"Treinamento com ID {instance_id} não encontrado.")
    except Exception as e:
        logger.error(f"Erro ao executar treinamento {instance_id}: {e}")


@receiver(pre_delete, sender=Treinamentos)
def signal_remover_treinamento_ia(
    sender: Any, instance: Treinamentos, **kwargs: Any
) -> None:
    """Remove os dados de treinamento do banco vetorial antes de deletar.

    Args:
        sender (Any): O remetente do signal.
        instance (Treinamentos): A instância do modelo de treinamento.
        **kwargs (Any): Argumentos de palavra-chave adicionais.

    Raises:
        Exception: Se a remoção do banco vetorial falhar.
    """
    try:
        if instance.treinamento_finalizado:
            __task_remover_treinamento_ia(instance.id)
    except Exception as e:
        logger.error(f"Erro ao processar remoção de treinamento: {e}")
        raise Exception(f"Falha ao remover treinamento {instance.id}: {e}")


def __task_remover_treinamento_ia(instance_id: int) -> None:
    """Tarefa para remover um treinamento do banco vetorial.

    Args:
        instance_id (int): O ID da instância de Treinamento.

    Raises:
        Exception: Se ocorrer um erro durante a remoção.
    """
    try:
        SERVICEHUB.vetor_storage.remove_by_metadata("id_treinamento", str(instance_id))
    except Exception as e:
        logger.error(f"Erro ao remover treinamento {instance_id}: {e}")
        raise
