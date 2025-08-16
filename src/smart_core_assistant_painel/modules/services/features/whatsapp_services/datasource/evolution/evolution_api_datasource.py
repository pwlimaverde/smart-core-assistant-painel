from py_return_success_or_error import NoParams
from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_whatsapp_service import (
    EvolutionWhatsAppService,
)
from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)

from smart_core_assistant_painel.modules.services.utils.types import WSData


class EvolutionAPIDatasource(WSData):
    """DataSource para interagir com a API do WhatsApp através do EvolutionAPI."""

    def __call__(self, parameters: NoParams) -> WhatsAppService:
        """Envia uma mensagem de texto através da API do WhatsApp."""
        # Monta o path para envio de mensagem
        try:
            return EvolutionWhatsAppService()

        except Exception as e:
            raise TypeError(f"Erro ao carregar serviço Evolution: {str(e)}")
