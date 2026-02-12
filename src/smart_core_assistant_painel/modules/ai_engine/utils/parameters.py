"""Define dataclasses e classes para os parâmetros do motor de IA.

Este módulo contém as estruturas de dados que encapsulam os parâmetros
necessários para as várias funcionalidades do motor de IA, como processamento
de mensagens, carregamento de documentos e interação com modelos de linguagem.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from langchain_core.language_models.chat_models import BaseChatModel
from loguru import logger
from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    AnaliseAvaliacaoError,
    AnaliseMensageError,
    DataMessageError,
    DocumentError,
    EmbeddingError,
    LlmError,
    TranscribeAudioError,
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
        error (LlmError): Instância de erro a ser usada em caso de falha.
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
        error: LlmError,
        prompt_system: str,
        prompt_human: str,
        context: str,
        extra_params: Optional[Dict[str, Any]] = None,
    ):
        """Inicializa os parâmetros do LLM.

        Args:
            llm_class (Type[BaseChatModel]): A classe do modelo de linguagem.
            model (str): O nome do modelo a ser usado.
            error (LlmError): Instância de erro a ser usada.
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
        try:
            return self.__llm_class(**params)
        except Exception as e:
            # Log seguro: nunca exibe o valor de nenhuma chave/token.
            safe_params: Dict[str, Any] = {}
            for k, v in params.items():
                if "key" in k.lower() or "token" in k.lower():
                    safe_params[k] = "***"
                else:
                    safe_params[k] = v
            logger.error(
                "Falha ao criar LLM "
                f"(class={getattr(self.__llm_class, '__name__', str(self.__llm_class))}, "
                f"params={safe_params}). "
                f"Tipo={type(e).__name__}, Mensagem={e}"
            )
            raise

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
        embeddings_data (list[dict[str, Any]]): Lista de dados com embeddings para busca.
        top_k (int): Número máximo de resultados a retornar.
        error (EmbeddingError): O erro a ser levantado em caso de falha.
    """

    query_embedding: list[float]
    embeddings_data: list[dict[str, Any]]
    top_k: int = 5
    error: EmbeddingError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class GenerateChunksParameters(ParametersReturnResult):
    """Parâmetros para geração de chunks a partir de conteúdo.

    Attributes:
        conteudo (str): Conteúdo de texto para ser dividido em chunks.
        metadata (dict[str, Any]): Metadados a serem associados aos chunks.
        error (DocumentError): O erro a ser levantado em caso de falha.
    """

    conteudo: str
    metadata: dict[str, Any]
    error: DocumentError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class TranscribeAudioParameters(ParametersReturnResult):
    """Parâmetros para transcrição de áudio.

    Attributes:
        audio_url: URL do arquivo de áudio.
        mimetype: Tipo MIME do áudio.
        language: Código do idioma para transcrição.
        error: Erro a ser levantado em caso de falha.
    """

    audio_url: str
    mimetype: str
    error: TranscribeAudioError
    language: str = "pt"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class AnaliseMensageParameters(ParametersReturnResult):
    """Parâmetros para análise de mensagem com ChatPromptTemplate multi-turn.

    Attributes:
        fluxos_disponiveis: Dicionário com fluxos disponíveis para
            transferência.
        chat_history: Lista de BaseMessage (HumanMessage/AIMessage) com o
            histórico da conversa estruturado para LangChain.
        dados_contexto: Dicionário com entidades extraídas, intents detectados
            e histórico de atendimentos anteriores.
        dados_empresa: Texto com dados da empresa para RAG.
        dados_treinamento: Texto com dados de treinamento para RAG.
        llm_parameters: Parâmetros do LLM.
        error: Erro a ser levantado em caso de falha.
    """

    fluxos_disponiveis: dict[str, str]
    chat_history: list[Any]  # list[BaseMessage] - Any para evitar import
    dados_contexto: dict[str, Any]
    dados_empresa: str
    dados_treinamento: str
    llm_parameters: LlmParameters
    error: AnaliseMensageError

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class AnaliseAvaliacaoParameters(ParametersReturnResult):
    """Parâmetros para e a feature de análise de avaliação.

    Attributes:
        chat_history: Histórico da conversa (LangChain format).
        llm_parameters: Parâmetros do LLM.
        error: Erro a ser levantado em caso de falha.
    """

    chat_history: list[Any]
    llm_parameters: LlmParameters
    error: AnaliseAvaliacaoError

    def __str__(self) -> str:
        return self.__repr__()
