"""Este módulo centraliza e expõe as principais funcionalidades e tipos de dados
do motor de Inteligência Artificial (AI Engine) do sistema.

A `FeaturesCompose` atua como uma fachada (Facade) para todos os casos de uso
relacionados à IA, simplificando a interação com outras partes do sistema.

Os erros customizados, parâmetros e tipos de dados também são expostos
para garantir uma comunicação clara e robusta entre os módulos.
"""

from .features.features_compose import FeaturesCompose
from .features.load_mensage_data.domain.model.message_data import (
    MessageData,
)
from .utils.erros import (
    DataMessageError,
    DocumentError,
    HtmlStrError,
    LlmError,
    TranscribeAudioError,
)
from .utils.parameters import (
    AnalisePreviaMensagemParameters,
    DataMensageParameters,
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
    TranscribeAudioParameters,
)
from .utils.types import (
    ACData,
    ACUsecase,
    AMTuple,
    APMData,
    APMTuple,
    APMUsecase,
    LDCUsecase,
    LDFData,
    LDFUsecase,
    LMDUsecase,
    TAData,
    TAUsecase,
)

__all__ = [
    # Facade
    "FeaturesCompose",
    # Erros
    "DataMessageError",
    "DocumentError",
    "HtmlStrError",
    "LlmError",
    "TranscribeAudioError",
    # Parameters
    "AnalisePreviaMensagemParameters",
    "DataMensageParameters",
    "LlmParameters",
    "LoadDocumentConteudoParameters",
    "LoadDocumentFileParameters",
    "TranscribeAudioParameters",
    "MessageData",
    # Types
    "ACData",
    "ACUsecase",
    "APMData",
    "APMTuple",
    "APMUsecase",
    "AMTuple",
    "LDCUsecase",
    "LDFData",
    "LDFUsecase",
    "LMDUsecase",
    "TAData",
    "TAUsecase",
]
