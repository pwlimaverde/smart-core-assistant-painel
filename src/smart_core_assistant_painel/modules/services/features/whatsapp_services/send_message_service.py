from typing import Dict, Any
import requests

from py_return_success_or_error import ReturnSuccessOrError

from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.whatsapp_api_datasource import (
    WhatsAppAPIDataSource,
)
from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.usecase.whatsapp_send_message_usecase import (
    WhatsAppSendMessageUseCase,
)
from smart_core_assistant_painel.modules.services.utils.parameters import WSParameters
from smart_core_assistant_painel.modules.services.utils.types import WSDatasource
from smart_core_assistant_painel.modules.services.utils.erros import (
    WhatsAppServiceError,
)


def send_whatsapp_message(
    instance: str, api_key: str, message_data: Dict[str, Any]
) -> ReturnSuccessOrError[requests.Response]:
    """
    Função de alto nível para enviar mensagem via WhatsApp.

    Args:
        instance: Nome da instância do WhatsApp
        api_key: Chave de API para autenticação
        message_data: Dados da mensagem a ser enviada

    Returns:
        Resultado do envio da mensagem
    """
    # Cria os parâmetros
    parameters = WSParameters(
        instance=instance,
        api_key=api_key,
        message_data=message_data,
        error=WhatsAppServiceError("Erro no envio de mensagem WhatsApp"),
    )

    # Cria o datasource e usecase
    datasource: WSDatasource = WhatsAppAPIDataSource()
    usecase = WhatsAppSendMessageUseCase(datasource=datasource)

    # Executa o caso de uso
    result = usecase(parameters)

    return result
