"""Caso de uso para enviar mensagens através do serviço de WhatsApp.

Este módulo define o caso de uso que orquestra o envio de uma mensagem
pelo WhatsApp, incluindo o controle do indicador de 'digitando'.

Classes:
    WhatsappServicesUseCase: O caso de uso para enviar mensagens de WhatsApp.
"""
from py_return_success_or_error import (
    EMPTY,
    Empty,
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import WahaApiError
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    MessageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import WSUsecase


class WhatsappServicesUseCase(WSUsecase):
    """Caso de uso para orquestrar o envio de mensagens via WhatsApp."""

    def __call__(self, parameters: MessageParameters) -> ReturnSuccessOrError[Empty]:
        """Executa o caso de uso para enviar uma mensagem.

        Este método obtém a API do WhatsApp a partir da fonte de dados,
        simula o status de 'digitando', envia a mensagem e, em seguida,
        para o status de 'digitando'.

        Args:
            parameters (MessageParameters): Os parâmetros necessários para
                enviar a mensagem, como o ID do chat e o conteúdo.

        Returns:
            ReturnSuccessOrError[Empty]: Retorna um `SuccessReturn` com um
                objeto `EMPTY` em caso de sucesso, ou um `ErrorReturn`
                contendo um `WahaApiError` em caso de falha.
        """
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
                return ErrorReturn(WahaApiError("Erro ao obter dados do datasource."))
        except Exception as e:
            return ErrorReturn(WahaApiError(str(e)))
