from datetime import timedelta
from typing import Any

from django.db.models.signals import post_save, pre_delete
from django.dispatch import Signal, receiver
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import async_task
from loguru import logger

from smart_core_assistant_painel.modules.services.features.service_hub import (
    SERVICEHUB,
)

from .models import Treinamentos

# Signal customizado para notificar sobre mensagens bufferizadas
mensagem_bufferizada = Signal()


@receiver(post_save, sender=Treinamentos)
def signals_treinamento_ia(
    sender: Any, instance: Treinamentos, created: bool, **kwargs: Any
) -> None:
    """
    Signal executado após salvar um treinamento.
    Executa o treinamento da IA de forma assíncrona se o treinamento foi
    finalizado.
    """
    try:
        if instance.treinamento_finalizado:
            async_task(__task_treinar_ia, instance.id)
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de treinamento para instância {instance.id}: {e}"
        )


@receiver(mensagem_bufferizada)
def signal_agendar_processamento_mensagens(
    sender: Any, phone: str, **kwargs: Any
) -> None:
    """
    Signal receiver para agendar processamento de mensagens no cluster.

    Cria uma Schedule do Django Q do tipo ONCE para execução futura da função
    send_message_response, respeitando o tempo de debounce configurado.

    Args:
        sender: Remetente do signal (padrão "oraculo")
        phone: Número do telefone para processamento
        **kwargs: Argumentos adicionais do signal
    """
    try:
        schedule_name = f"process_msg_{phone}"
        current_time = timezone.now()
        delay_seconds = SERVICEHUB.TIME_CACHE
        next_run = current_time + timedelta(seconds=delay_seconds)

        # Remove agendamentos pendentes para o mesmo telefone
        # para evitar duplicação
        __limpar_schedules_telefone(phone)

        # Cria nova Schedule para execução futura
        Schedule.objects.create(
            name=schedule_name,
            func="smart_core_assistant_painel.app.ui.oraculo.utils.send_message_response",
            args=phone,  # Passa diretamente o telefone como string
            schedule_type=Schedule.ONCE,
            next_run=next_run,
            cluster=None,  # Permite execução em qualquer cluster
        )

    except Exception as e:
        logger.error(
            f"[SIGNAL] ❌ Erro ao agendar processamento para {phone}: {e}",
            exc_info=True,
        )


def __limpar_schedules_telefone(phone: str) -> None:
    """
    Remove schedules pendentes para um telefone específico.

    Args:
        phone: Número do telefone

    Returns:
        int: Número de schedules removidos
    """
    try:
        schedule_name = f"process_msg_{phone}"

        # Remove schedules pendentes (ainda não executadas)
        Schedule.objects.filter(
            name=schedule_name, next_run__gt=timezone.now()
        ).delete()

    except Exception as e:
        logger.warning(f"[SIGNAL] Erro ao limpar schedules para {phone}: {e}")


def __task_treinar_ia(instance_id: int) -> None:
    """
    Task para treinar a IA com documentos de um treinamento específico.

    Args:
        instance_id: ID da instância de Treinamento
    """
    instance = Treinamentos.objects.get(id=instance_id)

    try:
        # Remove dados antigos do treinamento antes de adicionar novos
        SERVICEHUB.vetor_storage.remove_by_metadata("id_treinamento", str(instance_id))

        # Processa documentos
        documentos = instance.get_documentos()
        if not documentos:
            logger.warning(
                f"Nenhum documento encontrado para o treinamento {instance_id}"
            )
            return

        # Cria ou atualiza banco vetorial
        SERVICEHUB.vetor_storage.write(documentos)

    except Exception as e:
        logger.error(f"Erro ao executar treinamento {instance_id}: {e}")
        instance.treinamento_finalizado = False


@receiver(pre_delete, sender=Treinamentos)
def signal_remover_treinamento_ia(
    sender: Any, instance: Treinamentos, **kwargs: Any
) -> None:
    """
    Signal executado antes de deletar um treinamento.
    Remove os dados do treinamento do banco vetorial FAISS.
    Se houver erro na remoção, interrompe a deleção do treinamento.
    """
    try:
        if instance.treinamento_finalizado:
            # Executa a remoção de forma síncrona para garantir que seja
            # concluída antes da deleção do objeto
            __task_remover_treinamento_ia(instance.id)

    except Exception as e:
        logger.error(
            "Erro ao processar remoção de treinamento para instância "
            f"{instance.id}: {e}"
        )
        # Interrompe a deleção levantando uma exceção
        raise Exception(
            "Falha ao remover treinamento {id} do banco vetorial. "
            "Deleção interrompida: {err}".format(id=instance.id, err=e)
        )


def __task_remover_treinamento_ia(instance_id: int) -> None:
    """
    Task para remover um treinamento específico do banco vetorial FAISS.

    Args:
        instance_id: ID da instância de Treinamento

    Raises:
        Exception: Se houver erro na remoção do banco vetorial
    """
    try:
        SERVICEHUB.vetor_storage.remove_by_metadata("id_treinamento", str(instance_id))

    except Exception as e:
        logger.error(
            f"Erro ao remover treinamento {instance_id} do banco vetorial: {e}"
        )
        # Propaga a exceção para interromper o processo de deleção
        raise
