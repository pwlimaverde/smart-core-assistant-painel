"""Signals para o aplicativo Oráculo.

Este módulo define os signals e receivers para lidar com eventos assíncronos,
como o treinamento da IA após salvar um treinamento e o agendamento do
processamento de mensagens em buffer.
"""

from datetime import timedelta
from typing import Any, List

from django.conf import settings
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
        logger.error(
            f"Erro ao agendar processamento para {phone}: {e}", exc_info=True
        )


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


# -------------------------
# Helpers de Embeddings
# -------------------------

def __get_embeddings_instance() -> Any:
    """Constrói a instância de embeddings conforme configuração do ServiceHub.

    Returns:
        Any: Instância de embeddings compatível com LangChain.

    Raises:
        ValueError: Caso a classe configurada não seja suportada.
    """
    embeddings_class: str = SERVICEHUB.EMBEDDINGS_CLASS
    embeddings_model: str = SERVICEHUB.EMBEDDINGS_MODEL

    try:
        if embeddings_class == "OllamaEmbeddings":
            # Usa Ollama via URL configurada no settings/env
            from langchain_ollama import OllamaEmbeddings

            base_url: str = getattr(settings, "OLLAMA_BASE_URL", "")
            kwargs: dict[str, Any] = {}
            if embeddings_model:
                kwargs["model"] = embeddings_model
            if base_url:
                kwargs["base_url"] = base_url
            return OllamaEmbeddings(**kwargs)

        if embeddings_class == "OpenAIEmbeddings":
            from langchain_openai import OpenAIEmbeddings

            if embeddings_model:
                return OpenAIEmbeddings(model=embeddings_model)
            return OpenAIEmbeddings()

        if embeddings_class == "HuggingFaceEmbeddings":
            from langchain_huggingface import HuggingFaceEmbeddings

            if embeddings_model:
                return HuggingFaceEmbeddings(model_name=embeddings_model)
            return HuggingFaceEmbeddings()

        raise ValueError(
            "Classe de embeddings não suportada: " f"{embeddings_class}"
        )
    except Exception as exc:  # pragma: no cover - proteção adicional
        # Loga erro e repassa para tratamento na chamada
        logger.error(
            "Falha ao criar instancia de embeddings: " f"{exc}",
            exc_info=True,
        )
        raise


def __embed_text(text: str) -> List[float]:
    """Gera o vetor de embedding para um texto.

    Tenta usar embed_query se disponível (preferível para uma única string),
    caso contrário, utiliza embed_documents.

    Args:
        text (str): Texto a ser convertido em embedding.

    Returns:
        List[float]: Vetor de embedding como lista de floats.
    """
    embeddings = __get_embeddings_instance()

    try:
        if hasattr(embeddings, "embed_query"):
            vec: List[float] = list(map(float, embeddings.embed_query(text)))
        else:
            # Fallback para APIs que suportam apenas embed_documents
            docs_vec: List[List[float]] = embeddings.embed_documents([text])
            vec = list(map(float, docs_vec[0]))
        return vec
    except Exception as exc:  # pragma: no cover - proteção adicional
        logger.error(
            "Erro ao gerar embedding do texto: " f"{exc}",
            exc_info=True,
        )
        raise


def __task_treinar_ia(instance_id: int) -> None:
    """Tarefa para treinar a IA com os documentos de um treinamento.

    Args:
        instance_id (int): O ID da instância de Treinamento.
    """
    try:
        instance = Treinamentos.objects.get(id=instance_id)

        # 1) Limpa embedding anterior sem disparar signals
        Treinamentos.objects.filter(id=instance_id).update(embedding=None)

        # 2) Extrai conteúdo unificado e gera embedding
        texto_unificado: str = instance.get_conteudo_unificado() or ""
        if not texto_unificado.strip():
            logger.warning(
                "Treinamento %s sem conteúdo para embedding.", instance_id
            )
            return

        vetor: List[float] = __embed_text(texto_unificado)

        # 3) Persiste vetor via update() para evitar loop de signals
        Treinamentos.objects.filter(id=instance_id).update(embedding=vetor)
        logger.info("Embedding atualizado para treinamento %s", instance_id)

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
        # Como os dados ficam no próprio modelo, basta limpar o vetor.
        Treinamentos.objects.filter(id=instance_id).update(embedding=None)
        logger.info(
            "Embedding removido para treinamento %s (pre_delete)", instance_id
        )
    except Exception as e:
        logger.error(f"Erro ao remover treinamento {instance_id}: {e}")
        raise
