"""Signals para o aplicativo Treinamento."""

from typing import Any

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_q.tasks import async_task
from langchain_core.documents.base import Document
from loguru import logger

from .models import Documento, QueryCompose, Treinamento


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
            async_task(__gerar_documentos, instance.id)
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
                async_task(__gerar_embedding_documento, instance.pk)
            else:
                logger.warning(f"Documento {instance.pk} sem conteúdo para embedding")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Erro no signal de embedding do documento {instance.pk}: {e}")


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
                async_task(__gerar_embedding_query_compose, instance.pk)
            else:
                logger.warning(
                    f"QueryCompose {instance.pk} sem descricao para embedding"
                )
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Erro no signal de embedding do QueryCompose {instance.pk}: {e}"
        )


def __processar_conteudo_para_chunks(
    treinamento: Treinamento,
) -> list[Document]:
    """Processa conteúdo e cria chunks."""
    from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (  # noqa: E501
        FeaturesCompose,
    )

    metadata = {
        "source": "treinamento_manual",
        "treinamento_id": str(treinamento.pk),
        "tag": treinamento.tag,
        "grupo": treinamento.grupo,
    }

    conteudo = treinamento.conteudo or ""

    chunks = FeaturesCompose.generate_chunks(conteudo=conteudo, metadata=metadata)

    return chunks


def __gerar_embedding_documento(documento_id: int) -> None:
    """Gera embedding para um documento específico."""
    try:
        from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (  # noqa: E501
            FeaturesCompose,
        )

        documento: Documento = Documento.objects.get(id=documento_id)

        if not documento.conteudo or not documento.conteudo.strip():
            logger.warning(f"Documento {documento_id} sem conteúdo válido")
            return

        embedding_vector: list[float] = FeaturesCompose.generate_embeddings(
            text=documento.conteudo
        )

        if embedding_vector:
            Documento.objects.filter(id=documento_id).update(
                embedding=embedding_vector
            )
            logger.info(f"Embedding gerado e salvo para documento {documento_id}")
        else:
            logger.error(f"Falha ao gerar embedding para documento {documento_id}")

    except Documento.DoesNotExist:
        logger.error(f"Documento {documento_id} não encontrado")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Erro ao gerar embedding para documento {documento_id}: {e}")


def __gerar_embedding_query_compose(query_compose_id: int) -> None:
    """Gera embedding para um QueryCompose específico."""
    try:
        from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (  # noqa: E501
            FeaturesCompose,
        )

        qc: QueryCompose = QueryCompose.objects.get(id=query_compose_id)
        text:str = f"{qc.tag}: {qc.exemplo}"
        embedding_vector: list[float] = FeaturesCompose.generate_embeddings(
            text=text
        )

        if embedding_vector:
            QueryCompose.objects.filter(id=query_compose_id).update(
                embedding=embedding_vector
            )
            logger.info(
                f"Embedding gerado e salvo para QueryCompose {query_compose_id}"
            )
        else:
            logger.error(
                f"Falha ao gerar embedding para QueryCompose {query_compose_id}"
            )

    except QueryCompose.DoesNotExist:
        logger.error(f"QueryCompose {query_compose_id} não encontrado")
    except Exception as e:  # noqa: BLE001
        logger.error(
            f"Erro ao gerar embedding para QueryCompose {query_compose_id}: {e}"
        )


def __gerar_documentos(instance_id: int) -> None:
    try:
        instance: Treinamento = Treinamento.objects.get(id=instance_id)

        if not instance.conteudo or not instance.conteudo.strip():
            logger.warning("Treinamento %s sem conteúdo para embedding.", instance_id)
            return

        if instance.treinamento_vetorizado:
            logger.info(f"Treinamento {instance_id} já está vetorizado, pulando...")
            return
        chunks: list[Document] = __processar_conteudo_para_chunks(
            treinamento=instance
        )

        Documento.criar_documentos_de_chunks(
            chunks=chunks, treinamento_id=instance_id
        )
        instance.treinamento_vetorizado = True
        instance.save()
        logger.info("Documentos gerados: %s", instance_id)

    except Treinamento.DoesNotExist:
        logger.error(f"Treinamento com ID {instance_id} não encontrado.")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Erro ao executar treinamento {instance_id}: {e}")


@receiver(pre_delete, sender=Treinamento)
def signal_remover_treinamento_ia(
    sender: Any, instance: Treinamento, **kwargs: Any
) -> None:
    """Remove os dados de treinamento do banco vetorial antes de deletar."""
    try:
        if instance.treinamento_finalizado:
            __task_remover_treinamento_ia(instance.id)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Erro ao processar remoção de treinamento: {e}")
        raise Exception(f"Falha ao remover treinamento {instance.id}: {e}")


def __task_remover_treinamento_ia(instance_id: int) -> None:
    """Tarefa para remover um treinamento do banco vetorial."""
    try:
        Treinamento.objects.filter(id=instance_id).update(
            treinamento_vetorizado=False
        )
        logger.info(
            "Treinamento marcado como não vetorizado: %s (pre_delete)",
            instance_id,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Erro ao remover treinamento {instance_id}: {e}")
        raise
