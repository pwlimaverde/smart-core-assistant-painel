from abc import ABC, abstractmethod
from typing import Dict, Any
from py_return_success_or_error import ReturnSuccessOrError
import requests


class WhatsAppServiceInterface(ABC):
    """Interface para o serviço de WhatsApp."""

    @abstractmethod
    def send_message(
        self, instance: str, api_key: str, message_data: Dict[str, Any]
    ) -> ReturnSuccessOrError[requests.Response]:
        """Envia uma mensagem de texto através da API do WhatsApp."""
        pass
