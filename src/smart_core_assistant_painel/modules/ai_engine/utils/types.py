"""Define apelidos de tipo e estruturas de dados para o módulo de IA.

Este módulo centraliza as definições de tipo usadas nas funcionalidades do motor
de IA, melhorando a legibilidade e a manutenção do código. Inclui apelidos
para casos de uso e fontes de dados, bem como tuplas nomeadas para estruturas
de dados específicas.
"""

from typing import Any, NamedTuple, Optional, TypeAlias

from langchain_core.documents import Document
from py_return_success_or_error import (
    Datasource,
    UsecaseBase,
    UsecaseBaseCallData,
)
from pydantic import BaseModel, Field

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.interface.analise_previa_mensagem import (
    AnalisePreviaMensagem,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.model.message_data import (
    MessageData,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseAvaliacaoParameters,
    AnaliseMensageParameters,
    AnalisePreviaMensagemParameters,
    DataMensageParameters,
    GenerateChunksParameters,
    GenerateEmbeddingsParameters,
    InterpretMediaParameters,
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
    SearchSimilarEmbeddingsParameters,
    TranscribeAudioParameters,
)

ACUsecase: TypeAlias = UsecaseBaseCallData[
    str,
    str,
    LlmParameters,
]
ACData: TypeAlias = Datasource[str, LlmParameters]


class APMTuple(NamedTuple):
    """Tupla nomeada para dados de Análise Prévia de Mensagem.

    Attributes:
        intent_types (list[dict[str, Any]]): Lista de tipos de intenção válidos
            com suas configurações.
        entity_types (list[dict[str, Any]]): Lista de tipos de entidade válidos
            com suas configurações.
    """

    intent_types: list[dict[str, Any]]
    entity_types: list[dict[str, Any]]


APMUsecase: TypeAlias = UsecaseBaseCallData[
    APMTuple,
    AnalisePreviaMensagem,
    AnalisePreviaMensagemParameters,
]
APMData: TypeAlias = Datasource[
    AnalisePreviaMensagem, AnalisePreviaMensagemParameters
]

LDFUsecase: TypeAlias = UsecaseBaseCallData[
    list[Document],
    list[Document],
    LoadDocumentFileParameters,
]
LDFData: TypeAlias = Datasource[list[Document], LoadDocumentFileParameters]

LDCUsecase: TypeAlias = UsecaseBase[
    list[Document],
    LoadDocumentConteudoParameters,
]

LMDUsecase: TypeAlias = UsecaseBase[
    MessageData,
    DataMensageParameters,
]

# Aliases para Generate Embeddings
GEUsecase: TypeAlias = UsecaseBaseCallData[
    list[float],
    list[float],
    GenerateEmbeddingsParameters,
]
GEData: TypeAlias = Datasource[list[float], GenerateEmbeddingsParameters]

# Aliases para Search Similar Embeddings
SSEUsecase: TypeAlias = UsecaseBase[
    list[dict[str, Any]],
    SearchSimilarEmbeddingsParameters,
]

# Aliases para Generate Chunks
GCUsecase: TypeAlias = UsecaseBase[
    list[Document],
    GenerateChunksParameters,
]


class AMTuple(NamedTuple):
    """Tupla nomeada para dados de Análise de Mensagem.

    Attributes:
        resposta_bot: Texto da resposta gerada pelo bot.
        confiabilidade: Score de confiança da resposta (0.0 a 1.0).
        transferir_atendimento: Se o atendimento deve ser transferido.
        fluxo_transferencia: Nome do setor/fluxo para transferência.
    """

    resposta_bot: str
    confiabilidade: float
    transferir_atendimento: bool
    fluxo_transferencia: str


class RespostaBot(BaseModel):
    """Modelo Pydantic para Structured Output do LLM.

    Usado com `llm.with_structured_output(RespostaBot)` para extrair
    respostas estruturadas diretamente do modelo de linguagem,
    eliminando a necessidade de parsing por regex.

    Attributes:
        resposta_texto: Texto da resposta para o usuário.
        acao_transferencia: Nome do setor para transferência (se aplicável).
        confianca: Score de confiança da resposta (0.0 a 1.0).
    """

    resposta_texto: str = Field(
        description="Resposta completa e educada para o usuário final"
    )
    acao_transferencia: Optional[str] = Field(
        default=None,
        description=(
            "Nome EXATO do setor para transferência. "
            "Preencha apenas se for necessário transferir o atendimento. "
            "Use o nome conforme listado nos setores disponíveis."
        ),
    )
    confianca: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Score de confiança da resposta (0.0 a 1.0)",
    )


AMData: TypeAlias = Datasource[str, AnaliseMensageParameters]
AMUsecase: TypeAlias = UsecaseBaseCallData[
    str,
    str,
    AnaliseMensageParameters,
]


class AnaliseAvaliacao(BaseModel):
    """Modelo Pydantic para Structured Output da análise de avaliação."""

    nota: int = Field(
        description="Nota de avaliação numérica convertida para escala 1-5"
    )
    sentimento: str = Field(
        description="Sentimento do cliente (positivo, negativo, neutro)"
    )
    feedback_original: Optional[str] = Field(
        description="Texto original do feedback, se houver", default=None
    )


AAUsecase: TypeAlias = UsecaseBaseCallData[
    AnaliseAvaliacao,
    AnaliseAvaliacao,
    AnaliseAvaliacaoParameters,
]
AAData: TypeAlias = Datasource[AnaliseAvaliacao, AnaliseAvaliacaoParameters]


class MediaAnalysis(BaseModel):
    """Modelo Pydantic para Structured Output da análise de mídia.

    Usado com `llm.with_structured_output(MediaAnalysis)`. Separa o que é
    contexto interno do bot (``analise``) do que é exibido ao atendente
    (``resumo``).

    Attributes:
        analise: Descrição/transcrição COMPLETA do conteúdo da mídia,
            usada como contexto para compor a resposta do bot.
        resumo: Resumo geral curto e amigável do que se trata a mídia,
            exibido ao atendente no chat.
    """

    analise: str = Field(
        description=(
            "Descrição/transcrição completa e detalhada do conteúdo da "
            "mídia, em português. Para áudio: a transcrição literal. Para "
            "imagem/vídeo: descrição detalhada (elementos, textos visíveis, "
            "contexto). Para documento: o conteúdo textual organizado."
        )
    )
    resumo: str = Field(
        default="",
        description=(
            "Resumo geral curto (1-3 frases), em português, do que se trata "
            "a mídia — para exibir ao atendente."
        ),
    )


# Aliases para Interpret Media (imagem/vídeo/documento)
IMData: TypeAlias = Datasource[MediaAnalysis, InterpretMediaParameters]
IMUsecase: TypeAlias = UsecaseBaseCallData[
    MediaAnalysis,
    MediaAnalysis,
    InterpretMediaParameters,
]


# Aliases para Transcribe Audio
TAData: TypeAlias = Datasource[MediaAnalysis, TranscribeAudioParameters]
TAUsecase: TypeAlias = UsecaseBaseCallData[
    MediaAnalysis,
    MediaAnalysis,
    TranscribeAudioParameters,
]
