from py_return_success_or_error import (
    ErrorReturn,
    NoParams,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB
from smart_core_assistant_painel.modules.services.features.set_environ_remote.datasource.set_environ_remote_firebase_datasource import (
    SetEnvironRemoteFirebaseDatasource,
)
from smart_core_assistant_painel.modules.services.features.set_environ_remote.domain.usecase.set_environ_remote_usecase import (
    SetEnvironRemoteUseCase,
)
from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_storage_datasource import (
    FaissStorageDatasource,
)
from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.usecase.vetor_storage_usecase import (
    VetorStorageUseCase,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    SetEnvironRemoteError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    SetEnvironRemoteParameters,
)
from smart_core_assistant_painel.modules.services.utils.types import (
    SERData,
    SERUsecase,
    VSData,
    VSUsecase,
)


class FeaturesCompose:
    @staticmethod
    def set_environ_remote() -> None:
        config_mapping = {
            "groq_api_key": "GROQ_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "whatsapp_api_base_url": "WHATSAPP_API_BASE_URL",
            "whatsapp_api_send_text_url": "WHATSAPP_API_SEND_TEXT_URL",
            "whatsapp_api_start_typing_url": "WHATSAPP_API_START_TYPING_URL",
            "whatsapp_api_stop_typing_url": "WHATSAPP_API_STOP_TYPING_URL",
            "llm_class": "LLM_CLASS",
            "model": "MODEL",
            "temperature": "TEMPERATURE",
            "prompt_system_analise_conteudo": "PROMPT_SYSTEM_ANALISE_CONTEUDO",
            "prompt_human_analise_conteudo": "PROMPT_HUMAN_ANALISE_CONTEUDO",
            "prompt_system_melhoria_conteudo": "PROMPT_SYSTEM_MELHORIA_CONTEUDO",
            "chunk_overlap": "CHUNK_OVERLAP",
            "chunk_size": "CHUNK_SIZE",
            "faiss_model": "FAISS_MODEL",
            "prompt_human_analise_previa_mensagem": "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM",
            "prompt_system_analise_previa_mensagem": "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM",
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

    @staticmethod
    def vetor_storage() -> None:
        parameters: NoParams = NoParams()
        datasource: VSData = FaissStorageDatasource()
        usecase: VSUsecase = VetorStorageUseCase(datasource=datasource)

        data = usecase(parameters)
        if isinstance(data, SuccessReturn):
            SERVICEHUB.set_vetor_storage(data.result)
        if isinstance(data, ErrorReturn):
            raise data.result