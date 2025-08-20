"""
Este módulo centraliza e expõe os principais serviços e configurações
da aplicação, simplificando o acesso e a inicialização de componentes
essenciais como o ServiceHub, armazenamento de vetores e comunicação
com o WhatsApp.
"""
from .features.features_compose import FeaturesCompose
from .features.service_hub import SERVICEHUB, ServiceHub
from .start_services import start_services
from .utils.erros import (
    SetEnvironRemoteError,
    VetorStorageError,
    WhatsAppServiceError,
)
from .utils.parameters import (
    SetEnvironRemoteParameters,
    WhatsAppMensagemParameters,
)
from .utils.types import (
    SERData,
    SERUsecase,
    VSData,
    VSUsecase,
    WSData,
    WSUsecase,
)

__all__ = [
    # Facade
    "FeaturesCompose",
    # Service Hub
    "ServiceHub",
    "SERVICEHUB",
    # Start Services
    "start_services",
    # Erros
    "SetEnvironRemoteError",
    "WhatsAppServiceError",
    "VetorStorageError",
    # Parameters
    "SetEnvironRemoteParameters",
    "WhatsAppMensagemParameters",
    # Types
    "SERUsecase",
    "SERData",
    "VSUsecase",
    "VSData",
    "WSUsecase",
    "WSData",
]
