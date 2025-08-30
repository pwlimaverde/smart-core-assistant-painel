"""Facade para os casos de uso do módulo AI Engine.

Esta classe fornece uma interface simplificada para acessar as funcionalidades
de IA do sistema, como processamento de documentos, análise de mensagens e
interação com modelos de linguagem.
"""

from py_return_success_or_error.core.return_success_or_error import ReturnSuccessOrError
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import GenerateEmbeddingsParameters
from smart_core_assistant_painel.modules.ai_engine.utils.erros import EmbeddingError
from typing import Any

from langchain.docstore.document import Document
from loguru import logger
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.services import SERVICEHUB

from ..utils.erros import (
    DataMessageError,
    DocumentError,
    LlmError,
)
from ..utils.parameters import (
    AnalisePreviaMensagemParameters,
    DataMensageParameters,
    GenerateChunksParameters,
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
    SearchSimilarEmbeddingsParameters,
)
from ..utils.types import (
    ACData,
    ACUsecase,
    APMData,
    APMTuple,
    APMUsecase,
    GCUsecase,
    GEData,
    GEUsecase,
    LDCUsecase,
    LDFData,
    LDFUsecase,
    LMDUsecase,
    SSEUsecase,
)
from .analise_conteudo.datasource.analise_conteudo_langchain_datasource import (
    AnaliseConteudoLangchainDatasource,
)
from .analise_conteudo.domain.usecase.analise_conteudo_usecase import (
    AnaliseConteudoUseCase,
)
from .analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource import (
    AnalisePreviaMensagemLangchainDatasource,
)
from .analise_previa_mensagem.domain.usecase.analise_previa_mensagem_usecase import (
    AnalisePreviaMensagemUsecase,
)
from .load_document_conteudo.domain.usecase.load_document_conteudo_usecase import (
    LoadDocumentConteudoUseCase,
)
from .load_document_file.datasource.load_document_file_datasource import (
    LoadDocumentFileDatasource,
)
from .load_document_file.domain.usecase.load_document_file_usecase import (
    LoadDocumentFileUseCase,
)
from .load_mensage_data.domain.model.message_data import MessageData
from .load_mensage_data.domain.usecase.load_mensage_data_usecase import (
    LoadMensageDataUseCase,
)
from .generate_embeddings.datasource.generate_embeddings_langchain_datasource import (
    GenerateEmbeddingsLangchainDatasource,
)
from .generate_embeddings.domain.usecase.generate_embeddings_usecase import (
    GenerateEmbeddingsUseCase,
)
from .search_similar_embeddings.domain.usecase.search_similar_embeddings_usecase import (
    SearchSimilarEmbeddingsUseCase,
)
from .generate_chunks.domain.usecase.generate_chunks_usecase import (
    GenerateChunksUseCase,
)


class FeaturesCompose:
    """Facade para os casos de uso do módulo AI Engine."""

    @staticmethod
    def load_document_conteudo(
        id: str,
        conteudo: str,
        tag: str,
        grupo: str,
    ) -> list[Document]:
        """Carrega e processa o conteúdo de um texto para treinamento.

        Args:
            id (str): Identificador único para o conteúdo.
            conteudo (str): O texto a ser processado.
            tag (str): Tag para categorização do conteúdo.
            grupo (str): Grupo ao qual o conteúdo pertence.

        Returns:
            list[Document]: Uma lista de objetos Document do Langchain.

        Raises:
            DocumentError: Se ocorrer um erro durante o processamento.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error = DocumentError("Error ao processar os dados do arquivo!")
        parameters = LoadDocumentConteudoParameters(
            id=id, conteudo=conteudo, tag=tag, grupo=grupo, error=error
        )
        usecase: LDCUsecase = LoadDocumentConteudoUseCase()
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def load_document_file(id: str, path: str, tag: str, grupo: str) -> list[Document]:
        """Carrega e processa um arquivo de documento para treinamento.

        Args:
            id (str): Identificador único para o documento.
            path (str): O caminho do arquivo a ser carregado.
            tag (str): Tag para categorização do documento.
            grupo (str): Grupo ao qual o documento pertence.

        Returns:
            list[Document]: Uma lista de objetos Document do Langchain.

        Raises:
            DocumentError: Se ocorrer um erro durante o carregamento.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error = DocumentError("Error ao processar os dados do arquivo!")
        parameters = LoadDocumentFileParameters(
            id=id, path=path, tag=tag, grupo=grupo, error=error
        )
        datasource: LDFData = LoadDocumentFileDatasource()
        usecase: LDFUsecase = LoadDocumentFileUseCase(datasource)
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def pre_analise_ia_treinamento(context: str) -> str:
        """Executa uma pré-análise em um conteúdo para treinamento de IA.

        Args:
            context (str): O conteúdo a ser analisado.

        Returns:
            str: O resultado da análise.

        Raises:
            LlmError: Se ocorrer um erro durante a comunicação com o LLM.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={"temperature": SERVICEHUB.LLM_TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_ANALISE_CONTEUDO,
            context=context,
            error=LlmError,
        )
        datasource: ACData = AnaliseConteudoLangchainDatasource()
        usecase: ACUsecase = AnaliseConteudoUseCase(datasource)
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def melhoria_ia_treinamento(context: str) -> str:
        """Solicita ao LLM uma versão melhorada de um conteúdo para treinamento.

        Args:
            context (str): O conteúdo a ser melhorado.

        Returns:
            str: A versão melhorada do conteúdo.

        Raises:
            LlmError: Se ocorrer um erro durante a comunicação com o LLM.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={"temperature": SERVICEHUB.LLM_TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_MELHORIA_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_MELHORIA_CONTEUDO,
            context=context,
            error=LlmError,
        )
        datasource: ACData = AnaliseConteudoLangchainDatasource()
        usecase: ACUsecase = AnaliseConteudoUseCase(datasource)
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def analise_previa_mensagem(
        historico_atendimento: dict[str, Any], context: str
    ) -> APMTuple:
        """Realiza análise prévia de mensagem para extrair intenção e entidades.

        Args:
            historico_atendimento (dict[str, Any]): Histórico da conversa.
            context (str): O texto da mensagem a ser analisada.

        Returns:
            APMTuple: Uma tupla contendo as intenções e entidades detectadas.

        Raises:
            LlmError: Se ocorrer um erro durante a comunicação com o LLM.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        llm_parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={"temperature": SERVICEHUB.LLM_TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM,
            context=context,
            error=LlmError,
        )
        parameters = AnalisePreviaMensagemParameters(
            historico_atendimento=historico_atendimento,
            valid_intent_types=SERVICEHUB.VALID_INTENT_TYPES,
            valid_entity_types=SERVICEHUB.VALID_ENTITY_TYPES,
            llm_parameters=llm_parameters,
            error=LlmError("Erro ao processar mensagem"),
        )
        datasource: APMData = AnalisePreviaMensagemLangchainDatasource()
        usecase: APMUsecase = AnalisePreviaMensagemUsecase(datasource)
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            logger.error(f"Erro ao analisar prévia da mensagem: {data.result}")
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def _converter_contexto(metadados: dict[str, Any]) -> str:
        """Converte metadados de mensagens multimídia para texto.

        Args:
            metadados (dict[str, Any]): Dicionário com os metadados da mensagem.

        Returns:
            str: Texto formatado representando o contexto da mensagem.
        """
        try:
            return "contexto"
        except Exception as e:
            logger.error(f"Erro ao converter contexto: {e}")
            raise e

    @staticmethod
    def load_message_data(data: dict[str, Any]) -> MessageData:
        """Carrega e processa os dados de uma mensagem de webhook.

        Args:
            data (dict[str, Any]): O payload do webhook.

        Returns:
            MessageData: Um objeto com os dados da mensagem normalizados.

        Raises:
            DataMessageError: Se ocorrer um erro ao processar os dados.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error = DataMessageError("Error ao processar os dados da mensagem!")
        parameters = DataMensageParameters(data=data, error=error)
        usecase: LMDUsecase = LoadMensageDataUseCase()
        message_data = usecase(parameters)

        if isinstance(message_data, SuccessReturn):
            result: MessageData = message_data.result
            if result.metadados:
                conteudo_media: str = FeaturesCompose._converter_contexto(
                    result.metadados
                )
                if conteudo_media and conteudo_media != "contexto":
                    result.conteudo = f"{result.conteudo}\n{conteudo_media}"
            return result
        elif isinstance(message_data, ErrorReturn):
            raise message_data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def mensagem_apresentacao() -> None:
        """Envia uma mensagem de apresentação da empresa."""
        pass

    @staticmethod
    def solicitacao_info_cliene() -> None:
        """Envia uma mensagem para coleta de informações do cliente."""
        pass

    @staticmethod
    def resumo_atendimento() -> None:
        """Envia uma mensagem de resumo do atendimento."""
        pass

    @staticmethod
    def generate_embeddings(text: str) -> list[float]:
        """Gera embeddings para um texto.

        Args:
            text (str): Texto para gerar embeddings.

        Returns:
            list[float]: Vetor de embeddings gerado.

        Raises:
            EmbeddingError: Se ocorrer um erro durante a geração.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error: EmbeddingError = EmbeddingError("Erro ao gerar embeddings!")
        parameters: GenerateEmbeddingsParameters = GenerateEmbeddingsParameters(text=text, error=error)
        datasource: GEData = GenerateEmbeddingsLangchainDatasource()
        usecase: GEUsecase = GenerateEmbeddingsUseCase(datasource)
        data: ReturnSuccessOrError[list[float]] = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def search_similar_embeddings(
        query_embedding: list[float],
        embeddings_data: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """Busca embeddings similares ao embedding de consulta.

        Args:
            query_embedding (list[float]): Embedding da consulta.
            embeddings_data (list[dict]): Dados com embeddings para busca.
            top_k (int): Número de resultados a retornar.

        Returns:
            list[dict]: Lista ordenada por similaridade.

        Raises:
            EmbeddingError: Se ocorrer um erro durante a busca.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error = EmbeddingError("Erro ao buscar embeddings similares!")
        parameters = SearchSimilarEmbeddingsParameters(
            query_embedding=query_embedding,
            embeddings_data=embeddings_data,
            top_k=top_k,
            error=error,
        )
        usecase: SSEUsecase = SearchSimilarEmbeddingsUseCase()
        data = usecase(parameters)
        
        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def generate_chunks() -> None:
        error = DocumentError("Erro ao gerar chunks do conteúdo!")
        parameters = GenerateChunksParameters(
            error=error,
        )
        datasource: GEData = GenerateEmbeddingsLangchainDatasource()
        usecase: GEUsecase = GenerateEmbeddingsUseCase(datasource)
        data: ReturnSuccessOrError[list[float]] = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")
