import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from loguru import logger

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB
from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage, )


class FaissVetorStorage(VetorStorage):
    """
    Implementação singleton do VetorStorage usando FAISS.
    Garante que todas as instâncias compartilhem o mesmo banco vetorial.
    """

    _instance = None
    _initialized = False
    _lock = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Inicializa o armazenamento FAISS.
        Cria ou carrega o banco vetorial existente.
        """
        if not self._initialized:
            # Import aqui para evitar problemas de importação circular
            import threading
            if FaissVetorStorage._lock is None:
                FaissVetorStorage._lock = threading.Lock()

            with FaissVetorStorage._lock:
                if not self._initialized:
                    self.__db_path = str(Path(__file__).parent / "banco_faiss")
                    self.__embeddings = OllamaEmbeddings(
                        model=SERVICEHUB.FAISS_MODEL)
                    self.__vectordb = self.__inicializar_banco_vetorial()
                    FaissVetorStorage._initialized = True
                    logger.info(
                        f"FaissVetorStorage singleton inicializado (ID: {
                            id(self)})")

    def __faiss_db_exists(self, db_path: str) -> bool:
        """Verifica se o banco FAISS existe no caminho especificado."""
        return os.path.exists(os.path.join(db_path, "index.faiss"))

    def __inicializar_banco_vetorial(self) -> FAISS:
        """
        Inicializa o banco vetorial FAISS.
        Carrega o banco existente ou cria um novo se não existir.
        """
        if self.__faiss_db_exists(self.__db_path):
            logger.info("Carregando banco vetorial FAISS existente")
            try:
                vectordb = FAISS.load_local(
                    self.__db_path,
                    self.__embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Banco vetorial FAISS carregado com sucesso")
                return vectordb
            except Exception as e:
                logger.error(f"Erro ao carregar banco FAISS existente: {e}")
                return self.__criar_banco_vazio()
        else:
            logger.info("Criando novo banco vetorial FAISS vazio")
            return self.__criar_banco_vazio()

    def __criar_banco_vazio(self) -> FAISS:
        """Cria um banco FAISS vazio."""
        try:
            # Cria um documento dummy para inicializar o FAISS
            dummy_doc = Document(
                page_content="dummy", metadata={
                    "temp_id": "dummy_init"})

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
            logger.info(
                f"Banco vetorial FAISS vazio criado em {
                    self.__db_path}")
            return self.__vectordb

        except Exception as e:
            logger.error(f"Erro ao criar banco FAISS vazio: {e}")
            raise

    def __find_by_metadata(
            self,
            metadata_key: str,
            metadata_value: str) -> List[str]:
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
            logger.warning("Chave ou valor de metadado não podem estar vazios")
            return []

        matching_ids: List[str] = []

        try:
            if not (hasattr(self.__vectordb, 'docstore') and
                    hasattr(self.__vectordb, 'index_to_docstore_id')):
                logger.warning(
                    "Vectorstore não possui estrutura necessária para busca por metadados")
                return matching_ids

            # Verificar se o vectordb não está vazio
            if not self.__vectordb.index_to_docstore_id:
                logger.info("Banco vetorial está vazio")
                return matching_ids

            total_docs = len(self.__vectordb.index_to_docstore_id)
            logger.debug(
                f"Buscando em {total_docs} documentos por {metadata_key}={metadata_value}")

            # Usar método mais robusto para busca
            processed_count = 0
            for doc_id in self.__vectordb.index_to_docstore_id.values():
                try:
                    doc = self.__vectordb.docstore.search(doc_id)
                    if (doc and
                        hasattr(doc, 'metadata') and
                        doc.metadata and
                            doc.metadata.get(metadata_key) == metadata_value):
                        matching_ids.append(doc_id)

                    processed_count += 1
                    # Log de progresso para bancos grandes
                    if processed_count % 1000 == 0:
                        logger.debug(
                            f"Processados {processed_count}/{total_docs} documentos")

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

    def read(self,
             query_vector: Optional[List[float]] = None,
             metadata: Optional[Dict[str, Any]] = None,
             k: int = 5) -> List[Document]:
        """
        Busca documentos similares no armazenamento FAISS.

        Args:
            query_vector: Vetor de consulta (opcional)
            metadata: Metadados para filtrar a busca (opcional)
            k: Número de documentos mais similares a retornar

        Returns:
            Lista de documentos encontrados
        """
        try:
            # Sincroniza com o disco antes de ler
            self._sync_vectordb()

            if query_vector:
                results = self.__vectordb.similarity_search_by_vector(
                    query_vector, k=k)
                logger.info(
                    f"Encontrados {
                        len(results)} documentos por similaridade vetorial")
                return results

            elif metadata:
                # Implementação corrigida: busca por TODOS os metadados (AND
                # logic)
                if not metadata:
                    logger.warning("Dicionário de metadados está vazio")
                    return []

                matching_docs = []

                # Se temos apenas uma chave de metadado, busca simples
                if len(metadata) == 1:
                    key, value = next(iter(metadata.items()))
                    doc_ids = self.__find_by_metadata(key, str(value))

                    for doc_id in doc_ids[:k]:  # Limitar desde o início
                        try:
                            doc = self.__vectordb.docstore.search(doc_id)
                            if doc:
                                matching_docs.append(doc)
                        except Exception as e:
                            logger.warning(
                                f"Erro ao recuperar documento {doc_id}: {e}")

                else:
                    # Para múltiplos metadados, fazer intersecção
                    sets_of_ids = []
                    for key, value in metadata.items():
                        doc_ids = self.__find_by_metadata(key, str(value))
                        sets_of_ids.append(set(doc_ids))

                    # Intersecção de todos os conjuntos
                    if sets_of_ids:
                        common_ids = sets_of_ids[0]
                        for id_set in sets_of_ids[1:]:
                            common_ids = common_ids.intersection(id_set)

                        # Recuperar documentos da intersecção
                        for doc_id in list(common_ids)[:k]:
                            try:
                                doc = self.__vectordb.docstore.search(doc_id)
                                if doc:
                                    matching_docs.append(doc)
                            except Exception as e:
                                logger.warning(
                                    f"Erro ao recuperar documento {doc_id}: {e}")

                logger.info(
                    f"Encontrados {
                        len(matching_docs)} documentos por metadados")
                return matching_docs

            else:
                logger.warning("Nenhum critério de busca fornecido")
                return []

        except Exception as e:
            logger.error(f"Erro ao ler documentos: {e}")
            return []

    def write(self, chunks: List[Document]) -> None:
        """
        Adiciona uma lista de chunks de documentos ao banco vetorial.

        Args:
            chunks: Lista de chunks de documentos para adicionar

        Raises:
            ValueError: Se nenhum chunk válido for encontrado
            Exception: Erro ao adicionar documentos ao banco
        """
        if not chunks:
            logger.warning("Lista de chunks está vazia")
            return

        # Validação dos documentos
        valid_chunks = []
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, Document):
                logger.warning(
                    f"Chunk {i} não é uma instância válida de Document")
                continue
            if not chunk.page_content or not chunk.page_content.strip():
                logger.warning(f"Chunk {i} possui conteúdo vazio ou nulo")
                continue
            # Validar metadados se existirem
            if chunk.metadata is not None and not isinstance(
                    chunk.metadata, dict):
                logger.warning(f"Chunk {i} possui metadados inválidos")
                continue
            valid_chunks.append(chunk)

        if not valid_chunks:
            error_msg = "Nenhum chunk válido encontrado"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Verificar se o vectordb está disponível
            if not hasattr(self.__vectordb, 'add_documents'):
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

            logger.info(
                f"Adicionados {
                    len(valid_chunks)} chunks válidos ao banco FAISS")

        except Exception as e:
            logger.error(f"Erro ao adicionar documentos: {e}")
            raise

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
            self._sync_vectordb()

            # Busca documentos relacionados ao treinamento
            ids_para_remover = self.__find_by_metadata(
                metadata_key, metadata_value,)

            if ids_para_remover:
                # Verificar se docstore existe e tem método apropriado
                if not (hasattr(self.__vectordb, 'docstore') and
                        hasattr(self.__vectordb.docstore, 'search')):
                    logger.error(
                        "Vectorstore não possui estrutura necessária para remoção")
                    return

                # Validar que os IDs ainda existem no docstore
                ids_validos = []
                for doc_id in ids_para_remover:
                    try:
                        doc = self.__vectordb.docstore.search(str(doc_id))
                        if doc:
                            ids_validos.append(str(doc_id))
                    except Exception as e:
                        logger.warning(
                            f"ID {doc_id} não encontrado no docstore: {e}")

                if ids_validos:
                    self.__vectordb.delete(ids_validos)
                    self.__vectordb.save_local(self.__db_path)
                    logger.info(
                        f"Removidos {
                            len(ids_validos)} documentos do {metadata_key}: {metadata_value}")
                else:
                    logger.warning(
                        f"Nenhum documento válido encontrado para remoção do {metadata_key}: {metadata_value}")
            else:
                logger.info(
                    f"Nenhum documento encontrado para o {metadata_key}: {metadata_value}")

        except Exception as e:
            logger.error(
                f"Erro ao remover {metadata_key}: {metadata_value} do banco vetorial: {e}")

    def _sync_vectordb(self):
        """
        Sincroniza o banco vetorial recarregando do disco.
        Usado para garantir que mudanças de outros processos sejam visíveis.
        """
        try:
            if self.__faiss_db_exists(self.__db_path):
                logger.debug("Sincronizando banco vetorial com o disco")
                self.__vectordb = FAISS.load_local(
                    self.__db_path,
                    self.__embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.debug("Banco vetorial sincronizado com sucesso")
            else:
                logger.warning(
                    "Arquivo do banco vetorial não encontrado para sincronização")
        except Exception as e:
            logger.error(f"Erro ao sincronizar banco vetorial: {e}")

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
