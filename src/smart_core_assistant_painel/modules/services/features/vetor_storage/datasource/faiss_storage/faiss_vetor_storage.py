import os
from pathlib import Path
from typing import Any, Dict, List
from abc import ABCMeta

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from loguru import logger

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB
from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage,
)


class _FaissVetorStorageMeta(ABCMeta):
    """Metaclasse para implementar o padrão Singleton com suporte a ABC."""

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class FaissVetorStorage(VetorStorage, metaclass=_FaissVetorStorageMeta):
    """
    Implementação singleton do VetorStorage usando FAISS.
    Garante que todas as instâncias compartilhem o mesmo banco vetorial.
    """

    def __init__(self) -> None:
        """
        Inicializa o armazenamento FAISS.
        Cria ou carrega o banco vetorial existente.
        """
        # Evita reinicialização em instâncias subsequentes do Singleton
        if hasattr(self, "_initialized"):
            return

        self.__db_path = str(Path(__file__).parent / "banco_faiss")
        self.__embeddings = OllamaEmbeddings(model=SERVICEHUB.FAISS_MODEL)
        self.__vectordb = self.__inicializar_banco_vetorial()
        self._initialized = True

    def __faiss_db_exists(self, db_path: str) -> bool:
        """Verifica se o banco FAISS existe no caminho especificado."""
        return os.path.exists(os.path.join(db_path, "index.faiss"))

    def __inicializar_banco_vetorial(self) -> FAISS:
        """
        Inicializa o banco vetorial FAISS.
        Carrega o banco existente ou cria um novo se não existir.
        """
        if self.__faiss_db_exists(self.__db_path):
            try:
                vectordb = FAISS.load_local(
                    self.__db_path,
                    self.__embeddings,
                    allow_dangerous_deserialization=True,
                )

                return vectordb
            except Exception as e:
                logger.error(f"Erro ao carregar banco FAISS existente: {e}")
                return self.__criar_banco_vazio()
        else:
            return self.__criar_banco_vazio()

    def __criar_banco_vazio(self) -> FAISS:
        """Cria um banco FAISS vazio."""
        try:
            # Cria um documento dummy para inicializar o FAISS
            dummy_doc = Document(
                page_content="dummy", metadata={"temp_id": "dummy_init"}
            )

            # Cria o diretório se não existir
            os.makedirs(self.__db_path, exist_ok=True)

            # Cria o banco com o documento dummy
            vectordb = FAISS.from_documents([dummy_doc], self.__embeddings)

            # Salva temporariamente para poder usar o método de remoção
            vectordb.save_local(self.__db_path)

            # Atualiza a instância da classe para usar o método existente
            self.__vectordb = vectordb

            # Remove o documento dummy usando o método existente
            self.remove_by_metadata("temp_id", "dummy_init")

            # Retorna o banco limpo

            return self.__vectordb

        except Exception as e:
            logger.error(f"Erro ao criar banco FAISS vazio: {e}")
            raise

    def __sync_vectordb(self) -> None:
        """
        Sincroniza o banco vetorial recarregando do disco.
        Usado para garantir que mudanças de outros processos sejam visíveis.
        """
        try:
            if self.__faiss_db_exists(self.__db_path):
                self.__vectordb = FAISS.load_local(
                    self.__db_path,
                    self.__embeddings,
                    allow_dangerous_deserialization=True,
                )

        except Exception as e:
            logger.error(f"Erro ao sincronizar banco vetorial: {e}")

    def __find_by_metadata(self, metadata_key: str, metadata_value: str) -> List[str]:
        """
        Localiza IDs de documentos baseado em metadados específicos.

        Args:
            metadata_key: Chave do metadado para buscar
            metadata_value: Valor do metadado para buscar

        Returns:
            Lista de IDs de documentos que correspondem aos critérios
        """
        # Validação de entrada
        if not metadata_key or not metadata_value:
            return []

        matching_ids: List[str] = []

        try:
            if not (
                hasattr(self.__vectordb, "docstore")
                and hasattr(self.__vectordb, "index_to_docstore_id")
            ):
                return matching_ids

            # Verificar se o vectordb não está vazio
            if not self.__vectordb.index_to_docstore_id:
                return matching_ids

            # Usar método mais robusto para busca
            processed_count = 0
            for doc_id in self.__vectordb.index_to_docstore_id.values():
                try:
                    doc = self.__vectordb.docstore.search(doc_id)
                    if (
                        doc
                        and hasattr(doc, "metadata")
                        and doc.metadata
                        and doc.metadata.get(metadata_key) == metadata_value
                    ):
                        matching_ids.append(doc_id)

                    processed_count += 1

                except Exception as e:
                    logger.warning(f"Erro ao buscar documento {doc_id}: {e}")
                    continue

        except Exception as e:
            logger.error(
                f"Erro ao buscar por metadados {metadata_key}={metadata_value}: {e}"
            )

        return matching_ids

    def read(self, query_vector: str, k: int = 5) -> List[Document]:
        """
        Busca documentos similares no armazenamento FAISS.

        Args:
            query_vector: Vetor de consulta
            k: Número de documentos mais similares a retornar

        Returns:
            Lista de documentos encontrados
        """
        try:
            # Sincroniza com o disco antes de ler
            self.__sync_vectordb()

            results = self.__vectordb.similarity_search(query_vector, k=k)

            return results

        except Exception as e:
            logger.error(f"Erro ao ler documentos: {e}")
            return []

    def write(self, documents: List[Document]) -> None:
        """
        Adiciona uma lista de chunks de documentos ao banco vetorial.

        Args:
            chunks: Lista de chunks de documentos para adicionar

        Raises:
            ValueError: Se nenhum chunk válido for encontrado
            Exception: Erro ao adicionar documentos ao banco
        """
        # Sincroniza com o disco antes de escrever
        self.__sync_vectordb()

        if not documents:
            raise ValueError("Lista de documents está vazia")

        # Divide documentos em chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=SERVICEHUB.CHUNK_SIZE, chunk_overlap=SERVICEHUB.CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(documents)

        # Validação dos documentos
        valid_chunks = []
        for chunk in chunks:
            if not isinstance(chunk, Document):
                continue
            if not chunk.page_content or not chunk.page_content.strip():
                continue
            # Validar metadados se existirem
            if chunk.metadata is not None and not isinstance(chunk.metadata, dict):
                continue
            valid_chunks.append(chunk)

        if not valid_chunks:
            error_msg = "Nenhum chunk válido encontrado"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Verificar se o vectordb está disponível
            if not hasattr(self.__vectordb, "add_documents"):
                error_msg = "Vectorstore não possui método add_documents"
                logger.error(error_msg)
                raise AttributeError(error_msg)

            self.__vectordb.add_documents(valid_chunks)

            # Verificar se o save foi bem-sucedido
            self.__vectordb.save_local(self.__db_path)

            # Verificar se os arquivos foram salvos
            if not self.__faiss_db_exists(self.__db_path):
                error_msg = "Falha ao salvar banco FAISS no disco"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Erro ao adicionar documentos: {e}")
            raise ValueError(f"Erro ao adicionar documentos ao banco FAISS: {e}") from e

    def remove_by_metadata(
        self,
        metadata_key: str,
        metadata_value: str,
    ) -> None:
        """
        Remove vetores do armazenamento FAISS baseado em metadados.

        Args:
            metadata_key: Chave do metadado para buscar
            metadata_value: Valor do metadado para buscar
        """
        try:
            # Sincroniza com o disco antes de remover
            self.__sync_vectordb()

            # Busca documentos relacionados ao treinamento
            ids_para_remover = self.__find_by_metadata(
                metadata_key,
                metadata_value,
            )

            if ids_para_remover:
                # Verificar se docstore existe e tem método apropriado
                if not (
                    hasattr(self.__vectordb, "docstore")
                    and hasattr(self.__vectordb.docstore, "search")
                ):
                    logger.error(
                        "Vectorstore não possui estrutura necessária para remoção"
                    )
                    return

                # Validar que os IDs ainda existem no docstore
                ids_validos = []
                for doc_id in ids_para_remover:
                    try:
                        doc = self.__vectordb.docstore.search(str(doc_id))
                        if doc:
                            ids_validos.append(str(doc_id))
                    except Exception as e:
                        logger.warning(f"ID {doc_id} não encontrado no docstore: {e}")

                if ids_validos:
                    self.__vectordb.delete(ids_validos)
                    self.__vectordb.save_local(self.__db_path)

        except Exception as e:
            logger.error(
                f"Erro ao remover {metadata_key}: {metadata_value} do banco vetorial: {e}"
            )

    # def get_stats(self) -> Dict[str, Any]:
    #     """
    #     Retorna estatísticas do banco vetorial.

    #     Returns:
    #         Dicionário com estatísticas do banco
    #     """
    #     stats = {
    #         "total_documents": 0,
    #         "database_path": self.__db_path,
    #         "database_exists": self.__faiss_db_exists(self.__db_path),
    #         "model_name": getattr(self.__embeddings, 'model', 'unknown'),
    #         "has_docstore": False,
    #         "has_index": False
    #     }

    #     try:
    #         if hasattr(self.__vectordb, 'index_to_docstore_id'):
    #             stats["total_documents"] = len(
    #                 self.__vectordb.index_to_docstore_id)
    #             stats["has_index"] = True

    #         if hasattr(self.__vectordb, 'docstore'):
    #             stats["has_docstore"] = True

    #         logger.info(f"Estatísticas do banco: {stats}")

    #     except Exception as e:
    #         logger.error(f"Erro ao obter estatísticas: {e}")
    #         stats["error"] = str(e)

    #     return stats

    # def health_check(self) -> bool:
    #     """
    #     Verifica a saúde do banco vetorial.

    #     Returns:
    #         True se o banco está saudável, False caso contrário
    #     """
    #     try:
    #         # Verificar se os componentes essenciais existem
    #         if not hasattr(self.__vectordb, 'docstore'):
    #             logger.error("Banco não possui docstore")
    #             return False

    #         if not hasattr(self.__vectordb, 'index_to_docstore_id'):
    #             logger.error("Banco não possui mapeamento de índices")
    #             return False

    #         # Verificar se os arquivos no disco existem
    #         if not self.__faiss_db_exists(self.__db_path):
    #             logger.warning("Arquivos do banco não existem no disco")
    #             return False

    #         # Tentar fazer uma busca simples
    #         try:
    #             self.__vectordb.similarity_search("test", k=1)
    #             logger.debug("Teste de busca bem-sucedido")
    #         except Exception as e:
    #             logger.warning(f"Teste de busca falhou: {e}")
    #             # Não é crítico se o banco estiver vazio

    #         logger.info("Health check do banco passou")
    #         return True

    #     except Exception as e:
    #         logger.error(f"Health check falhou: {e}")
    #         return False
