from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from ..utils.erros import SetEnvironRemoteError, UnifieldDataServicesError
from ..utils.parameters import (
    SetEnvironRemoteParameters,
    UnifieldDataServicesParameters,
)
from ..utils.types import (
    SERData,
    SERUsecase,
    UDSData,
    UDSUsecase,
)
from .service_hub import SERVICEHUB
from .set_environ_remote.datasource.set_environ_remote_firebase_datasource import (
    SetEnvironRemoteFirebaseDatasource,
)
from .set_environ_remote.domain.usecase.set_environ_remote_usecase import (
    SetEnvironRemoteUseCase,
)
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
        """Busca as variáveis de ambiente de um datasource remoto (Firebase)
        e as injeta no `SERVICEHUB` para uso global na aplicação.

        Raises:
            SetEnvironRemoteError: Se ocorrer um erro ao buscar ou definir
                                   as variáveis de ambiente.
        """
        config_mapping = {
            # Api_Keys
            "groq_api_key": "GROQ_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "huggingface_api_key": "HUGGINGFACE_API_KEY",
            # LLM
            "llm_class": "LLM_CLASS",
            "model": "MODEL",
            "llm_temperature": "LLM_TEMPERATURE",
            # Prompts
            "prompt_system_analise_conteudo": "PROMPT_SYSTEM_ANALISE_CONTEUDO",
            "prompt_human_analise_conteudo": "PROMPT_HUMAN_ANALISE_CONTEUDO",
            "prompt_system_melhoria_conteudo": "PROMPT_SYSTEM_MELHORIA_CONTEUDO",
            "prompt_human_melhoria_conteudo": "PROMPT_HUMAN_MELHORIA_CONTEUDO",
            "prompt_human_analise_previa_mensagem": "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM",
            "prompt_system_analise_previa_mensagem": "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM",
            "prompt_system_analise_mensagem": "PROMPT_SYSTEM_ANALISE_MENSAGEM",
            # Embeddings
            "chunk_overlap": "CHUNK_OVERLAP",
            "chunk_size": "CHUNK_SIZE",
            "embeddings_model": "EMBEDDINGS_MODEL",
            "embeddings_class": "EMBEDDINGS_CLASS",
            # Utilitarios
            "valid_entity_types": "VALID_ENTITY_TYPES",
            "time_cache": "TIME_CACHE",
        }
        error: SetEnvironRemoteError = SetEnvironRemoteError(
            "Erro ao carregar variáveis de ambiente"
        )
        parameters: SetEnvironRemoteParameters = SetEnvironRemoteParameters(
            error=error,
            config_mapping=config_mapping,
        )
        datasource: SERData = SetEnvironRemoteFirebaseDatasource()
        usecase: SERUsecase = SetEnvironRemoteUseCase(datasource=datasource)

        data = usecase(parameters)
        if isinstance(data, ErrorReturn):
            raise data.result

        # Recarrega as configurações do SERVICEHUB após carregar as variáveis do Firebase
        SERVICEHUB.reload_config()

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
