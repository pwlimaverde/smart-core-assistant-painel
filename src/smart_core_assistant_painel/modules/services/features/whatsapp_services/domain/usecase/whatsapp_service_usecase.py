"""Caso de uso para inicializar o serviço de WhatsApp.

Este módulo define o caso de uso responsável por criar e retornar uma
instância do serviço de WhatsApp. Ele lida com possíveis erros durante a
inicialização e encapsula o resultado em um objeto `ReturnSuccessOrError`.

Classes:
    WhatsAppServiceUsecase: O caso de uso para obter uma instância do serviço de WhatsApp.
"""
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
    """Caso de uso para obter uma instância do serviço de WhatsApp.

    Esta classe encapsula a lógica para inicializar o serviço de WhatsApp
    chamando a fonte de dados apropriada. Ela retorna a instância do serviço
    em caso de sucesso ou um objeto de erro em caso de falha.
    """

    def __call__(self, parameters: NoParams) -> ReturnSuccessOrError[WhatsAppService]:
        """Executa o caso de uso para obter uma instância do serviço de WhatsApp.

        Args:
            parameters (NoParams): Nenhum parâmetro é necessário para esta operação.

        Returns:
            ReturnSuccessOrError[WhatsAppService]: Um objeto de resultado contendo
                a instância `WhatsAppService` em caso de sucesso ou um
                `AppError` em caso de falha.
        """
        try:
            result = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )
            return result
        except Exception as e:
            error_msg = f"Erro na inicialização de WatsApp Services: {str(e)}"
            return ErrorReturn(WhatsAppServiceError(error_msg))
