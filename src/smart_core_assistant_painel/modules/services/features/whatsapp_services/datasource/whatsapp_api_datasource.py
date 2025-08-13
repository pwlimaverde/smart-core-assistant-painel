from urllib.parse import urljoin

import requests
from loguru import logger

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB
from smart_core_assistant_painel.modules.services.utils.types import WSDatasource
from smart_core_assistant_painel.modules.services.utils.parameters import WSParameters
from smart_core_assistant_painel.modules.services.utils.erros import (
    WhatsAppServiceError,
)


class WhatsAppAPIDataSource(WSDatasource):
    """DataSource para interagir com a API do WhatsApp através do EvolutionAPI."""

    def __call__(self, parameters: WSParameters) -> requests.Response:
        """Envia uma mensagem de texto através da API do WhatsApp."""
        # Monta a URL base
        base_url = SERVICEHUB.WHATSAPP_API_BASE_URL
        if not base_url:
            raise WhatsAppServiceError(
                "WHATSAPP_API_BASE_URL não configurada no ServiceHub"
            )

        # Monta o path para envio de mensagem
        send_text_url = SERVICEHUB.WHATSAPP_API_SEND_TEXT_URL
        if not send_text_url:
            raise WhatsAppServiceError(
                "WHATSAPP_API_SEND_TEXT_URL não configurada no ServiceHub"
            )

        url = urljoin(base_url, send_text_url.format(instance=parameters.instance))

        # Cabeçalhos
        headers = {
            "Content-Type": "application/json",
            "apikey": parameters.api_key,
        }

        # Dados da mensagem
        body = parameters.message_data

        # Realiza a requisição
        logger.info(f"Enviando mensagem para {parameters.instance}")
        response = requests.post(url, headers=headers, json=body)

        if response.status_code in [200, 201]:
            logger.info(f"Mensagem enviada com sucesso para {parameters.instance}")
            return response
        else:
            error_msg = (
                f"Erro ao enviar mensagem: {response.status_code} - {response.text}"
            )
            logger.error(error_msg)
            raise WhatsAppServiceError(error_msg)
