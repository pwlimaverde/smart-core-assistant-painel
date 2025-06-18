import os

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from loguru import logger

from .models import Treinamentos


@receiver(post_save, sender=Treinamentos)
def signals_treinamento_ia(sender, instance, created, **kwargs):
    if instance.treinamento_finalizado:
        async_task(task_treinar_ia, instance.id)


@receiver(post_delete, sender=Treinamentos)
def task_remover_treinamento_ia(sender, instance, **kwargs):
    if instance.treinamento_finalizado:
        db_path = settings.BASE_DIR.parent / 'db' / "banco_faiss"
        if os.path.exists(db_path):
            vectordb = FAISS.load_local(
                db_path,
                OllamaEmbeddings(
                    model="mxbai-embed-large"),
                allow_dangerous_deserialization=True)
            teste = find_by_metadata(vectordb, "id_treinamento", instance.id)
            logger.error(f"🎉 id para apagar {instance.id}")
            logger.error(f"🎉 id list {teste}")
            if teste:
                ids_existentes = set(vectordb.docstore._dict.keys())
                logger.warning(f"🎉 ids_existentes {ids_existentes}")
                ids_para_remover_str = [str(id) for id in teste]
                logger.warning(
                    f"🎉 ids_para_remover_str {ids_para_remover_str}")
                ids_validos = [
                    id for id in ids_para_remover_str if id in ids_existentes]
                logger.warning(f"🎉 ids_validos {ids_validos}")
                logger.success(f"🎉 Dados removidos com sucesso {teste}")
                vectordb.delete(ids_validos)
                vectordb.save_local(db_path)
            else:
                logger.warning("🎉 Nenhum dado encontrado para remover")
        else:
            logger.error("🎉 Banco de dados não encontrado")


def task_treinar_ia(instance_id):
    instance = Treinamentos.objects.get(id=instance_id)
    documentos = [Document.model_validate_json(instance.documento)]
    logger.success(f"🎉 Processamento concluído {documentos}")
    logger.success(f"🎉 Tipo de dado  {type(documentos)}")
    if not documentos:
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=100, chunk_overlap=20)
    chunks = splitter.split_documents(documentos)

    embeddings = OllamaEmbeddings(model="mxbai-embed-large")

    db_path = settings.BASE_DIR.parent / 'db' / "banco_faiss"
    if os.path.exists(db_path):
        vectordb = FAISS.load_local(
            db_path, embeddings, allow_dangerous_deserialization=True)
        vectordb.add_documents(chunks)

        teste = find_by_metadata(vectordb, "grupo", instance.grupo)
        logger.warning(f"🎉 Dados os exists salvos {teste}")
    else:
        vectordb = FAISS.from_documents(chunks, embeddings)
        logger.warning("🎉 Dados salvos criados")
    vectordb.save_local(db_path)


# Exemplo de busca por metadados específicos
def find_by_metadata(vectorstore, metadata_key, metadata_value):
    """
    Localiza índices de documentos baseado em metadados específicos
    """
    matching_indices = []

    # Se usando LangChain FAISS
    if hasattr(vectorstore, 'docstore'):
        for i, doc_id in enumerate(vectorstore.index_to_docstore_id.values()):
            doc = vectorstore.docstore.search(doc_id)
            if doc and hasattr(doc, 'metadata'):
                if doc.metadata.get(metadata_key) == metadata_value:
                    matching_indices.append(doc_id)

    return matching_indices
