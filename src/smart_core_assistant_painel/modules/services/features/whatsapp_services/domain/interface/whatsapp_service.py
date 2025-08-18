"""Interface abstrata para um serviço de mensagens do WhatsApp.

Este módulo define o contrato que qualquer implementação de serviço de WhatsApp
deve seguir, garantindo que funcionalidades essenciais como o envio de mensagens
e o gerenciamento de indicadores de digitação sejam padronizadas em toda a
aplicação.

Classes:
    WhatsAppService: Uma classe base abstrata para serviços de WhatsApp.
"""

from abc import ABC, abstractmethod


class WhatsAppService(ABC):
    """Define a interface abstrata para um serviço de WhatsApp.

    Esta classe serve como um modelo para implementações concretas de serviços
    de WhatsApp, exigindo que elas forneçam funcionalidades específicas.
    """

    @abstractmethod
    def send_message(
        self,
        instance: str,
        api_key: str,
        number: str,
        text: str,
    ) -> None:
        """Envia uma mensagem de texto para um número especificado.

        Args:
            instance (str): O identificador da instância do WhatsApp a ser usada.
            api_key (str): A chave de API para autenticação com o serviço.
            number (str): O número de telefone do destinatário.
            text (str): O conteúdo da mensagem a ser enviada.
        """
        pass

    @abstractmethod
    def _typing(
        self,
        typing: bool,
        instance: str,
        number: str,
        api_key: str,
    ) -> None:
        """Controla o indicador de 'digitando' em um chat.

        Args:
            typing (bool): True para mostrar 'digitando', False para parar.
            instance (str): O identificador da instância do WhatsApp.
            number (str): O número de telefone do chat onde o indicador
                          deve ser exibido.
            api_key (str): A chave de API para autenticação.
        """
        pass
