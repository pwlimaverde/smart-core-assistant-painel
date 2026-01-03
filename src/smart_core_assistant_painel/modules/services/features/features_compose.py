from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from ..utils.erros import UnifieldDataServicesError
from ..utils.parameters import (
    UnifieldDataServicesParameters,
)
from ..utils.types import (
    UDSData,
    UDSUsecase,
)
from .service_hub import SERVICEHUB
from .unifield_data_services.datasource.unifield_data_services_datasource import (
    UnifieldDataServicesDatasource,
)
from .unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from .unifield_data_services.domain.usecase.unifield_data_services_usecase import (
    UnifieldDataServicesUseCase,
)


class FeaturesCompose:
    """Facade para os casos de uso do módulo de Serviços.

    Esta classe inicializa e configura os principais serviços da aplicação,
    como variáveis de ambiente e o banco de dados vetorial (vector storage).
    """

    @staticmethod
    def set_environ_remote() -> None:
        """
        [DEPRECATED] Método removido na migração SaaS.
        As configurações agora são gerenciadas via settings_manager e ConfigLoader.
        Mantido vazio temporariamente para evitar quebras de chamadas legadas.
        """
        pass

    @staticmethod
    def unifield_data_services() -> None:
        """Inicializa o serviço de dados unificado e registra no SERVICEHUB.

        Levanta erro padronizado em caso de falha na construção/registro.
        """
        error = UnifieldDataServicesError(
            "Erro ao executar unifield_data_services!"
        )
        parameters = UnifieldDataServicesParameters(
            data_source_id="",
            provider="trello",
            root_container_name="Unified Data Root",
            enable_observability=True,  # Habilitando observabilidade para debug
            error=error,
        )
        datasource: UDSData = UnifieldDataServicesDatasource()
        usecase: UDSUsecase = UnifieldDataServicesUseCase(
            datasource=datasource
        )
        result: ReturnSuccessOrError[UnifiedDataService] = usecase(parameters)
        if isinstance(result, SuccessReturn):
            SERVICEHUB.set_unified_data_service(result.result)
        elif isinstance(result, ErrorReturn):
            raise result.result
