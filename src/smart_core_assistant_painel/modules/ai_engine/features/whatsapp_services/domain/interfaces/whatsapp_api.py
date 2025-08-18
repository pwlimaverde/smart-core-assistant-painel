"""Interface abstrata para uma API de serviço de WhatsApp.

Este módulo define o contrato que qualquer implementação de API de WhatsApp
deve seguir, garantindo a padronização das funcionalidades de envio de
mensagens e controle do indicador de 'digitando'.

Classes:
    WhatsappApi: Uma classe base abstrata para APIs de WhatsApp.
"""
from abc import ABC, abstractmethod

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    MessageParameters,
)


class WhatsappApi(ABC):
    """Define a interface abstrata para uma API de WhatsApp.

    Esta classe serve como um modelo para implementações concretas de APIs
    de WhatsApp, exigindo que elas forneçam funcionalidades específicas.
    """

    def __init__(self, parameters: MessageParameters) -> None:
        """Inicializa a API do WhatsApp com os parâmetros necessários.

        Args:
            parameters (MessageParameters): Os parâmetros da mensagem,
                incluindo sessão, ID do chat e conteúdo.
        """
        self._parameters = parameters

    @abstractmethod
    def send_message(self) -> None:
        """Envia uma mensagem de texto."""
        pass

    @abstractmethod
    def typing(self, typing: bool) -> None:
        """Controla o indicador de 'digitando'.

        Args:
            typing (bool): True para mostrar 'digitando', False para parar.
        """
        pass
