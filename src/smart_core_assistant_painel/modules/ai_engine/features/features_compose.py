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
from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.model.message_data import (
    MessageData,
)
from smart_core_assistant_painel.modules.ai_engine.features.load_mensage_data.domain.usecase.load_mensage_data_usecase import (
    LoadMensageDataUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DataMessageError,
    DocumentError,
    LlmError,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
    DataMensageParameters,
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
    LMDUsecase,
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
    def _converter_contexto(metadados: dict[str, Any]) -> str:
        """
    Converte metadados de mensagens multimídia para texto formatado legível.

    Esta função processa os metadados de mensagens não textuais (imagens,
    áudios, documentos, vídeos, stickers, etc.) e os converte em uma
    representação textual que pode ser compreendida e processada pelo
    sistema de IA para geração de respostas contextuais apropriadas.

    Args:
        metadata (dict): Dicionário contendo os metadados da mensagem.
            Estrutura típica inclui:
            - 'type': Tipo da mídia (image, audio, document, etc.)
            - 'mime_type'/'mimetype': Tipo MIME do arquivo
            - 'size'/'fileLength': Tamanho do arquivo em bytes
            - 'url': URL para download do arquivo
            - 'fileName': Nome original do arquivo
            - Campos específicos por tipo (duration, dimensions, etc.)

    Returns:
        str: Texto formatado representando o contexto da mensagem.
            Exemplos de retorno futuro:
            - "Imagem JPEG de 2.1MB (1920x1080)"
            - "Áudio MP3 de 45 segundos"
            - "Documento PDF: 'Relatório_Mensal.pdf' (856KB)"
            - "Vídeo MP4 de 2min30s (1280x720)"

    Raises:
        Exception: Repassada para o chamador em caso de erro na conversão.
            Logs de erro são gerados automaticamente para debugging.

    Implementation Status:
        - ATUAL: Retorna placeholder 'contexto' para todos os tipos
        - PLANEJADO: Conversão específica por tipo de mídia
        - FUTURO: Integração com análise de conteúdo por IA

    Processing Logic (Futuro):
        1. Identificar tipo de mídia pelos metadados
        2. Extrair informações relevantes (tamanho, formato, duração)
        3. Formatar texto descritivo apropriado
        4. Adicionar contexto específico quando possível

    Notes:
        - Função crítica para suporte completo a mensagens multimídia
        - Permite que o bot compreenda e responda a qualquer tipo de mensagem
        - Essencial para experiência de usuário completa no WhatsApp
        - Base para futuras funcionalidades de análise de conteúdo

    Examples:
        >>> # Imagem
        >>> metadata = {
        ...     "type": "image",
        ...     "mimetype": "image/jpeg",
        ...     "fileLength": 2048000,
        ...     "url": "https://example.com/image.jpg"
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Imagem JPEG de 2MB'  # Implementação futura

        >>> # Áudio
        >>> metadata = {
        ...     "type": "audio",
        ...     "mimetype": "audio/ogg",
        ...     "seconds": 45,
        ...     "ptt": True
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Mensagem de voz de 45 segundos'  # Implementação futura

        >>> # Documento
        >>> metadata = {
        ...     "type": "document",
        ...     "fileName": "Contrato_2025.pdf",
        ...     "mimetype": "application/pdf",
        ...     "fileLength": 856000
        ... }
        >>> _converter_contexto(metadata)
        'contexto'  # Atual
        # 'Documento PDF: Contrato_2025.pdf (856KB)'  # Implementação futura
    """
        try:
            # TODO: Implementar lógica específica de conversão por tipo de mídia
            #
            # Estrutura planejada:
            # if not metadata:
            #     return "Conteúdo sem metadados"
            #
            # media_type = metadata.get('type', 'unknown')
            #
            # if media_type == 'image':
            #     return _processar_contexto_imagem(metadata)
            # elif media_type == 'audio':
            #     return _processar_contexto_audio(metadata)
            # elif media_type == 'document':
            #     return _processar_contexto_documento(metadata)
            # elif media_type == 'video':
            #     return _processar_contexto_video(metadata)
            # else:
            #     return f"Conteúdo do tipo {media_type}"

            # Implementação atual: placeholder
            return "contexto"

        except Exception as e:
            logger.error(f"Erro ao converter contexto: {e}")
            raise e

    @staticmethod
    def load_message_data(
        data: dict[str, Any],
    ) -> MessageData:
        error = DataMessageError("Error ao processar os dados da mensagem!")

        parameters = DataMensageParameters(
            data=data,
            error=error,
        )

        usecase: LMDUsecase = LoadMensageDataUseCase()

        message_data = usecase(parameters)

        if isinstance(message_data, SuccessReturn):
            result: MessageData = message_data.result
            # TODO: Tratar dos dados da mensagem caso ela seja de midia, transcrevendo os audio, video, etc. em imagem
            if result.metadados:
                conteudo_media: str = FeaturesCompose._converter_contexto(result.metadados)
                result.conteudo = f"{result.conteudo}\n{conteudo_media}"
            return result
        elif isinstance(message_data, ErrorReturn):
            raise message_data.result
        else:
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
