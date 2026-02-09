"""Facade para os casos de uso do módulo AI Engine.

Esta classe fornece uma interface simplificada para acessar as funcionalidades
de IA do sistema, como processamento de documentos, análise de mensagens e
interação com modelos de linguagem.
"""

import math
from typing import Any

from langchain_core.documents import Document
from loguru import logger
from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_langchain_datasource import (
    AnalisePreviaLangchainDatasource,
)
from smart_core_assistant_painel.modules.ai_engine.features.generate_chunks.domain.usecase.generate_chunks_usecase import (
    GenerateChunksUseCase,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    EmbeddingError,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    GenerateEmbeddingsParameters,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB

from ..utils.erros import (
    AnaliseAvaliacaoError,
    AnaliseMensageError,
    DataMessageError,
    DocumentError,
    LlmError,
)
from ..utils.parameters import (
    AnaliseAvaliacaoParameters,
    AnaliseMensageParameters,
    AnalisePreviaMensagemParameters,
    DataMensageParameters,
    GenerateChunksParameters,
    LlmParameters,
    LoadDocumentConteudoParameters,
    LoadDocumentFileParameters,
)
from ..utils.types import (
    ACData,
    ACUsecase,
    AMData,
    AMTuple,
    AMUsecase,
    AnaliseAvaliacao,
    APMData,
    APMTuple,
    APMUsecase,
    GCUsecase,
    GEData,
    LDCUsecase,
    LDFData,
    LDFUsecase,
    LMDUsecase,
    RespostaBot,
)
from .analise_avaliacao.datasource.analise_avaliacao_datasource import (
    AnaliseAvaliacaoDatasource,
)
from .analise_avaliacao.domain.usecase.analise_avaliacao_usecase import (
    AnaliseAvaliacaoUsecase,
)
from .analise_conteudo.datasource.analise_conteudo_langchain_datasource import (
    AnaliseConteudoLangchainDatasource,
)
from .analise_conteudo.domain.usecase.analise_conteudo_usecase import (
    AnaliseConteudoUseCase,
)
from .analise_mensage.datasource.analise_mensage_datasource import (
    AnaliseMensageDatasource,
)
from .analise_mensage.domain.usecase.analise_mensage_usecase import (
    AnaliseMensageUseCase,
)

# REMOVIDO: import legado AnalisePreviaMensagemLangchainDatasource
# from .analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain_datasource import (
#     AnalisePreviaMensagemLangchainDatasource,
# )
from .analise_previa_mensagem.domain.usecase.analise_previa_mensagem_usecase import (
    AnalisePreviaMensagemUsecase,
)
from .generate_embeddings.datasource.generate_embeddings_langchain_datasource import (
    GenerateEmbeddingsLangchainDatasource,
)
from .load_document_conteudo.domain.usecase.load_document_conteudo_usecase import (
    LoadDocumentConteudoUseCase,
)
from .load_document_file.datasource.load_document_file_datasource import (
    LoadDocumentFileDatasource,
)
from .load_document_file.domain.usecase.load_document_file_usecase import (
    LoadDocumentFileUseCase,
)
from .load_mensage_data.domain.model.message_data import MessageData
from .load_mensage_data.domain.usecase.load_mensage_data_usecase import (
    LoadMensageDataUseCase,
)

# Compatibilidade com testes legados:
# Alguns testes patcham `AnalisePreviaMensagemLangchainDatasource` diretamente
# deste módulo. Reexportamos como alias para o novo datasource simplificado.
AnalisePreviaMensagemLangchainDatasource = AnalisePreviaLangchainDatasource


class FeaturesCompose:
    """Facade para os casos de uso do módulo AI Engine."""

    @staticmethod
    def load_document_conteudo(
        id: str,
        conteudo: str,
        tag: str,
        grupo: str,
    ) -> list[Document]:
        """Carrega e processa o conteúdo de um texto para treinamento.

        Args:
            id (str): Identificador único para o conteúdo.
            conteudo (str): O texto a ser processado.
            tag (str): Tag para categorização do conteúdo.
            grupo (str): Grupo ao qual o conteúdo pertence.

        Returns:
            list[Document]: Uma lista de objetos Document do Langchain.

        Raises:
            DocumentError: Se ocorrer um erro durante o processamento.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error = DocumentError("Error ao processar os dados do arquivo!")
        parameters = LoadDocumentConteudoParameters(
            id=id, conteudo=conteudo, tag=tag, grupo=grupo, error=error
        )
        usecase: LDCUsecase = LoadDocumentConteudoUseCase()
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def load_document_file(
        id: str, path: str, tag: str, grupo: str
    ) -> list[Document]:
        """Carrega e processa um arquivo de documento para treinamento.

        Args:
            id (str): Identificador único para o documento.
            path (str): O caminho do arquivo a ser carregado.
            tag (str): Tag para categorização do documento.
            grupo (str): Grupo ao qual o documento pertence.

        Returns:
            list[Document]: Uma lista de objetos Document do Langchain.

        Raises:
            DocumentError: Se ocorrer um erro durante o carregamento.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error = DocumentError("Error ao processar os dados do arquivo!")
        parameters = LoadDocumentFileParameters(
            id=id, path=path, tag=tag, grupo=grupo, error=error
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
        """Executa uma pré-análise em um conteúdo para treinamento de IA.

        Args:
            context (str): O conteúdo a ser analisado.

        Returns:
            str: O resultado da análise.

        Raises:
            LlmError: Se ocorrer um erro durante a comunicação com o LLM.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={
                "temperature": SERVICEHUB.LLM_TEMPERATURE,
                "api_key": SERVICEHUB.GROQ_API_KEY,
            },
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_ANALISE_CONTEUDO,
            context=context,
            error=LlmError("Erro na pré-análise do conteúdo"),
        )
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
        """Solicita ao LLM uma versão melhorada de um conteúdo para treinamento.

        Args:
            context (str): O conteúdo a ser melhorado.

        Returns:
            str: A versão melhorada do conteúdo.

        Raises:
            LlmError: Se ocorrer um erro durante a comunicação com o LLM.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={
                "temperature": SERVICEHUB.LLM_TEMPERATURE,
                "api_key": SERVICEHUB.GROQ_API_KEY,
            },
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_MELHORIA_CONTEUDO,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_MELHORIA_CONTEUDO,
            context=context,
            error=LlmError("Erro na melhoria do conteúdo"),
        )
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
    def analise_avaliacao(
        chat_history: list[dict[str, Any]] | list[Any],
        llm_config: LlmParameters | None = None,
    ) -> AnaliseAvaliacao:
        """Realiza análise de avaliação (feedback) da mensagem.

        Args:
            chat_history: Histórico da conversa para análise.
            llm_config: Configurações opcionais do LLM.

        Returns:
            AnaliseAvaliacao: Objeto com nota, sentimento e feedback.

        Raises:
            AnaliseAvaliacaoError: Se houver erro na análise.
        """
        try:
            if llm_config is None:
                llm_config = LlmParameters(
                    llm_class=SERVICEHUB.LLM_CLASS,
                    model=SERVICEHUB.MODEL,
                    error=LlmError("Erro na análise de avaliação"),
                    prompt_system="",
                    prompt_human="",
                    context="",
                    extra_params={
                        "temperature": SERVICEHUB.LLM_TEMPERATURE,
                        "api_key": SERVICEHUB.GROQ_API_KEY,
                    },
                )

            error_param = AnaliseAvaliacaoError("Erro na análise de avaliação")

            params = AnaliseAvaliacaoParameters(
                chat_history=chat_history,
                llm_parameters=llm_config,
                error=error_param,
            )
            datasource = AnaliseAvaliacaoDatasource()
            usecase = AnaliseAvaliacaoUsecase(datasource)
            result = usecase(params)

            if isinstance(result, SuccessReturn):
                return result.result
            elif isinstance(result, ErrorReturn):
                raise result.result
            else:
                raise ValueError("Unexpected return type from usecase")

        except Exception as e:
            logger.error(f"Erro na feature analise_avaliacao: {e}")
            raise AnaliseAvaliacaoError(f"Erro na análise de avaliação: {e}")

    @staticmethod
    def analise_previa_mensagem(
        historico_atendimento: dict[str, Any],
        context: str,
        valid_intent_types: str,
    ) -> APMTuple:
        """Realiza análise prévia de mensagem para extrair intenção e entidades.

        Args:
            historico_atendimento (dict[str, Any]): Histórico da conversa.
            context (str): O texto da mensagem a ser analisada.

        Returns:
            APMTuple: Uma tupla contendo as intenções e entidades detectadas.

        Raises:
            LlmError: Se ocorrer um erro durante a comunicação com o LLM.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        llm_parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={
                "temperature": SERVICEHUB.LLM_TEMPERATURE,
                "api_key": SERVICEHUB.GROQ_API_KEY,
            },
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM,
            prompt_human=SERVICEHUB.PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM,
            context=context,
            error=LlmError("Erro na análise prévia da mensagem"),
        )
        parameters = AnalisePreviaMensagemParameters(
            historico_atendimento=historico_atendimento,
            valid_intent_types=valid_intent_types,
            valid_entity_types=SERVICEHUB.VALID_ENTITY_TYPES,
            llm_parameters=llm_parameters,
            error=LlmError("Erro ao processar mensagem"),
        )
        # Usa o alias legado para compatibilidade com testes
        datasource: APMData = AnalisePreviaMensagemLangchainDatasource()
        usecase: APMUsecase = AnalisePreviaMensagemUsecase(datasource)
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def converter_contexto(metadados: dict[str, Any]) -> str:
        """Converte metadados de mensagens multimídia para texto.

        Args:
            metadados (dict[str, Any]): Dicionário com os metadados da mensagem.

        Returns:
            str: Texto formatado representando o contexto da mensagem.
        """
        try:
            return "contexto"
        except Exception as e:
            logger.error(f"Erro ao converter contexto: {e}")
            raise e

    @staticmethod
    def load_message_data(data: dict[str, Any]) -> MessageData:
        """Carrega e processa os dados de uma mensagem de webhook.

        Args:
            data (dict[str, Any]): O payload do webhook.

        Returns:
            MessageData: Um objeto com os dados da mensagem normalizados.

        Raises:
            DataMessageError: Se ocorrer um erro ao processar os dados.
            ValueError: Se o tipo de retorno do caso de uso for inesperado.
        """
        error = DataMessageError("Error ao processar os dados da mensagem!")
        parameters = DataMensageParameters(data=data, error=error)
        usecase: LMDUsecase = LoadMensageDataUseCase()
        message_data = usecase(parameters)

        if isinstance(message_data, SuccessReturn):
            result: MessageData = message_data.result
            if result.metadados:
                conteudo_media: str = FeaturesCompose.converter_contexto(
                    result.metadados
                )
                if conteudo_media and conteudo_media != "contexto":
                    result.conteudo = f"{result.conteudo}\n{conteudo_media}"
            return result
        elif isinstance(message_data, ErrorReturn):
            raise message_data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def mensagem_apresentacao() -> None:
        """Envia uma mensagem de apresentação da empresa."""
        pass

    @staticmethod
    def solicitacao_info_cliene() -> None:
        """Envia uma mensagem para coleta de informações do cliente."""
        pass

    @staticmethod
    def resumo_atendimento() -> None:
        """Envia uma mensagem de resumo do atendimento."""
        pass

    @staticmethod
    def generate_embeddings(text: str) -> list[float]:
        """Gera embeddings para um texto.

        Args:
            text (str): Texto para gerar embeddings.

        Returns:
            list[float]: Vetor de embeddings gerado.

        Raises:
            EmbeddingError: Se ocorrer um erro durante a geração.
        """
        parameters: GenerateEmbeddingsParameters = (
            GenerateEmbeddingsParameters(
                text=text,
                error=EmbeddingError("Erro ao gerar embeddings!"),
            )
        )
        datasource: GEData = GenerateEmbeddingsLangchainDatasource()
        try:
            return datasource(parameters)
        except Exception as e:
            raise EmbeddingError(f"Erro ao gerar embeddings: {e}") from e

    @staticmethod
    def _calculate_embedding_similarity(
        embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Calcula a similaridade do cosseno entre dois embeddings.

        A similaridade do cosseno mede o ângulo entre dois vetores,
        retornando um valor entre -1 e 1, onde:
        - 1 indica vetores idênticos (máxima similaridade)
        - 0 indica vetores ortogonais (sem similaridade)
        - -1 indica vetores opostos (mínima similaridade)

        Args:
            embedding1 (list[float]): Primeiro vetor de embedding.
            embedding2 (list[float]): Segundo vetor de embedding.

        Returns:
            float: Valor da similaridade do cosseno entre -1 e 1.

        Raises:
            ValueError: Se os embeddings tiverem dimensões diferentes ou
                       se algum dos vetores for zero.
        """
        if len(embedding1) != len(embedding2):
            raise ValueError(
                f"Embeddings devem ter a mesma dimensão. "
                f"Recebido: {len(embedding1)} e {len(embedding2)}"
            )

        if not embedding1 or not embedding2:
            raise ValueError("Embeddings não podem estar vazios")

        # Calcula o produto escalar (dot product)
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))

        # Calcula a magnitude (norma) de cada vetor
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))

        # Evita divisão por zero
        if magnitude1 == 0 or magnitude2 == 0:
            raise ValueError(
                "Não é possível calcular similaridade para vetores zero"
            )

        # Calcula a similaridade do cosseno
        similarity = dot_product / (magnitude1 * magnitude2)

        return similarity

    @staticmethod
    def _evaluate_triple_similarity(
        message_vec: list[float],
        response_vec: list[float],
        training_vec: list[float] | None = None,
    ) -> float:
        """Avalia a consistência entre pergunta, resposta e treinamento.

        A métrica final considera as similaridades pareadas:
        - sr: pergunta vs resposta
        - sq: pergunta vs treinamento (se houver)
        - st: resposta vs treinamento (se houver)

        Estratégia:
        - Se não houver ``training_vec``, o score final é reduzido, pois há
          maior risco de alucinação. Usamos 0.75 * sr.
        - Se houver ``training_vec``, combinamos as três similaridades com
          pesos e penalizamos inconsistências (quando alguma fica muito baixa).

        Returns:
            float: Score final normalizado entre 0 e 1.
        """
        # Similaridade entre pergunta e resposta
        sr: float = FeaturesCompose._calculate_embedding_similarity(
            message_vec, response_vec
        )

        # Sem dados de treinamento: score com penalidade leve
        if training_vec is None:
            final_score: float = max(0.0, min(1.0, 0.75 * sr))
            return final_score

        # Com dados de treinamento: calcular as demais similaridades
        sq: float = FeaturesCompose._calculate_embedding_similarity(
            message_vec, training_vec
        )
        st: float = FeaturesCompose._calculate_embedding_similarity(
            response_vec, training_vec
        )

        # Combinação ponderada das três similaridades
        base_score: float = 0.5 * sr + 0.25 * sq + 0.25 * st

        # Penalização por inconsistência com o treinamento
        # (se uma das duas ficar muito baixa, reduzimos o score)
        min_qt: float = min(sq, st)
        if min_qt < 0.4:
            # Redução proporcional ao quão abaixo do limite está
            penalty: float = (0.4 - min_qt) * 0.5
            base_score = max(0.0, base_score - penalty)

        # Garantir faixa [0, 1]
        final_score = max(0.0, min(1.0, base_score))
        return final_score

    @staticmethod
    def generate_chunks(
        conteudo: str, metadata: dict[str, Any]
    ) -> list[Document]:
        """Gera chunks a partir do conteúdo informado.

        Args:
            conteudo (str): Texto de entrada para gerar chunks.
            metadata (dict[str, Any]): Metadados associados ao conteúdo.

        Returns:
            list[Document]: Lista de documentos (chunks) gerados.
        """
        error = DocumentError("Erro ao gerar chunks do conteúdo!")
        parameters = GenerateChunksParameters(
            metadata=metadata,
            conteudo=conteudo,
            error=error,
        )
        usecase: GCUsecase = GenerateChunksUseCase()
        data: ReturnSuccessOrError[list[Document]] = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def _extrair_fluxo_transferencia(
        response_text: str, fluxos_disponiveis: dict[str, str]
    ) -> str:
        """DEPRECATED: Use _mapear_acao_para_fluxo com Structured Output.

        Extrai a chave do fluxo de transferência adequado da resposta do bot.
        Este método usa regex e será removido em versão futura.

        Args:
            response_text: Resposta do bot que contém a menção de transferência
            fluxos_disponiveis: Dicionário com os fluxos disponíveis

        Returns:
            str: Chave do fluxo correspondente ou string vazia se não encontrar
        """
        import re
        import warnings

        warnings.warn(
            "_extrair_fluxo_transferencia está deprecated. "
            "Use _mapear_acao_para_fluxo com Structured Output.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Padrão para extrair o nome do setor após "Estarei transferindo seu atendimento para"
        pattern = r"Estarei transferindo seu atendimento para ([^.]+)"
        match = re.search(pattern, response_text, re.IGNORECASE)

        if not match:
            return ""

        setor_mentionado = match.group(1).strip()

        # Percorre todos os fluxos disponíveis para encontrar correspondência
        for fluxo_key in fluxos_disponiveis.keys():
            # Extrai apenas o nome do setor (antes do "-")
            nome_setor = fluxo_key.split(" - ")[0].strip()

            # Verifica correspondência exata ou parcial
            if (
                setor_mentionado.lower() == nome_setor.lower()
                or setor_mentionado.lower() in nome_setor.lower()
                or nome_setor.lower() in setor_mentionado.lower()
            ):
                logger.info(
                    f"Fluxo de transferência identificado: {fluxo_key} "
                    f"(setor mencionado: {setor_mentionado})"
                )
                return fluxo_key

        logger.warning(
            f"Nenhum fluxo correspondente encontrado para: {setor_mentionado}. "
            "Usando primeiro fluxo disponível como padrão."
        )
        # Retorna a primeira key como padrão se houver fluxos disponíveis
        if fluxos_disponiveis:
            primeira_key = next(iter(fluxos_disponiveis.keys()))
            logger.info(f"Usando fluxo padrão: {primeira_key}")
            return primeira_key
        return ""

    @staticmethod
    def analise_mensage(
        fluxos_disponiveis: dict[str, str],
        context: str,
        historico_atendimento: dict[str, Any],
        prompt_human: str,
        dados_treinamento: str,
    ) -> AMTuple:
        error = AnaliseMensageError("Erro ao executar analise_mensage!")
        llm_parameters = LlmParameters(
            llm_class=SERVICEHUB.LLM_CLASS,
            model=SERVICEHUB.MODEL,
            extra_params={
                "temperature": SERVICEHUB.LLM_TEMPERATURE,
                "api_key": SERVICEHUB.GROQ_API_KEY,
            },
            prompt_system=SERVICEHUB.PROMPT_SYSTEM_ANALISE_MENSAGEM,
            prompt_human=prompt_human,
            context=context,
            error=LlmError("Erro na análise de mensagem"),
        )

        parameters = AnaliseMensageParameters(
            fluxos_disponiveis=fluxos_disponiveis,
            chat_history=historico_atendimento.get("chat_history", []),
            dados_contexto={
                "entidades_extraidas": historico_atendimento.get(
                    "entidades_extraidas", []
                ),
                "intents_detectados": historico_atendimento.get(
                    "intents_detectados", []
                ),
                "historico_atendimentos": historico_atendimento.get(
                    "historico_atendimentos", []
                ),
            },
            dados_empresa=SERVICEHUB.PROMPT_SYSTEM_DADOS_EMPRESA,
            dados_treinamento=dados_treinamento,
            llm_parameters=llm_parameters,
            error=error,
        )
        datasource: AMData = AnaliseMensageDatasource()
        usecase: AMUsecase = AnaliseMensageUseCase(datasource)
        data = usecase(parameters)
        if isinstance(data, SuccessReturn):
            # Obtém RespostaBot estruturada (via Structured Output)
            resposta_estruturada: RespostaBot = data.result  # type: ignore
            response_text: str = str(
                resposta_estruturada.resposta_texto
            ).strip()

            # Determina transferência via Structured Output
            # (acao_transferencia preenchido automaticamente pelo LLM)
            acao_transferencia = resposta_estruturada.acao_transferencia
            confianca_llm = resposta_estruturada.confianca

            logger.info(
                f"Structured Output: acao_transferencia={acao_transferencia}, "
                f"confianca={confianca_llm}"
            )

            # Define flags com base na resposta estruturada
            transfer_attendance: bool = acao_transferencia is not None
            fluxo_transferencia: str = ""

            # Mapeia acao_transferencia para fluxo_disponiveis
            if transfer_attendance and acao_transferencia:
                fluxo_transferencia = FeaturesCompose._mapear_acao_para_fluxo(
                    acao_transferencia, fluxos_disponiveis
                )
                logger.info(
                    f"Transferência detectada via Structured Output. "
                    f"acao={acao_transferencia} → fluxo={fluxo_transferencia}"
                )

            # Gera embeddings para pergunta (context), treinamento (se houver)
            # e resposta do bot. Quando não há treinamento, evitamos gerar
            # embedding para string vazia.
            vector_mensagem: list[float] = FeaturesCompose.generate_embeddings(
                context
            )
            vector_treinamento: list[float] | None = None
            if dados_treinamento and str(dados_treinamento).strip():
                vector_treinamento = FeaturesCompose.generate_embeddings(
                    dados_treinamento
                )
            vector_resposta: list[float] = FeaturesCompose.generate_embeddings(
                response_text
            )

            # Calcula a similaridade considerando os 3 vetores
            final_score = FeaturesCompose._evaluate_triple_similarity(
                message_vec=vector_mensagem,
                response_vec=vector_resposta,
                training_vec=vector_treinamento,
            )

            # Log do score final para análise
            logger.info(
                "Score de confiabilidade (triádico): %.4f" % final_score
            )

            # Decide se força transferência por baixa confiabilidade.
            # A decisão considera AMBOS os indicadores:
            # 1. Score de similaridade (cálculo triádico)
            # 2. Confiança do LLM (confianca_llm retornada pelo modelo)
            #
            # Só força transferência quando:
            # - O LLM NÃO indicou transferência (acao_transferencia é None)
            # - E a confiança do LLM está baixa (< 0.5)
            # - E o score de similaridade está abaixo do threshold
            #
            # Se o LLM retornou confiança alta e não indicou transferência,
            # respeitamos essa decisão mesmo que o score de similaridade
            # seja baixo (ex: saudação sem dados de treinamento).
            similarity_threshold = SERVICEHUB.SIMILARITY_THRESHOLD
            llm_confidence_threshold = 0.5  # Limiar de confiança do LLM

            should_force_transfer = (
                final_score < similarity_threshold
                and confianca_llm < llm_confidence_threshold
                and not transfer_attendance
            )

            if should_force_transfer:
                transfer_attendance = True
                logger.info(
                    f"Transferência forçada: score={final_score:.4f} < "
                    f"{similarity_threshold}, confianca_llm={confianca_llm:.2f} < "
                    f"{llm_confidence_threshold}."
                )
                # Adiciona mensagem de transferência
                msg_transferencia = SERVICEHUB.MSG_TRANSFERENCIA_GENERICA
                response_text = f"{response_text}\n\n{msg_transferencia}"
            elif (
                final_score < similarity_threshold and not transfer_attendance
            ):
                # Log informativo: score baixo, mas confiança do LLM está alta
                logger.info(
                    f"Score baixo ({final_score:.4f}), mas confianca_llm alta "
                    f"({confianca_llm:.2f}). Mantendo resposta sem transferência."
                )

            # Se precisa transferir e ainda não tem fluxo, usa o primeiro
            if transfer_attendance and not fluxo_transferencia:
                if fluxos_disponiveis:
                    fluxo_transferencia = next(iter(fluxos_disponiveis.keys()))
                    logger.info(f"Usando fluxo padrão: {fluxo_transferencia}")

            return AMTuple(
                resposta_bot=response_text,
                confiabilidade=final_score,
                transferir_atendimento=transfer_attendance,
                fluxo_transferencia=fluxo_transferencia,
            )
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Unexpected return type from usecase")

    @staticmethod
    def _mapear_acao_para_fluxo(
        acao_transferencia: str, fluxos_disponiveis: dict[str, str]
    ) -> str:
        """Mapeia ação de transferência para chave de fluxo disponível.

        Args:
            acao_transferencia: Nome do setor retornado pelo LLM.
            fluxos_disponiveis: Dicionário com fluxos disponíveis.

        Returns:
            Chave do fluxo correspondente ou string vazia.
        """
        acao_lower = acao_transferencia.lower().strip()

        # Correspondência exata ou parcial com chaves de fluxo
        for fluxo_key in fluxos_disponiveis.keys():
            nome_setor = fluxo_key.split(" - ")[0].strip().lower()
            if (
                acao_lower == nome_setor
                or acao_lower in nome_setor
                or nome_setor in acao_lower
            ):
                logger.info(
                    f"Mapeamento: '{acao_transferencia}' → '{fluxo_key}'"
                )
                return fluxo_key

        # Fallback: usa primeiro fluxo disponível
        if fluxos_disponiveis:
            primeira_key = next(iter(fluxos_disponiveis.keys()))
            logger.warning(
                f"Nenhum fluxo correspondente para '{acao_transferencia}'. "
                f"Usando padrão: {primeira_key}"
            )
            return primeira_key

        return ""
