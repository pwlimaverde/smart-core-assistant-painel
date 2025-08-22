from py_return_success_or_error import (
    ErrorReturn,
    NoParams,
    SuccessReturn,
)

from ..utils.erros import SetEnvironRemoteError
from ..utils.parameters import SetEnvironRemoteParameters
from ..utils.types import (
    SERData,
    SERUsecase,
    WSData,
)
from .service_hub import SERVICEHUB
from .set_environ_remote.datasource.set_environ_remote_firebase_datasource import (
    SetEnvironRemoteFirebaseDatasource,
)
from .set_environ_remote.domain.usecase.set_environ_remote_usecase import (
    SetEnvironRemoteUseCase,
)
from .whatsapp_services.datasource.evolution.evolution_api_datasource import (
    EvolutionAPIDatasource,
)
from .whatsapp_services.domain.usecase.whatsapp_service_usecase import (
    WhatsAppServiceUsecase,
)


class FeaturesCompose:
    """Facade para os casos de uso do módulo de Serviços.

    Esta classe inicializa e configura os principais serviços da aplicação,
    como variáveis de ambiente, o banco de dados vetorial (vector storage)
    e o serviço de mensagens do WhatsApp.
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
            #Api_Keys
            "groq_api_key": "GROQ_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "huggingface_api_key": "HUGGINGFACE_API_KEY",
            #LLM
            "llm_class": "LLM_CLASS",
            "model": "MODEL",
            "llm_temperature": "LLM_TEMPERATURE",
            #Prompts
            "prompt_system_analise_conteudo": "PROMPT_SYSTEM_ANALISE_CONTEUDO",
            "prompt_human_analise_conteudo": "PROMPT_HUMAN_ANALISE_CONTEUDO",
            "prompt_system_melhoria_conteudo": "PROMPT_SYSTEM_MELHORIA_CONTEUDO",
            "prompt_human_melhoria_conteudo": "PROMPT_HUMAN_MELHORIA_CONTEUDO",
            "prompt_human_analise_previa_mensagem": "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM",
            "prompt_system_analise_previa_mensagem": "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM",
            #Embeddings
            "chunk_overlap": "CHUNK_OVERLAP",
            "chunk_size": "CHUNK_SIZE",
            "embeddings_model": "EMBEDDINGS_MODEL",
            "embeddings_class": "EMBEDDINGS_CLASS",
            #Whatsapp
            "whatsapp_api_base_url": "WHATSAPP_API_BASE_URL",
            "whatsapp_api_send_text_url": "WHATSAPP_API_SEND_TEXT_URL",
            "whatsapp_api_start_typing_url": "WHATSAPP_API_START_TYPING_URL",
            "whatsapp_api_stop_typing_url": "WHATSAPP_API_STOP_TYPING_URL",
            #Utilitarios
            "valid_entity_types": "VALID_ENTITY_TYPES",
            "valid_intent_types": "VALID_INTENT_TYPES",
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
    def whatsapp_service() -> None:
        """Inicializa o serviço de cliente de API do WhatsApp (Evolution API)
        e o disponibiliza no `SERVICEHUB`.

        Raises:
            WhatsappServiceError: Se ocorrer um erro ao inicializar o serviço.
        """
        # Cria os parâmetros
        parameters: NoParams = NoParams()
        datasource: WSData = EvolutionAPIDatasource()
        usecase = WhatsAppServiceUsecase(datasource=datasource)

        data = usecase(parameters)
        if isinstance(data, SuccessReturn):
            SERVICEHUB.set_whatsapp_service(data.result)
        if isinstance(data, ErrorReturn):
            raise data.result
