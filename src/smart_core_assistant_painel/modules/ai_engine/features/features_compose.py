
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource import (
    AnaliseConteudoLangchainDatasource, )
from smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.domain.usecase.analise_conteudo_usecase import (
    AnaliseConteudoUseCase, )
from smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.datasource.load_document_conteudo_datasource import (
    LoadDocumentConteudoDatasource, )
from smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase import (
    LoadDocumentConteudoUseCase, )
from smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource import (
    LoadDocumentFileDatasource, )
from smart_core_assistant_painel.modules.ai_engine.features.load_document_file.domain.usecase.load_document_file_usecase import (
    LoadDocumentFileUseCase, )
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DocumentError,
    LlmError,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    ACData,
    ACUsecase,
    LDCData,
    LDCUsecase,
    LDFData,
    LDFUsecase,
)
from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB


class FeaturesCompose:

    @staticmethod
    def load_document_conteudo(
        id: str,
        conteudo: str,
        tag: str,
        grupo: str,
    ) -> str:

        error = DocumentError('Error ao processar os dados do arquivo!')
        parameters = LoadDocumentConteudoParameters(
            id=id,
            conteudo=conteudo,
            tag=tag,
            grupo=grupo,
            error=error,
        )

        datasource: LDCData = LoadDocumentConteudoDatasource()
        usecase: LDCUsecase = LoadDocumentConteudoUseCase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def load_document_file(id: str, path: str, tag: str, grupo: str,) -> str:

        error = DocumentError('Error ao processar os dados do arquivo!')
        parameters = LoadDocumentFileParameters(
            id=id,
            path=path,
            tag=tag,
            grupo=grupo,
            error=error,
        )

        datasource: LDFData = LoadDocumentFileDatasource()
        usecase: LDFUsecase = LoadDocumentFileUseCase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

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
        else:
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
        else:
            raise ValueError("Unexpected return type from usecase")
