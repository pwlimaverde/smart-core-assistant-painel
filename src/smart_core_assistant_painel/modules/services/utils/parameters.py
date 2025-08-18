"""Define dataclasses para os parâmetros relacionados a serviços.

Este módulo contém dataclasses que estruturam os parâmetros necessários
para diferentes serviços, garantindo segurança de tipo e clareza.
"""
from dataclasses import dataclass
from typing import Any, Dict

from py_return_success_or_error import ParametersReturnResult

from smart_core_assistant_painel.modules.services.utils.erros import (
    SetEnvironRemoteError,
    WhatsAppServiceError,
)


@dataclass
class SetEnvironRemoteParameters(ParametersReturnResult):
    """Parâmetros para configurar variáveis de ambiente remotas.

    Attributes:
        config_mapping (dict[str, str]): Um dicionário que mapeia os nomes
            das variáveis de ambiente para suas chaves correspondentes no
            serviço de configuração remota.
        error (SetEnvironRemoteError): O erro a ser levantado se a
            operação falhar.
    """

    config_mapping: dict[str, str]
    error: SetEnvironRemoteError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class WhatsAppMensagemParameters(ParametersReturnResult):
    """Parâmetros para o envio de mensagens via WhatsApp.

    Attributes:
        instance (str): O identificador da instância do WhatsApp.
        api_key (str): A chave de API para autenticação com o serviço.
        message_data (Dict[str, Any]): O payload da mensagem a ser enviada.
        error (WhatsAppServiceError): O erro a ser levantado se a
            operação falhar.
    """

    instance: str
    api_key: str
    message_data: Dict[str, Any]
    error: WhatsAppServiceError

    def __str__(self) -> str:
        """Retorna uma representação simplificada em string da instância."""
        return f"WhatsAppServiceParameters(instance={self.instance})"
