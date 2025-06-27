from py_return_success_or_error import (
    EMPTY,
    Empty,
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi, )
from smart_core_assistant_painel.modules.ai_engine.utils.erros import WahaApiError
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import MessageParameters
from smart_core_assistant_painel.modules.ai_engine.utils.types import WSUsecase


class WhatsappServicesUseCase(WSUsecase):

    def __call__(
            self,
            parameters: MessageParameters) -> ReturnSuccessOrError[Empty]:

        try:

            result_data = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )
            if isinstance(result_data, SuccessReturn):
                whatsapp_api: WhatsappApi = result_data.result
                whatsapp_api.typing(typing=True)
                whatsapp_api.send_message()
                whatsapp_api.typing(typing=False)
                return SuccessReturn(EMPTY)
            else:
                return ErrorReturn(
                    WahaApiError('Erro ao obter dados do datasource.'))
        except Exception as e:
            return ErrorReturn(WahaApiError(str(e)))
