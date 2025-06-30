from typing import TypeAlias

from langchain.docstore.document import Document
from py_return_success_or_error import (
    Datasource,
    Empty,
    UsecaseBase,
    UsecaseBaseCallData,
)

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi, )
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
    MessageParameters,
)

WSUsecase: TypeAlias = UsecaseBaseCallData[
    Empty,
    WhatsappApi,
    MessageParameters
]
WSData: TypeAlias = Datasource[WhatsappApi, MessageParameters]

ACUsecase: TypeAlias = UsecaseBaseCallData[
    str,
    str,
    LlmParameters,
]
ACData: TypeAlias = Datasource[str, LlmParameters]

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
