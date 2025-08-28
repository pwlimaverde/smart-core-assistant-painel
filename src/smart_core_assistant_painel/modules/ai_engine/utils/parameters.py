"""Define dataclasses e classes para os parâmetros do motor de IA.

Este módulo contém as estruturas de dados que encapsulam os parâmetros
necessários para as várias funcionalidades do motor de IA, como processamento
de mensagens, carregamento de documentos e interação com modelos de linguagem.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel
from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DataMessageError,
    DocumentError,
    EmbeddingError,
    LlmError,
)


@dataclass
class DataMensageParameters(ParametersReturnResult):
    """Parâmetros para manipulação de dados de mensagens.

    Attributes:
        data (dict[str, Any]): Os dados da mensagem.
        error (DataMessageError): O erro a ser levantado em caso de falha.
    """

    data: dict[str, Any]
    error: DataMessageError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class LoadDocumentFileParameters(ParametersReturnResult):
    """Parâmetros para o carregamento de um documento a partir de um arquivo.

    Attributes:
        id (str): O ID do documento.
        path (str): O caminho do arquivo a ser carregado.
        tag (str): A tag associada ao documento.
        grupo (str): O grupo ao qual o documento pertence.
        error (DocumentError): O erro a ser levantado em caso de falha.
    """

    id: str
    path: str
    tag: str
    grupo: str
    error: DocumentError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class LoadDocumentConteudoParameters(ParametersReturnResult):
    """Parâmetros para o carregamento de um documento a partir de seu conteúdo.

    Attributes:
        id (str): O ID do documento.
        conteudo (str): O conteúdo do documento.
        tag (str): A tag associada ao documento.
        grupo (str): O grupo ao qual o documento pertence.
        error (DocumentError): O erro a ser levantado em caso de falha.
    """

    id: str
    conteudo: str
    tag: str
    grupo: str
    error: DocumentError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


class LlmParameters(ParametersReturnResult):
    """Parâmetros para interação com um modelo de linguagem (LLM).

    Esta classe encapsula todas as configurações necessárias para instanciar e
    usar um modelo de linguagem, incluindo a classe do modelo, prompts e
    parâmetros extras.

    Attributes:
        prompt_system (str): O prompt de sistema para o LLM.
        prompt_human (str): O prompt humano para o LLM.
        context (str): O contexto a ser fornecido ao LLM.
        error (Type[LlmError]): O tipo de erro a ser levantado em caso de falha.
    """

    __slots__ = [
        "__llm_class",
        "__model",
        "__extra_params",
        "prompt_system",
        "prompt_human",
        "context",
        "error",
    ]

    def __init__(
        self,
        llm_class: Type[BaseChatModel],
        model: str,
        error: Type[LlmError],
        prompt_system: str,
        prompt_human: str,
        context: str,
        extra_params: Optional[Dict[str, Any]] = None,
    ):
        """Inicializa os parâmetros do LLM.

        Args:
            llm_class (Type[BaseChatModel]): A classe do modelo de linguagem.
            model (str): O nome do modelo a ser usado.
            error (Type[LlmError]): O tipo de erro a ser levantado.
            prompt_system (str): O prompt de sistema.
            prompt_human (str): O prompt humano.
            context (str): O contexto.
            extra_params (Optional[Dict[str, Any]]): Parâmetros extras para o
                modelo.
        """
        self.error = error
        self.__llm_class = llm_class
        self.__model = model
        self.__extra_params = extra_params
        self.prompt_system = prompt_system
        self.prompt_human = prompt_human
        self.context = context

    @property
    def create_llm(self) -> BaseChatModel:
        """Cria uma instância do LLM com os parâmetros configurados.

        Returns:
            BaseChatModel: Uma instância do modelo de linguagem.
        """
        params = self.__get_params()
        return self.__llm_class(**params)

    def __get_params(self) -> Dict[str, Any]:
        """Retorna os parâmetros como um dicionário.

        Returns:
            Dict[str, Any]: Um dicionário contendo os parâmetros do modelo.
        """
        params = {"model": self.__model}

        if self.__extra_params:
            params.update(self.__extra_params)

        return params

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class AnalisePreviaMensagemParameters(ParametersReturnResult):
    """Parâmetros para a análise prévia de uma mensagem.

    Attributes:
        historico_atendimento (dict[str, Any]): O histórico de atendimento
            associado à mensagem.
        valid_intent_types (str): Os tipos de intenção válidos.
        valid_entity_types (str): Os tipos de entidade válidos.
        llm_parameters (LlmParameters): Os parâmetros para o LLM.
        error (LlmError): O erro a ser levantado em caso de falha.
    """

    historico_atendimento: dict[str, Any]
    valid_intent_types: str
    valid_entity_types: str
    llm_parameters: LlmParameters
    error: LlmError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class GenerateEmbeddingsParameters(ParametersReturnResult):
    """Parâmetros para geração de embeddings.

    Attributes:
        text (str): Texto para o qual gerar o embedding.
        error (EmbeddingError): O erro a ser levantado em caso de falha.
    """

    text: str
    error: EmbeddingError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()



@dataclass
class SearchSimilarEmbeddingsParameters(ParametersReturnResult):
    """Parâmetros para busca por similaridade de embeddings.

    Attributes:
        query_embedding (list[float]): Vetor de embedding da consulta.
        embeddings_data (list[dict]): Lista de dados com embeddings para busca.
        top_k (int): Número máximo de resultados a retornar.
        error (EmbeddingError): O erro a ser levantado em caso de falha.
    """

    query_embedding: list[float]
    embeddings_data: list[dict]
    top_k: int = 5
    error: EmbeddingError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()
