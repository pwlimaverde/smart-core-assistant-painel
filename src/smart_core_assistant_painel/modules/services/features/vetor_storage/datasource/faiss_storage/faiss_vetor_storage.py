"""Implementação da interface VetorStorage baseada em FAISS.

Este módulo fornece uma implementação concreta do `VetorStorage` usando
a biblioteca FAISS para busca de similaridade eficiente. Ele emprega um
padrão singleton para garantir que uma única instância do banco de dados vetorial
seja compartilhada em toda a aplicação.

Classes:
    _FaissVetorStorageMeta: Metaclasse para garantir o padrão Singleton.
    FaissVetorStorage: A classe principal para o armazenamento vetorial FAISS.
"""

import os
from abc import ABCMeta
from pathlib import Path
from typing import Any, Dict, List

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from loguru import logger
from pydantic import ValidationError

from smart_core_assistant_painel.modules.services.features.service_hub import (
    SERVICEHUB,
)
from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage,
)


class _FaissVetorStorageMeta(ABCMeta):
    """Metaclasse para implementar o padrão Singleton com suporte a ABC.

    Attributes:
        _instances (Dict[type, Any]): Armazena as instâncias singleton.
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Garante que apenas uma instância da classe seja criada.

        Args:
            *args: Lista de argumentos variáveis.
            **kwargs: Argumentos de palavra-chave arbitrários.

        Returns:
            Any: A instância singleton da classe.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class FaissVetorStorage(VetorStorage, metaclass=_FaissVetorStorageMeta):
    """Implementação singleton do VetorStorage usando FAISS.

    Garante que todas as instâncias compartilhem o mesmo banco de dados vetorial.

    Attributes:
        _initialized (bool): Flag para evitar reinicialização.
        __db_path (str): Caminho para o diretório do banco de dados FAISS.
        __embeddings (Any): A instância do modelo de embeddings.
        __vectordb (FAISS): A instância do banco de dados vetorial FAISS.
    """

    def __init__(self) -> None:
        """Inicializa o armazenamento FAISS.

        Cria ou carrega o banco de dados vetorial existente. A inicialização
        é executada apenas uma vez devido ao padrão singleton.
        """
        if hasattr(self, "_initialized"):
            return

        self.__db_path = str(Path(__file__).parent / "banco_faiss")
        self.__embeddings = self.__create_embeddings()
        self.__vectordb = self.__initialize_vector_database()
        self._initialized = True

    def __create_embeddings(self) -> Any:
        """Cria uma instância de embeddings com base na classe configurada.

        Tenta instanciar a classe primeiro com 'model_name' (padrão para
        classes HuggingFace) e depois com 'model' (padrão para Ollama),
        evitando passar argumentos posicionais para modelos baseados em Pydantic.

        Returns:
            Any: Uma instância da classe de embeddings configurada.

        Raises:
            TypeError: Se a classe de embeddings não puder ser instanciada com as
                       configurações de modelo e chave de API fornecidas.
        """
        emb_cls = SERVICEHUB.EMBEDDINGS_CLASS
        model = SERVICEHUB.EMBEDDINGS_MODEL
        api_key = SERVICEHUB.HUGGINGFACE_API_KEY

        if api_key:
            try:
                return emb_cls(model_name=model, api_key=api_key)  # type: ignore[call-arg]
            except (TypeError, ValidationError):
                try:
                    return emb_cls(model_name=model, huggingfacehub_api_token=api_key)  # type: ignore[call-arg]
                except (TypeError, ValidationError):
                    try:
                        return emb_cls(model_name=model)  # type: ignore[call-arg]
                    except (TypeError, ValidationError):
                        pass
        else:
            try:
                return emb_cls(model_name=model)  # type: ignore[call-arg]
            except (TypeError, ValidationError):
                pass

        try:
            return emb_cls(model=model)  # type: ignore[call-arg]
        except (TypeError, ValidationError) as e:
            logger.error(
                "Não foi possível instanciar a classe de embeddings. "
                f"classe={getattr(emb_cls, '__name__', str(emb_cls))}, "
                f"model={model}, erro={e}"
            )
            raise

    def __faiss_db_exists(self, db_path: str) -> bool:
        """Verifica se o banco de dados FAISS existe no caminho especificado.

        Args:
            db_path (str): O caminho para o diretório do banco de dados.

        Returns:
            bool: True se 'index.faiss' existir, False caso contrário.
        """
        return os.path.exists(os.path.join(db_path, "index.faiss"))

    def __initialize_vector_database(self) -> FAISS:
        """Inicializa o banco de dados vetorial FAISS.

        Carrega um banco de dados existente ou cria um novo se não existir.

        Returns:
            FAISS: A instância FAISS inicializada.
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
                logger.error(f"Erro ao carregar banco de dados FAISS existente: {e}")
                return self.__create_empty_database()
        else:
            return self.__create_empty_database()

    def __create_empty_database(self) -> FAISS:
        """Cria um banco de dados FAISS vazio.

        Inicializa o banco de dados com um documento fictício, salva-o, remove o
        documento fictício e, em seguida, retorna o banco de dados limpo.

        Returns:
            FAISS: Uma instância FAISS vazia e limpa.

        Raises:
            Exception: Se a criação do banco de dados vazio falhar.
        """
        try:
            dummy_doc = Document(
                page_content="dummy", metadata={"temp_id": "dummy_init"}
            )
            os.makedirs(self.__db_path, exist_ok=True)
            vectordb = FAISS.from_documents([dummy_doc], self.__embeddings)
            vectordb.save_local(self.__db_path)
            self.__vectordb = vectordb
            self.remove_by_metadata("temp_id", "dummy_init")
            return self.__vectordb
        except Exception as e:
            logger.error(f"Erro ao criar banco de dados FAISS vazio: {e}")
            raise

    def __sync_vectordb(self) -> None:
        """Sincroniza o banco de dados vetorial recarregando-o do disco.

        Usado para garantir que as alterações de outros processos sejam visíveis.
        """
        try:
            if self.__faiss_db_exists(self.__db_path):
                self.__vectordb = FAISS.load_local(
                    self.__db_path,
                    self.__embeddings,
                    allow_dangerous_deserialization=True,
                )
        except Exception as e:
            logger.error(f"Erro ao sincronizar banco de dados vetorial: {e}")

    def __find_by_metadata(self, metadata_key: str, metadata_value: str) -> List[str]:
        """Encontra IDs de documentos com base em metadados específicos.

        Args:
            metadata_key (str): A chave de metadados a ser pesquisada.
            metadata_value (str): O valor de metadados a ser correspondido.

        Returns:
            List[str]: Uma lista de IDs de documentos que correspondem aos critérios.
        """
        if not metadata_key or not metadata_value:
            return []

        matching_ids: List[str] = []
        try:
            if not (
                hasattr(self.__vectordb, "docstore")
                and hasattr(self.__vectordb, "index_to_docstore_id")
            ):
                return matching_ids
            if not self.__vectordb.index_to_docstore_id:
                return matching_ids

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
                except Exception as e:
                    logger.warning(f"Erro ao pesquisar documento {doc_id}: {e}")
                    continue
        except Exception as e:
            logger.error(
                f"Erro ao pesquisar por metadados {metadata_key}={metadata_value}: {e}"
            )

        return matching_ids

    def read(self, query_vector: str, k: int = 5) -> List[Document]:
        """Busca por documentos similares no armazenamento FAISS.

        Args:
            query_vector (str): O vetor de consulta a ser pesquisado.
            k (int): O número de documentos mais similares a serem retornados.

        Returns:
            List[Document]: Uma lista de documentos encontrados.
        """
        try:
            self.__sync_vectordb()
            results = self.__vectordb.similarity_search(query_vector, k=k)
            if not results:
                return []

            documents: List[Document] = []
            for doc in results:
                if isinstance(doc, Document):
                    documents.append(doc)
            return documents
        except Exception as e:
            logger.error(f"Erro ao ler dos embeddings FAISS: {e}")
            return []

    def write(self, documents: list[Document]) -> None:
        """Adiciona documentos ao armazenamento vetorial e persiste no disco.

        Garante robustez convertendo entradas não-Documento quando possível
        e ignorando as inválidas. Sincroniza o banco de dados antes de escrever para
        refletir alterações externas.

        Args:
            documents (list[Document]): Uma lista de documentos a serem adicionados.

        Raises:
            ValueError: Se a lista de documentos estiver vazia ou se nenhum chunk válido
                        puder ser criado, ou se a adição de documentos falhar.
        """
        self.__sync_vectordb()
        if not documents:
            raise ValueError("A lista de documentos está vazia.")

        docs: list[Document] = []
        for item in documents:
            if isinstance(item, Document):
                docs.append(item)

        if not docs:
            raise ValueError("Nenhum chunk válido encontrado")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=SERVICEHUB.CHUNK_SIZE,
            chunk_overlap=SERVICEHUB.CHUNK_OVERLAP,
            length_function=len,
            is_separator_regex=False,
        )

        chunked_docs: list[Document] = []
        for doc in docs:
            content = (doc.page_content or "").strip()
            if not content:
                continue
            chunks = splitter.split_text(content)
            for chunk in chunks:
                chunked_docs.append(
                    Document(page_content=chunk.strip(), metadata=doc.metadata)
                )

        if not chunked_docs:
            raise ValueError("Nenhum chunk válido encontrado")

        try:
            self.__vectordb.add_documents(chunked_docs)
            self.__vectordb.save_local(self.__db_path)
        except Exception as e:
            raise ValueError(
                f"Erro ao adicionar documentos ao banco de dados FAISS: {e}"
            ) from e

    def add_from_file(
        self,
        file_path: str,
        chunk_overlap: int | None = None,
        chunk_size: int | None = None,
    ) -> bool:
        """Adiciona o conteúdo de um arquivo de texto ao armazenamento FAISS.

        Args:
            file_path (str): O caminho do arquivo de texto a ser adicionado.
            chunk_overlap (Optional[int]): Sobreposição de caracteres entre os chunks.
            chunk_size (Optional[int]): O tamanho de cada chunk de texto.

        Returns:
            bool: True se o conteúdo foi adicionado com sucesso, False caso contrário.
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Arquivo não encontrado: {file_path}")
                return False

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            if not content.strip():
                logger.warning(
                    f"Arquivo vazio ou sem conteúdo significativo: {file_path}"
                )
                return False

            overlap = (
                chunk_overlap if chunk_overlap is not None else SERVICEHUB.CHUNK_OVERLAP
            )
            size = chunk_size if chunk_size is not None else SERVICEHUB.CHUNK_SIZE
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=size,
                chunk_overlap=overlap,
                length_function=len,
                is_separator_regex=False,
            )
            chunks = text_splitter.split_text(content)
            if not chunks:
                logger.warning(f"Falha ao gerar chunks para o arquivo: {file_path}")
                return False

            docs = [
                Document(page_content=chunk, metadata={"source": file_path})
                for chunk in chunks
            ]
            self.__vectordb.add_documents(docs)
            self.__vectordb.save_local(self.__db_path)
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar arquivo ao FAISS: {e}")
            return False

    def remove_by_metadata(self, metadata_key: str, metadata_value: str) -> bool:
        """Remove documentos do armazenamento com base em metadados.

        Args:
            metadata_key (str): A chave de metadados a ser pesquisada.
            metadata_value (str): O valor de metadados a ser removido.

        Returns:
            bool: True se algum documento foi removido, False caso contrário.
        """
        try:
            matching_ids = self.__find_by_metadata(metadata_key, metadata_value)
            if not matching_ids:
                return False

            self.__vectordb.delete(matching_ids)
            self.__vectordb.save_local(self.__db_path)
            return True
        except Exception as e:
            logger.error(
                f"Erro ao remover por metadados {metadata_key}={metadata_value}: {e}"
            )
            return False
