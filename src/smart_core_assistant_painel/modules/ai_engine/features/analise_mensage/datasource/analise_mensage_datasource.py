from datetime import datetime
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langsmith import traceable
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseMensageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    AMData,
    RespostaBot,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB


class AnaliseMensageDatasource(AMData):
    """Datasource para análise de mensagem com ChatPromptTemplate multi-turn.

    Usa MessagesPlaceholder para injetar o histórico de chat estruturado
    (HumanMessage/AIMessage), permitindo que a LLM entenda a sequência
    completa da conversa.

    Retorna RespostaBot com estrutura:
    - resposta_texto: Texto para o usuário
    - acao_transferencia: Setor para transferência (se necessário)
    - confianca: Score de confiança (0.0 a 1.0)
    """

    def __call__(self, parameters: AnaliseMensageParameters) -> RespostaBot:
        result: RespostaBot = self._run(parameters)
        return result

    def _formatar_fluxos_disponiveis(
        self, fluxos_disponiveis: dict[str, str]
    ) -> str:
        """Formata os fluxos disponíveis para inclusão no prompt.

        Args:
            fluxos_disponiveis: Dicionário com os fluxos disponíveis

        Returns:
            str: Texto formatado com os setores para transferência
        """
        if not fluxos_disponiveis:
            return (
                "\n\n### SETORES DISPONÍVEIS PARA TRANSFERÊNCIA:\n"
                "Nenhum setor disponível no momento.\n"
            )

        fluxos_info = "\n\n### SETORES DISPONÍVEIS PARA TRANSFERÊNCIA:\n"
        for fluxo_key, fluxo_desc in fluxos_disponiveis.items():
            fluxos_info += f"- **{fluxo_key}**: {fluxo_desc}\n"

        # Usa regras externalizadas ou fallback padrão
        regras_transferencia = SERVICEHUB.PROMPT_REGRAS_TRANSFERENCIA
        if not regras_transferencia:
            regras_transferencia = (
                "\n### REGRAS DE TRANSFERÊNCIA:\n"
                "1. Analise a intenção do usuário e verifique se "
                "há um setor específico adequado\n"
                "2. Se houver um setor correspondente exato na lista acima, "
                "use-o\n"
                "3. Se não houver correspondência exata, "
                "escolha o setor mais próximo\n"
                "4. Use sempre o nome exato do setor conforme listado acima\n"
                "5. A transferência deve ser mencionada apenas se for "
                "realmente necessária\n"
            )
        else:
            regras_transferencia = f"\n{regras_transferencia}\n"

        fluxos_info += regras_transferencia

        return fluxos_info

    def _formatar_contexto_adicional(
        self, dados_contexto: dict[str, Any]
    ) -> str:
        """Formata entidades, intents e atendimentos anteriores para o prompt.

        Args:
            dados_contexto: Dicionário com entidades, intents e histórico.

        Returns:
            str: Texto formatado com o contexto adicional.
        """
        parts: list[str] = []

        # Entidades já extraídas
        entidades = dados_contexto.get("entidades_extraidas", [])
        if entidades:
            parts.append("**ENTIDADES JÁ IDENTIFICADAS:**")
            for entidade in entidades:
                if isinstance(entidade, dict):
                    for chave, valor in entidade.items():
                        parts.append(f"- {chave}: {valor}")
                else:
                    parts.append(f"- {entidade}")

        # Intents detectados
        intents = dados_contexto.get("intents_detectados", [])
        if intents:
            if parts:
                parts.append("")
            parts.append("**INTENÇÕES DETECTADAS:**")
            for intent in intents:
                if isinstance(intent, dict):
                    for chave in intent.keys():
                        parts.append(f"- {chave}")
                else:
                    parts.append(f"- {intent}")

        # Histórico de atendimentos anteriores
        atendimentos = dados_contexto.get("historico_atendimentos", [])
        if atendimentos:
            if parts:
                parts.append("")
            parts.append("**ATENDIMENTOS ANTERIORES:**")
            for atend in atendimentos:
                parts.append(f"- {atend}")

        return "\n".join(parts) if parts else "Nenhum contexto adicional."

    def _log_prompt_estruturado(
        self,
        system_prompt: str,
        chat_history: list[BaseMessage],
        mensagem_atual: str,
    ) -> None:
        """Gera log de debug mostrando o prompt final estruturado.

        Args:
            system_prompt: Prompt do sistema.
            chat_history: Lista de mensagens do histórico.
            mensagem_atual: Mensagem atual do usuário.
        """
        log_output = "\n" + "=" * 80 + "\n"
        log_output += "PROMPT ESTRUTURADO ENVIADO PARA LLM (MULTI-TURN)\n"
        log_output += "=" * 80 + "\n"

        # System message
        log_output += "\n" + "-" * 60 + "\n"
        log_output += "[SYSTEM]\n"
        log_output += "-" * 60 + "\n"
        log_output += f"{system_prompt}\n"

        # Chat history
        log_output += "\n" + "-" * 60 + "\n"
        log_output += f"[HISTÓRICO DE CHAT] ({len(chat_history)} mensagens)\n"
        log_output += "-" * 60 + "\n"

        for i, msg in enumerate(chat_history, 1):
            msg_type = type(msg).__name__
            role = "HUMAN" if "Human" in msg_type else "AI"
            # Converte content para string (pode ser str ou list)
            content_str = str(msg.content) if msg.content else ""
            content_preview = (
                content_str[:200] + "..."
                if len(content_str) > 200
                else content_str
            )
            log_output += f"\n  [{i}] {role}:\n"
            log_output += f"      {content_preview}\n"

        # Current user message
        log_output += "\n" + "-" * 60 + "\n"
        log_output += "[USER] (Mensagem Atual)\n"
        log_output += "-" * 60 + "\n"
        log_output += f"{mensagem_atual}\n"

        log_output += "\n" + "=" * 80 + "\n"
        log_output += "FIM DO PROMPT ESTRUTURADO\n"
        log_output += "=" * 80

        logger.info(log_output)

    @traceable(name="AnaliseMensage")
    def _run(self, parameters: AnaliseMensageParameters) -> RespostaBot:
        """Executa a análise de mensagem com ChatPromptTemplate multi-turn.

        Usa MessagesPlaceholder para injetar o histórico de chat estruturado,
        permitindo que a LLM entenda a sequência completa da conversa.

        Args:
            parameters: Parâmetros da análise de mensagem.

        Returns:
            RespostaBot: Resposta estruturada com texto, ação e confiança.
        """
        try:
            logger.debug("Iniciando _run de AnaliseMensageDatasource")

            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            dia_semana = datetime.now().strftime("%A")

            # Formata contexto adicional (entidades, intents, atendimentos)
            contexto_adicional = self._formatar_contexto_adicional(
                parameters.dados_contexto
            )
            logger.debug(
                f"Contexto adicional formatado "
                f"(tamanho: {len(contexto_adicional)})"
            )

            fluxos_disponiveis = self._formatar_fluxos_disponiveis(
                parameters.fluxos_disponiveis
            )

            # Carrega regras de resposta externalizadas ou usa fallback
            regras_resposta = SERVICEHUB.PROMPT_REGRAS_RESPOSTA
            msg_fallback = SERVICEHUB.MSG_FALLBACK_SEM_INFO
            if not regras_resposta:
                regras_resposta = (
                    "### Regras de Resposta (siga rigorosamente):\n"
                    "1. **Continuidade da Conversa:** Analise o histórico de "
                    "chat para entender o contexto e dar continuidade à "
                    "conversa de forma natural.\n"
                    "2. **Fonte da Resposta:** Baseie sua resposta nas "
                    "informações do <contexto_rag> e no fluxo da conversa.\n"
                    "3. **Informação Incorreta:** Se não houver informações "
                    f'relevantes, responda: "{msg_fallback}"\n'
                    "4. **Linguagem e Estilo:** Responda em português, de "
                    "forma sóbria, organizada e educada. Use quebras de linha e "
                    "listas com marcadores (-) para facilitar a leitura sempre que "
                    "houver múltiplos tópicos. Evite blocos de texto muito longos.\n"
                    "5. **Coleta de Informações e Transbordo:** Se faltarem "
                    "informações essenciais, solicite-as em UMA ÚNICA pergunta. "
                    "Se após perguntar o usuário não preencher as informações, "
                    "NÃO INSISTA, e transfira imediatamente o atendimento.\n"
                    "6. **Análise de Transferência:** Analise se o usuário "
                    "precisa ser transferido para um setor específico.\n"
                    "7. **Regra de Transferência:** Se identificar que uma "
                    "transferência é necessária, preencha o campo "
                    "'acao_transferencia' com o NOME EXATO do setor.\n"
                )

            # Monta o prompt do sistema
            system_prompt = (
                f"Data e Hora Atual: {data_atual} - {dia_semana}\n\n"
                f"{parameters.llm_parameters.prompt_system}\n\n"
                f"{parameters.llm_parameters.prompt_human}\n\n"
                f"{regras_resposta}"
                f"{fluxos_disponiveis}\n\n"
                f"### CONTEXTO DO ATENDIMENTO:\n{contexto_adicional}\n\n"
                f"### DADOS DA EMPRESA:\n{parameters.dados_empresa}\n\n"
                f"### DADOS DO TREINAMENTO (RAG):\n{parameters.dados_treinamento}"
            )

            # Usa MessagesPlaceholder para histórico de chat multi-turn
            messages = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("user", "{input}"),
                ]
            )

            # Log do prompt estruturado para debug
            mensagem_atual = parameters.llm_parameters.context
            self._log_prompt_estruturado(
                system_prompt,
                parameters.chat_history,
                mensagem_atual,
            )

            llm = parameters.llm_parameters.create_llm

            # Usa Structured Output para extrair resposta estruturada
            structured_llm = llm.with_structured_output(
                RespostaBot, method="json_schema"
            )
            chain = messages | structured_llm

            # Invoca com histórico estruturado
            logger.debug(
                f"Invocando LLM com {len(parameters.chat_history)} "
                f"mensagens no histórico..."
            )
            resultado: RespostaBot = chain.invoke(
                {
                    "chat_history": parameters.chat_history,
                    "input": mensagem_atual,
                }
            )

            logger.debug(
                f"Resposta estruturada: "
                f"resposta_texto={resultado.resposta_texto[:50]}..., "
                f"acao_transferencia={resultado.acao_transferencia}, "
                f"confianca={resultado.confianca}"
            )

            return resultado

        except Exception as e:
            logger.error(f"Erro ao processar análise de mensagem: {e}")
            raise
