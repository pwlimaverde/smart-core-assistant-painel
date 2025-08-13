from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import WSParameters
from smart_core_assistant_painel.modules.services.utils.types import WSUsecase
from smart_core_assistant_painel.modules.services.utils.erros import (
    WhatsAppServiceError,
)
import requests


class WhatsAppSendMessageUseCase(WSUsecase):
    """Caso de uso para envio de mensagens via WhatsApp."""

    def __call__(
        self, parameters: WSParameters
    ) -> ReturnSuccessOrError[requests.Response]:
        """Executa o caso de uso de envio de mensagem."""
        try:
            result = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )
            return result
        except Exception as e:
            error_msg = f"Erro no caso de uso de envio de mensagem: {str(e)}"
            return ErrorReturn(WhatsAppServiceError(error_msg))
