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
from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
    DataMensageParameters,
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
    MessageParameters,
)

WSUsecase: TypeAlias = UsecaseBaseCallData[Empty, WhatsappApi, MessageParameters]
WSData: TypeAlias = Datasource[WhatsappApi, MessageParameters]

ACUsecase: TypeAlias = UsecaseBaseCallData[
    str,
    str,
    LlmParameters,
]
ACData: TypeAlias = Datasource[str, LlmParameters]


class APMTuple(NamedTuple):
    """Tupla nomeada para dados de Análise Prévia de Mensagem.

    Attributes:
        intent_types: Lista de tipos de intent válidos com suas configurações
        entity_types: Lista de tipos de entidade válidos com suas configurações
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
