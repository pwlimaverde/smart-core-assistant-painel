from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.datasource.waha.waha_whatsapp_api import (
    WahaWhatsAppApi, )
from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi, )
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import MessageParameters
from smart_core_assistant_painel.modules.ai_engine.utils.types import WSData


class WhatsappServicesDatasource(WSData):

    def __call__(self, parameters: MessageParameters) -> WhatsappApi:

        return WahaWhatsAppApi(parameters=parameters)
