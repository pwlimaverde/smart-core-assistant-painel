import json
import logging
import os

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

from .models import Treinamentos

logger = logging.getLogger(__name__)

# Constantes
FAISS_MODEL = "mxbai-embed-large"
CHUNK_SIZE = 1000  # Aumentado de 100 para melhor contexto
CHUNK_OVERLAP = 200  # Aumentado proporcionalmente


def get_faiss_db_path():
    """Retorna o caminho para o banco FAISS."""
    return settings.BASE_DIR.parent / 'db' / "banco_faiss"


def get_embeddings():
    """Retorna a instância de embeddings configurada."""
    return OllamaEmbeddings(model=FAISS_MODEL)


def faiss_db_exists(db_path):
    """Verifica se os arquivos necessários do FAISS existem."""
    index_faiss_path = db_path / "index.faiss"
    index_pkl_path = db_path / "index.pkl"
    return os.path.exists(index_faiss_path) and os.path.exists(index_pkl_path)


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
        db_path = get_faiss_db_path()

        if not faiss_db_exists(db_path):
            logger.warning(f"Banco FAISS não encontrado em {db_path}")
            return

        embeddings = get_embeddings()
        vectordb = FAISS.load_local(
            db_path,
            embeddings,
            allow_dangerous_deserialization=True
        )

        # Busca documentos relacionados ao treinamento
        ids_para_remover = find_by_metadata(
            vectordb, "id_treinamento", instance_id)

        if ids_para_remover:
            # Valida IDs existentes
            ids_existentes = set(vectordb.docstore._dict.keys())
            ids_validos = [
                str(doc_id) for doc_id in ids_para_remover
                if str(doc_id) in ids_existentes
            ]

            if ids_validos:
                vectordb.delete(ids_validos)
                vectordb.save_local(db_path)
                logger.info(
                    f"Removidos {
                        len(ids_validos)} documentos do treinamento {instance_id}")
            else:
                logger.warning(
                    f"Nenhum documento válido encontrado para remoção do treinamento {instance_id}")
        else:
            logger.info(
                f"Nenhum documento encontrado para o treinamento {instance_id}")

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

        # Adiciona metadados aos documentos para identificação
        for doc in documentos:
            if not doc.metadata:
                doc.metadata = {}
            doc.metadata["id_treinamento"] = instance_id
            doc.metadata["tag"] = instance.tag
            doc.metadata["grupo"] = instance.grupo

        # Divide documentos em chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(documentos)
        logger.info(
            f"Documentos divididos em {
                len(chunks)} chunks para treinamento {instance_id}")

        # Cria ou atualiza banco vetorial
        _criar_ou_atualizar_banco_vetorial(chunks)

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


def _criar_ou_atualizar_banco_vetorial(chunks):
    """
    Cria um novo banco vetorial ou atualiza o existente com novos chunks.

    Args:
        chunks: Lista de chunks de documentos para adicionar
    """
    embeddings = get_embeddings()
    db_path = get_faiss_db_path()

    if faiss_db_exists(db_path):
        # Carrega banco existente
        logger.info("Carregando banco vetorial existente")
        vectordb = FAISS.load_local(
            db_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        vectordb.add_documents(chunks)
        logger.info(f"Adicionados {len(chunks)} chunks ao banco existente")
    else:
        # Cria novo banco
        logger.info("Criando novo banco vetorial")
        vectordb = FAISS.from_documents(chunks, embeddings)

        # Cria o diretório se não existir
        os.makedirs(db_path, exist_ok=True)
        logger.info(f"Novo banco criado com {len(chunks)} chunks")

    vectordb.save_local(db_path)
    logger.info(f"Banco vetorial salvo em {db_path}")


def find_by_metadata(vectorstore, metadata_key, metadata_value):
    """
    Localiza IDs de documentos baseado em metadados específicos.

    Args:
        vectorstore: Instância do FAISS vectorstore
        metadata_key: Chave do metadado para buscar
        metadata_value: Valor do metadado para buscar

    Returns:
        List: Lista de IDs de documentos que correspondem aos critérios
    """
    matching_ids = []

    try:
        if hasattr(
                vectorstore,
                'docstore') and hasattr(
                vectorstore,
                'index_to_docstore_id'):
            for doc_id in vectorstore.index_to_docstore_id.values():
                try:
                    doc = vectorstore.docstore.search(doc_id)
                    if doc and hasattr(doc, 'metadata') and doc.metadata:
                        if doc.metadata.get(metadata_key) == metadata_value:
                            matching_ids.append(doc_id)
                except Exception as e:
                    logger.warning(f"Erro ao buscar documento {doc_id}: {e}")
                    continue

        logger.info(
            f"Encontrados {
                len(matching_ids)} documentos com {metadata_key}={metadata_value}")

    except Exception as e:
        logger.error(
            f"Erro ao buscar por metadados {metadata_key}={metadata_value}: {e}")

    return matching_ids
