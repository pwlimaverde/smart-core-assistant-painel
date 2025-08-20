"""Fonte de dados para os serviços de WhatsApp.

Este módulo fornece uma fonte de dados que instancia e retorna a implementação
concreta da API do WhatsApp a ser usada pela aplicação.

Classes:
    WhatsappServicesDatasource: A fonte de dados para o serviço de WhatsApp.
"""

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.waha.waha_whatsapp_api import (
    WahaWhatsAppApi,
)
from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    MessageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import WSData


class WhatsappServicesDatasource(WSData):
    """Fonte de dados para instanciar o serviço de API do WhatsApp."""

    def __call__(self, parameters: MessageParameters) -> WhatsappApi:
        """Cria e retorna uma instância da API do WhatsApp.

        Args:
            parameters (MessageParameters): Os parâmetros necessários para
                inicializar a API.

        Returns:
            WhatsappApi: Uma instância da implementação da API do WhatsApp.
        """
        return WahaWhatsAppApi(parameters=parameters)
