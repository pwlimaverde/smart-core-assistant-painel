"""Signals para o aplicativo Treinamento."""

from typing import Any

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from loguru import logger

from smart_core_assistant_painel.app.tenants.tenant_context import (
    get_current_tenant_slug,
)

from .models import Documento, QueryCompose, Treinamento
from .tasks import (
    remover_treinamento_ia_sync,
    task_gerar_documentos_treinamento,
    task_gerar_embedding_documento,
    task_gerar_embedding_query_compose,
)


@receiver(post_save, sender=Treinamento)
def signals_gerar_documentos_treinamento(
    sender: Any, instance: Treinamento, created: bool, **kwargs: Any
) -> None:
    """Executa o treinamento da IA de forma assíncrona após salvar um treinamento."""
    try:
        if (
            instance.treinamento_finalizado
            and not instance.treinamento_vetorizado
        ):
            task_gerar_documentos_treinamento.delay(
                get_current_tenant_slug(), instance.id
            )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Erro ao processar signal de treinamento: {e}")


@receiver(post_save, sender=Documento)
def signals_embeddings_documento(
    sender: Any, instance: Documento, created: bool, **kwargs: Any
) -> None:
    """Gera embedding para o documento após criação ou atualização."""
    try:
        if not instance.embedding or not instance.conteudo:
            if instance.conteudo and instance.conteudo.strip():
                task_gerar_embedding_documento.delay(
                    get_current_tenant_slug(), instance.pk
                )
            else:
                logger.warning(
                    f"Documento {instance.pk} sem conteúdo para embedding"
                )
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Erro no signal de embedding do documento {instance.pk}: {e}"
        )


@receiver(post_save, sender=QueryCompose)
def signals_embeddings_query_compose(
    sender: Any, instance: QueryCompose, created: bool, **kwargs: Any
) -> None:
    """Gera embedding para QueryCompose após criação ou atualização.

    - Quando o registro for salvo sem embedding, agenda uma tarefa assíncrona
      para gerar o vetor com base em ``descricao``.
    """
    try:
        if not instance.embedding or not instance.descricao:
            if instance.descricao and instance.descricao.strip():
                task_gerar_embedding_query_compose.delay(
                    get_current_tenant_slug(), instance.pk
                )
            else:
                logger.warning(
                    f"QueryCompose {instance.pk} sem descricao para embedding"
                )
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Erro no signal de embedding do QueryCompose {instance.pk}: {e}"
        )


@receiver(pre_delete, sender=Treinamento)
def signal_remover_treinamento_ia(
    sender: Any, instance: Treinamento, **kwargs: Any
) -> None:
    """Remove os dados de treinamento do banco vetorial antes de deletar."""
    try:
        if instance.treinamento_finalizado:
            # Sync helper call (quick db update)
            remover_treinamento_ia_sync(instance.id)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Erro ao processar remoção de treinamento: {e}")
        raise Exception(f"Falha ao remover treinamento {instance.id}: {e}")
