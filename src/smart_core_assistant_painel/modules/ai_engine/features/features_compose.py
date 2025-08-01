from typing import Any

from langchain.docstore.document import Document
from loguru import logger
from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.datasource.analise_conteudo_langchain_datasource import (
    AnaliseConteudoLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_conteudo.domain.usecase.analise_conteudo_usecase import (
    AnaliseConteudoUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource import (
    AnalisePreviaMensagemLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.usecase.analise_previa_mensagem_usecase import (
    AnalisePreviaMensagemUsecase,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_document_conteudo.domain.usecase.load_document_conteudo_usecase import (
    LoadDocumentConteudoUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_document_file.datasource.load_document_file_datasource import (
    LoadDocumentFileDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_document_file.domain.usecase.load_document_file_usecase import (
    LoadDocumentFileUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DocumentError,
    LlmError,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    ACData,
    ACUsecase,
    APMData,
    APMTuple,
    APMUsecase,
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
    ) -> list[Document]:
        error = DocumentError("Error ao processar os dados do arquivo!")
        parameters = LoadDocumentConteudoParameters(
            id=id,
            conteudo=conteudo,
            tag=tag,
            grupo=grupo,
            error=error,
        )

        usecase: LDCUsecase = LoadDocumentConteudoUseCase()

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            result: list[Document] = data.result
            return result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def load_document_file(
        id: str,
        path: str,
        tag: str,
        grupo: str,
    ) -> list[Document]:
        error = DocumentError("Error ao processar os dados do arquivo!")
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
            result: list[Document] = data.result
            return result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def pre_analise_ia_treinamento(context: str) -> str:
        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={"temperature": SERVICEHUB.TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_ANALISE_CONTEUDO,
            context=context,
            error=LlmError("Error ao analisar o conteúdo"),
        )

        datasource: ACData = AnaliseConteudoLangchainDatasource()
        usecase: ACUsecase = AnaliseConteudoUseCase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            result: str = data.result
            return result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def melhoria_ia_treinamento(context: str) -> str:
        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={"temperature": SERVICEHUB.TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_MELHORIA_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_MELHORIA_CONTEUDO,
            context=context,
            error=LlmError("Error ao gerar conteudo melhorado"),
        )

        datasource: ACData = AnaliseConteudoLangchainDatasource()
        usecase: ACUsecase = AnaliseConteudoUseCase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            result: str = data.result
            return result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def analise_previa_mensagem(
        historico_atendimento: dict[str, Any], context: str
    ) -> APMTuple:
        """
        Método para análise prévia de uma mensagem, incluindo detecção de intenção e extração de entidades.
        """
        # Aqui você pode implementar a lógica de análise prévia
        # Exemplo: Detecção de intenção e extração de entidades
        llm_parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={"temperature": SERVICEHUB.TEMPERATURE},
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM,
            context=context,
            error=LlmError("Erro ao processar llm"),
        )
        parameters = AnalisePreviaMensagemParameters(
            historico_atendimento=historico_atendimento,
            valid_intent_types=SERVICEHUB.VALID_INTENT_TYPES,
            valid_entity_types=SERVICEHUB.VALID_ENTITY_TYPES,
            llm_parameters=llm_parameters,
            error=LlmError("Erro ao processar mensagem"),
        )
        datasource: APMData = AnalisePreviaMensagemLangchainDatasource()
        usecase: APMUsecase = AnalisePreviaMensagemUsecase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            result: APMTuple = data.result
            return result
        elif isinstance(data, ErrorReturn):
            logger.error(f"Erro ao analisar prévia da mensagem: {data.result}")
            raise data.result
        else:
            logger.error("Tipo de retorno inesperado da usecase")
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def mensagem_apresentacao() -> None:
        # mensagem de apresentação da empresa
        pass

    @staticmethod
    def solicitacao_info_cliene() -> None:
        # mensagem para coleta de informações do cliente
        pass

    @staticmethod
    def resumo_atendimento() -> None:
        # mensagem para resumo do atendimento
        pass
