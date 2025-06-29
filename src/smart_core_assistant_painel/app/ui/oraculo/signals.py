import json

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB

from .models import Treinamentos


@receiver(post_save, sender=Treinamentos)
def signals_treinamento_ia(sender, instance, created, **kwargs):
    """
    Signal executado após salvar um treinamento.
    Executa o treinamento da IA de forma assíncrona se o treinamento foi finalizado.
    """
    try:
        if instance.treinamento_finalizado:
            logger.info(
                f"Iniciando treinamento assíncrono para instância {
                    instance.id}")
            async_task(task_treinar_ia, instance.id)
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de treinamento para instância {
                instance.id}: {e}")


@receiver(post_delete, sender=Treinamentos)
def signal_remover_treinamento_ia(sender, instance, **kwargs):
    """
    Signal executado após deletar um treinamento.
    Remove os dados do treinamento do banco vetorial FAISS.
    """
    try:
        if instance.treinamento_finalizado:
            logger.info(
                f"Removendo treinamento {
                    instance.id} do banco vetorial")
            async_task(task_remover_treinamento_ia, instance.id)
    except Exception as e:
        logger.error(
            f"Erro ao processar remoção de treinamento para instância {
                instance.id}: {e}")


def task_remover_treinamento_ia(instance_id):
    """
    Task para remover um treinamento específico do banco vetorial FAISS.
    """
    try:
        logger.info(f"Removendo treinamento {instance_id} do banco vetorial")
        SERVICEHUB.vetor_storage.remove_by_metadata(
            "id_treinamento", str(instance_id))
        logger.info(
            f"Treinamento {instance_id} removido com sucesso do banco vetorial")

    except Exception as e:
        logger.error(
            f"Erro ao remover treinamento {instance_id} do banco vetorial: {e}")


def task_treinar_ia(instance_id):
    """
    Task para treinar a IA com documentos de um treinamento específico.

    Args:
        instance_id: ID da instância de Treinamento
    """
    try:
        logger.info(
            f"Iniciando task de treinamento para instância {instance_id}")

        # Busca a instância do treinamento
        try:
            instance = Treinamentos.objects.get(id=instance_id)
        except Treinamentos.DoesNotExist:
            logger.error(f"Treinamento com ID {instance_id} não encontrado")
            return

        # Processa documentos
        documentos = _processar_documentos(instance.documentos)
        if not documentos:
            logger.warning(
                f"Nenhum documento encontrado para o treinamento {instance_id}")
            return

        # Divide documentos em chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=SERVICEHUB.CHUNK_SIZE,
            chunk_overlap=SERVICEHUB.CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(documentos)

        # Adiciona metadados de identificação do treinamento aos chunks
        for chunk in chunks:
            if chunk.metadata is None:
                chunk.metadata = {}
            chunk.metadata["id_treinamento"] = str(instance_id)

        logger.info(
            f"Documentos divididos em {
                len(chunks)} chunks para treinamento {instance_id}")

        # Cria ou atualiza banco vetorial
        SERVICEHUB.vetor_storage.write(chunks)

        logger.info(f"Treinamento {instance_id} concluído com sucesso")

    except Exception as e:
        logger.error(f"Erro ao executar treinamento {instance_id}: {e}")


def _processar_documentos(documentos_raw):
    """
    Processa e converte documentos JSON para objetos Document.

    Args:
        documentos_raw: Lista de documentos em formato JSON ou string

    Returns:
        List[Document]: Lista de documentos processados
    """
    documentos = []

    if not documentos_raw:
        return documentos

    try:
        # Se é uma string, faz parse primeiro
        if isinstance(documentos_raw, str):
            documentos_lista = json.loads(documentos_raw)
        else:
            documentos_lista = documentos_raw

        # Converte cada documento para objeto Document
        for doc_json in documentos_lista:
            if isinstance(doc_json, str):
                # Se é string JSON, faz parse primeiro
                documento = Document.model_validate_json(doc_json)
            else:
                # Se já é dicionário, converte para Document
                documento = Document(**doc_json)
            documentos.append(documento)

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error(f"Erro ao processar documentos: {e}")

    return documentos
