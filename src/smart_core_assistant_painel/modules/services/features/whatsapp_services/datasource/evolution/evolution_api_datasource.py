"""Fonte de dados para interagir com a API do WhatsApp via EvolutionAPI.

Este módulo fornece uma fonte de dados que encapsula a lógica para criar uma
instância do serviço de WhatsApp, especificamente a implementação que utiliza
a Evolution API.

Classes:
    EvolutionAPIDatasource: A fonte de dados para o serviço Evolution API.
"""

from py_return_success_or_error import NoParams

from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_whatsapp_service import (
    EvolutionWhatsAppService,
)
from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)
from smart_core_assistant_painel.modules.services.utils.types import WSData


class EvolutionAPIDatasource(WSData):
    """Fonte de dados para interagir com a API do WhatsApp via EvolutionAPI.

    Esta classe fornece uma interface para o EvolutionWhatsAppService,
    encapsulando a lógica para criar uma instância de serviço.
    """

    def __call__(self, parameters: NoParams) -> WhatsAppService:
        """Inicializa e retorna uma instância do serviço WhatsApp.

        Args:
            parameters (NoParams): Nenhum parâmetro é necessário para esta
                operação.

        Returns:
            WhatsAppService: Uma instância do EvolutionWhatsAppService.

        Raises:
            TypeError: Se ocorrer um erro ao carregar o serviço Evolution.
        """
        try:
            return EvolutionWhatsAppService()

        except Exception as e:
            raise TypeError(f"Erro ao carregar serviço Evolution: {str(e)}")
