"""Tasks para processamento de IA e Embeddings (Treinamento)."""

from celery import shared_task
from loguru import logger
from langchain_core.documents import Document

from smart_core_assistant_painel.app.treinamento.models import (
    Documento,
    QueryCompose,
    Treinamento,
)
from smart_core_assistant_painel.app.tenants.celery import TenantTask


def _processar_conteudo_para_chunks(
    treinamento: Treinamento,
) -> list[Document]:
    """Processa conteúdo e cria chunks."""
    from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
        FeaturesCompose,
    )

    metadata = {
        "source": "treinamento_manual",
        "treinamento_id": str(treinamento.pk),
        "tag": treinamento.tag,
        "grupo": treinamento.grupo,
    }

    conteudo = treinamento.conteudo or ""

    chunks = FeaturesCompose.generate_chunks(
        conteudo=conteudo, metadata=metadata
    )

    return chunks


@shared_task(base=TenantTask, queue="ai_processing", max_retries=3)
def task_gerar_embedding_documento(
    tenant_slug: str, documento_id: int
) -> None:
    """Gera embedding para um documento específico."""
    try:
        from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
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
            logger.info(
                f"Embedding gerado e salvo para documento {documento_id}"
            )
        else:
            logger.error(
                f"Falha ao gerar embedding para documento {documento_id}"
            )

    except Documento.DoesNotExist:
        logger.error(f"Documento {documento_id} não encontrado")
    except Exception as e:
        logger.error(
            f"Erro ao gerar embedding para documento {documento_id}: {e}"
        )


@shared_task(base=TenantTask, queue="ai_processing", max_retries=3)
def task_gerar_embedding_query_compose(
    tenant_slug: str, query_compose_id: int
) -> None:
    """Gera embedding para um QueryCompose específico."""
    try:
        from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
            FeaturesCompose,
        )

        qc: QueryCompose = QueryCompose.objects.get(id=query_compose_id)
        text: str = qc.to_embedding_text()
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
    except Exception as e:
        logger.error(
            f"Erro ao gerar embedding para QueryCompose {query_compose_id}: {e}"
        )


@shared_task(
    base=TenantTask, queue="ai_processing", max_retries=3, soft_time_limit=300
)
def task_gerar_documentos_treinamento(
    tenant_slug: str, instance_id: int
) -> None:
    """Gera documentos (chunks) a partir de um treinamento."""
    try:
        instance: Treinamento = Treinamento.objects.get(id=instance_id)

        if not instance.conteudo or not instance.conteudo.strip():
            logger.warning(
                "Treinamento %s sem conteúdo para embedding.", instance_id
            )
            return

        if instance.treinamento_vetorizado:
            logger.info(
                f"Treinamento {instance_id} já está vetorizado, pulando..."
            )
            return

        chunks: list[Document] = _processar_conteudo_para_chunks(
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
    except Exception as e:
        logger.error(f"Erro ao executar treinamento {instance_id}: {e}")


def remover_treinamento_ia_sync(instance_id: int) -> None:
    """Remove marcação vetorizada (síncrono/helper)."""
    try:
        Treinamento.objects.filter(id=instance_id).update(
            treinamento_vetorizado=False
        )
        logger.info(
            "Treinamento marcado como não vetorizado: %s (pre_delete)",
            instance_id,
        )
    except Exception as e:
        logger.error(f"Erro ao remover treinamento {instance_id}: {e}")
        raise
