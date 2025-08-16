from py_return_success_or_error import (
    ErrorReturn,
    NoParams,
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    WhatsAppServiceError,
)
from smart_core_assistant_painel.modules.services.utils.types import WSUsecase


class WhatsAppServiceUsecase(WSUsecase):

    """Caso de uso para envio de mensagens via WhatsApp."""

    def __call__(
        self, parameters: NoParams
    ) -> ReturnSuccessOrError[WhatsAppService]:
        """Executa o caso de uso de envio de mensagem."""
        try:
            result = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )
            return result
        except Exception as e:
            error_msg = f"Erro na inicialização de WatsApp Services: {str(e)}"
            return ErrorReturn(WhatsAppServiceError(error_msg))
