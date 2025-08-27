"""Define apelidos de tipo e estruturas de dados para o módulo de IA.

Este módulo centraliza as definições de tipo usadas nas funcionalidades do motor
de IA, melhorando a legibilidade e a manutenção do código. Inclui apelidos
para casos de uso e fontes de dados, bem como tuplas nomeadas para estruturas
de dados específicas.
"""

from typing import Any, NamedTuple, TypeAlias

from langchain.docstore.document import Document
from py_return_success_or_error import (
    Datasource,
    Empty,
    UsecaseBase,
    UsecaseBaseCallData,
)

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.interface.analise_previa_mensagem import (
    AnalisePreviaMensagem,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.model.message_data import (
    MessageData,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
    DataMensageParameters,
    EmbeddingToTextParameters,
    GenerateEmbeddingsParameters,
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
    MessageParameters,
    SearchSimilarEmbeddingsParameters,
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
APMData: TypeAlias = Datasource[AnalisePreviaMensagem, AnalisePreviaMensagemParameters]

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

# Aliases para Embedding to Text
ETTUsecase: TypeAlias = UsecaseBase[
    str,
    EmbeddingToTextParameters,
]

# Aliases para Search Similar Embeddings
SSEUsecase: TypeAlias = UsecaseBase[
    list[dict],
    SearchSimilarEmbeddingsParameters,
]