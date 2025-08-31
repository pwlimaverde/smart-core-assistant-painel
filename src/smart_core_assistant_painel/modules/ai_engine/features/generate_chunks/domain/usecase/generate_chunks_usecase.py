"""UseCase para geração de chunks a partir de conteúdo de texto.

Este módulo contém a implementação do caso de uso para divisão de texto
em chunks utilizando o RecursiveCharacterTextSplitter do LangChain.
"""




from langchain_core.documents.base import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from py_return_success_or_error import (
    ReturnSuccessOrError,
    SuccessReturn,
    ErrorReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    GenerateChunksParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import GCUsecase
from smart_core_assistant_painel.modules.services import SERVICEHUB


class GenerateChunksUseCase(GCUsecase):
    """Use case para gerar chunks a partir de conteúdo de texto.

    Esta classe processa um texto e o divide em chunks menores usando
    o RecursiveCharacterTextSplitter do LangChain, aplicando as configurações
    de chunk_size e chunk_overlap do ServiceHub.
    """

    def __call__(
        self, parameters: GenerateChunksParameters
    ) -> ReturnSuccessOrError[list[Document]]:
        """Executa o caso de uso de geração de chunks.

        Args:
            parameters (GenerateChunksParameters): Os parâmetros necessários
                para gerar chunks, incluindo o conteúdo e metadados.

        Returns:
            ReturnSuccessOrError[List[Document]]: Um objeto de retorno que
                contém a lista de documentos em chunks em caso de sucesso
                (SuccessReturn) ou um `AppError` em caso de falha
                (ErrorReturn).
        """
        try:
            # Valida se o conteúdo não está vazio
            if not parameters.conteudo or not parameters.conteudo.strip():
                error = parameters.error
                error.message = f"{error.message} - Conteúdo não pode estar vazio para geração de chunks"
                return ErrorReturn(error)

            # Cria documento temporário para chunking
            temp_document = Document(
                page_content=parameters.conteudo,
                metadata=parameters.metadata
            )
            
            # Configura o splitter com as configurações do ServiceHub
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=SERVICEHUB.CHUNK_SIZE, 
                chunk_overlap=SERVICEHUB.CHUNK_OVERLAP
            )
            
            # Gera os chunks
            chunks = splitter.split_documents(documents=[temp_document])
            
            return SuccessReturn(chunks)
            
        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)