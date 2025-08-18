import os
from abc import ABCMeta
from pathlib import Path
from typing import Any, Dict, List

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings  # Exposto para testes
from loguru import logger
from pydantic import ValidationError

from smart_core_assistant_painel.modules.services.features.service_hub import (
    SERVICEHUB,
)
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
        # Cria embeddings usando argumentos nomeados para evitar erro
        # "BaseModel.__init__() takes 1 positional argument but 2 were given"
        # em classes baseadas em Pydantic. Tentamos 'model_name' (HF*) e
        # fazemos fallback para 'model' (Ollama), sem usar posicional.
        self.__embeddings = self.__create_embeddings()
        self.__vectordb = self.__inicializar_banco_vetorial()
        self._initialized = True

    def __create_embeddings(self) -> Any:
        """Cria instância de embeddings conforme classe configurada.

        Tenta primeiro com 'model_name' (padrão das classes HuggingFace*) e
        depois com 'model' (padrão do OllamaEmbeddings), evitando passar
        argumentos posicionais para classes baseadas em Pydantic.
        """
        emb_cls = SERVICEHUB.EMBEDDINGS_CLASS
        model = SERVICEHUB.EMBEDDINGS_MODEL
        api_key = SERVICEHUB.HUGGINGFACE_API_KEY

        # 1) Tenta assinatura Hugging Face com api_key padrão
        if api_key:
            try:
                return emb_cls(  # type: ignore[call-arg]
                    model_name=model,
                    api_key=api_key,
                )
            except (TypeError, ValidationError):
                # 2) Fallback: algumas libs usam 'huggingfacehub_api_token'
                try:
                    return emb_cls(  # type: ignore[call-arg]
                        model_name=model,
                        huggingfacehub_api_token=api_key,
                    )
                except (TypeError, ValidationError):
                    # 3) Tenta sem chave (pode ser pública/local)
                    try:
                        return emb_cls(  # type: ignore[call-arg]
                            model_name=model,
                        )
                    except (TypeError, ValidationError):
                        pass
        else:
            # Sem chave definida, tenta somente com 'model_name'
            try:
                return emb_cls(model_name=model)  # type: ignore[call-arg]
            except (TypeError, ValidationError):
                pass

        # 4) Fallback geral: assinatura com 'model' (ex.: OllamaEmbeddings)
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

    def __find_by_metadata(
        self, metadata_key: str, metadata_value: str
    ) -> List[str]:
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

            # Pós-processamento para garantir que os resultados são Document
            if not results:
                return []

            documentos: List[Document] = []
            for doc in results:
                if isinstance(doc, Document):
                    documentos.append(doc)
                else:
                    # fallback defensivo para estruturas inesperadas
                    try:
                        documentos.append(
                            Document(
                                page_content=getattr(doc, "page_content", ""),
                                metadata=getattr(doc, "metadata", {}),
                            )
                        )
                    except Exception as e:
                        logger.warning(
                            "Documento retornado não é instância de Document "
                            f"e não pôde ser convertido. Erro: {e}"
                        )

            return documentos

        except Exception as e:
            logger.error(f"Erro na leitura de embeddings FAISS: {e}")
            return []

    def write(self, documents: list[Document]) -> None:
        """Adiciona documentos ao armazenamento vetorial e persiste no disco.

        Comentários:
            - Garante robustez convertendo entradas não-Document quando
              possível e ignorando inválidos.
            - Sincroniza o banco antes de escrever para refletir mudanças
              externas.
        """
        # Sincroniza para refletir alterações externas antes de escrever
        self.__sync_vectordb()

        if not documents:
            # Teste espera ValueError para listas vazias
            raise ValueError("Lista de documentos vazia.")

        # Normaliza entradas para instâncias de Document
        docs: list[Document] = []
        for item in documents:
            if isinstance(item, Document):
                docs.append(item)
            else:
                # Fallback defensivo para objetos similares
                try:
                    docs.append(
                        Document(
                            page_content=getattr(item, "page_content", ""),
                            metadata=getattr(item, "metadata", {}),
                        )
                    )
                except Exception as conv_err:  # noqa: BLE001
                    logger.warning(
                        "Documento inválido ignorado em write(): %s",
                        conv_err,
                    )

        if not docs:
            # Não há nenhum documento válido para processar
            raise ValueError("Nenhum chunk válido encontrado")

        # Realiza o chunking conforme configuração do SERVICEHUB
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
                chunk_text = chunk.strip()
                if not chunk_text:
                    continue
                chunked_docs.append(
                    Document(page_content=chunk_text, metadata=doc.metadata)
                )

        if not chunked_docs:
            # Teste espera mensagem específica
            raise ValueError("Nenhum chunk válido encontrado")

        try:
            self.__vectordb.add_documents(chunked_docs)
            self.__vectordb.save_local(self.__db_path)
        except Exception as e:  # noqa: BLE001
            # Teste verifica mensagem de erro amigável
            raise ValueError(
                f"Erro ao adicionar documentos ao banco FAISS: {e}"
            ) from e

    def add_from_file(self, file_path: str, chunk_overlap: int | None = None,
                      chunk_size: int | None = None) -> bool:
        """
        Adiciona o conteúdo de um arquivo de texto ao armazenamento FAISS.

        Args:
            file_path: Caminho do arquivo de texto a ser adicionado
            chunk_overlap: Sobreposição de caracteres entre chunks
            chunk_size: Tamanho de cada chunk de texto

        Returns:
            True se o conteúdo foi adicionado com sucesso, False caso contrário
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

            # Configuração de chunking dinâmica com fallbacks
            overlap = (
                chunk_overlap if chunk_overlap is not None else SERVICEHUB.CHUNK_OVERLAP
            )
            size = (
                chunk_size if chunk_size is not None else SERVICEHUB.CHUNK_SIZE
            )

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=size,
                chunk_overlap=overlap,
                length_function=len,
                is_separator_regex=False,
            )

            chunks = text_splitter.split_text(content)
            if not chunks:
                logger.warning(
                    f"Falha ao gerar chunks para o arquivo: {file_path}"
                )
                return False

            docs = [
                Document(
                    page_content=chunk,
                    metadata={"source": file_path},
                )
                for chunk in chunks
            ]

            self.__vectordb.add_documents(docs)
            self.__vectordb.save_local(self.__db_path)

            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar arquivo ao FAISS: {e}")
            return False

    def remove_by_metadata(self, metadata_key: str, metadata_value: str) -> bool:
        """
        Remove documentos do armazenamento com base em metadados.

        Args:
            metadata_key: Chave do metadado para busca
            metadata_value: Valor do metadado a ser removido

        Returns:
            True se algum documento foi removido, False caso contrário
        """
        try:
            matching_ids = self.__find_by_metadata(metadata_key, metadata_value)
            if not matching_ids:
                return False

            # Remoção direta via API do VectorStore e persistência
            try:
                self.__vectordb.delete(matching_ids)
                self.__vectordb.save_local(self.__db_path)
            except Exception as e:
                logger.error(
                    f"Erro ao excluir documentos {matching_ids} no FAISS: {e}"
                )
                return False

            return True

        except Exception as e:
            logger.error(
                f"Erro ao remover por metadados {metadata_key}={metadata_value}: {e}"
            )
            return False
