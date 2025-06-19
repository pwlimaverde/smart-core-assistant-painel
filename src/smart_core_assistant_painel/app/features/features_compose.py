
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.app.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource import (
    AnaliseConteudoLangchainDatasource, )
from smart_core_assistant_painel.app.features.analise_conteudo.domain.usecase.analise_conteudo_usecase import (
    AnaliseConteudoUseCase, )
from smart_core_assistant_painel.app.features.whatsapp_services.datasource.whatsapp_services_datasource import (
    WhatsappServicesDatasource, )
from smart_core_assistant_painel.app.features.whatsapp_services.domain.usecase.whatsapp_services_usecase import (
    WhatsappServicesUseCase, )
from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB
from smart_core_assistant_painel.utils.erros import LlmError
from smart_core_assistant_painel.utils.parameters import (
    LlmParameters,
    MessageParameters,
)
from smart_core_assistant_painel.utils.types import (
    ACData,
    ACUsecase,
    WSData,
    WSUsecase,
)


class FeaturesCompose:

    @staticmethod
    def send_message_whatsapp(parameters: MessageParameters) -> None:

        dataSource: WSData = WhatsappServicesDatasource()
        usecase: WSUsecase = WhatsappServicesUseCase(dataSource)

        data = usecase(parameters)
        if isinstance(data, ErrorReturn):
            raise data.result

    @staticmethod
    def pre_analise_ia_treinamento(context: str) -> str:

        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={
                'temperature': SERVICEHUB.TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_ANALISE_CONTEUDO,
            context=context,
            error=LlmError('Error ao analisar o conteúdo'),)

        datasource: ACData = AnaliseConteudoLangchainDatasource()
        usecase: ACUsecase = AnaliseConteudoUseCase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def melhoria_ia_treinamento(context: str) -> str:

        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={
                'temperature': SERVICEHUB.TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_MELHORIA_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_MELHORIA_CONTEUDO,
            context=context,
            error=LlmError('Error ao gerar conteudo melhorado'),)

        datasource: ACData = AnaliseConteudoLangchainDatasource()
        usecase: ACUsecase = AnaliseConteudoUseCase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        raise ValueError("Unexpected return type from usecase")
