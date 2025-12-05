from datetime import datetime
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
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
    """Datasource para análise de mensagem com Structured Output.

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
            return "\n\n### SETORES DISPONÍVEIS PARA TRANSFERÊNCIA:\nNenhum setor disponível no momento.\n"

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

    def _formatar_historico_atendimento(
        self, historico_atendimento: dict[str, Any]
    ) -> str:
        """Formata o histórico de atendimento para ser usado no prompt da LLM.

        Args:
            historico_atendimento: Histórico de atendimento a ser formatado (dict[str, Any])

        Returns:
            str: Histórico formatado para o prompt
        """
        mensagens = historico_atendimento.get("conteudo_mensagens", [])
        intents = historico_atendimento.get("intents_detectados", [])
        entidades = historico_atendimento.get("entidades_extraidas", [])
        atendimentos_anteriores = historico_atendimento.get(
            "historico_atendimentos", []
        )

        historico_parts = [
            "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:"
        ]

        # Atendimentos anteriores - para contexto histórico
        if atendimentos_anteriores:
            historico_parts.append("")
            historico_parts.append("HISTÓRICO DE ATENDIMENTOS ANTERIORES:")
            for i, atendimento in enumerate(atendimentos_anteriores, 1):
                historico_parts.append(f"{i}. {atendimento}")

        historico_parts.append("\n\nHISTÓRICO DO ATENDIMENTO ATUAL:")
        # Entidades extraídas - para entender elementos-chave
        if entidades:
            historico_parts.append("")
            historico_parts.append("ENTIDADES IDENTIFICADAS:")
            for entidade in entidades:
                historico_parts.append(f"- {entidade}")

        # Intents detectados - para entender intenções passadas
        if intents:
            historico_parts.append("")
            historico_parts.append("INTENÇÕES PREVIAMENTE DETECTADAS:")
            for intent in intents:
                historico_parts.append(f"- {intent}")

        # Conteúdo das mensagens - para entendimento da conversa
        if mensagens:
            historico_parts.append("")
            historico_parts.append("HISTÓRICO DA CONVERSA:")
            for i, msg in enumerate(mensagens, 1):
                historico_parts.append(f"{i}. {msg}")
        else:
            historico_parts.append("")
            historico_parts.append("HISTÓRICO DA CONVERSA:")
            historico_parts.append("Nenhuma mensagem anterior disponível.")

        return "\n".join(historico_parts)

    @traceable(name="AnaliseMensage")
    def _run(self, parameters: AnaliseMensageParameters) -> RespostaBot:
        try:
            logger.debug("Iniciando _run de AnaliseMensageDatasource")
            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )
            logger.debug(
                f"Histórico formatado (tamanho: {len(historico_formatado)})"
            )

            fluxos_disponiveis = self._formatar_fluxos_disponiveis(
                parameters.fluxos_disponiveis
            )
            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            dia_semana = datetime.now().strftime("%A")

            # Carrega regras de resposta externalizadas ou usa fallback
            regras_resposta = SERVICEHUB.PROMPT_REGRAS_RESPOSTA
            msg_fallback = SERVICEHUB.MSG_FALLBACK_SEM_INFO
            if not regras_resposta:
                regras_resposta = (
                    "### Regras de Resposta (siga rigorosamente):\n"
                    "1. **Fonte da Resposta:** Baseie sua resposta "
                    "exclusivamente nas informações contidas no bloco "
                    "<contexto_rag>. O <historico_conversa> pode ser usado "
                    "apenas para compreender a intenção do usuário, mas nunca "
                    "como fonte de informação factual.\n"
                    "2. **Informação Incorreta:** Se o <contexto_rag> não "
                    "contiver informações relacionadas a <pergunta_usuario>, "
                    f'responda exatamente: "{msg_fallback}"\n'
                    "3. **Linguagem e Estilo:** Responda sempre em português. "
                    "A resposta deve ser concisa (máximo de 5 frases), "
                    "objetiva e educada.\n"
                    "4. **Fidelidade ao Contexto:** Não invente, deduza ou "
                    "adicione informações que não estejam explicitamente "
                    "presentes no <contexto_rag>.\n"
                    "5. **Análise de Transferência:** Analise se o usuário "
                    "precisa ser transferido para um setor específico com base "
                    "nos setores disponíveis listados abaixo.\n"
                    "6. **Regra de Transferência:** Se identificar que uma "
                    "transferência é necessária, preencha o campo "
                    "'acao_transferencia' com o NOME EXATO do setor.\n"
                )

            # Carrega template user RAG externalizado ou usa fallback
            template_user_rag = SERVICEHUB.PROMPT_TEMPLATE_USER_RAG
            if not template_user_rag:
                template_user_rag = (
                    "<historico_conversa>\n"
                    "(Apenas para referência de contexto, não como fonte "
                    "factual)\n"
                    "{historico_context}\n"
                    "</historico_conversa>\n\n"
                    "<contexto_rag>\n"
                    "### Apresentação da Empresa:\n"
                    "{dados_empresa}\n\n"
                    "### Dados do Treinamento:\n"
                    "{dados_treinamento}\n"
                    "</contexto_rag>\n\n"
                    "<pergunta_usuario>\n"
                    "{context}\n"
                    "</pergunta_usuario>\n\n"
                    "Com base apenas nas regras acima, elabore a resposta "
                    "final ao usuário."
                )

            messages_spec: list[tuple[str, str]] = [
                (
                    "system",
                    (
                        f"Data e Hora Atual: {data_atual} - {dia_semana}\n\n"
                        f"{parameters.llm_parameters.prompt_system}\n\n"
                        f"{parameters.llm_parameters.prompt_human}\n\n"
                        f"{regras_resposta}"
                        f"{fluxos_disponiveis}"
                    ),
                ),
                (
                    "user",
                    template_user_rag,
                ),
            ]
            # Log do prompt completo para debug formatado
            prompt_completo = "=" * 80 + "\n"
            prompt_completo += "PROMPT COMPLETO ENVIADO PARA LLM\n"
            prompt_completo += "=" * 80 + "\n"

            for i, (role, content) in enumerate(messages_spec, 1):
                prompt_completo += f"\n{'=' * 60}\n"
                prompt_completo += f"MESSAGE {i} - ROLE: {role.upper()}\n"
                prompt_completo += f"{'=' * 60}\n"
                prompt_completo += f"{content}\n"

            prompt_completo += f"\n{'=' * 80}\n"
            prompt_completo += "FIM DO PROMPT\n"
            prompt_completo += f"{'=' * 80}"

            logger.info(prompt_completo)

            messages = ChatPromptTemplate.from_messages(messages_spec)
            llm = parameters.llm_parameters.create_llm

            # Usa Structured Output para extrair resposta estruturada
            structured_llm = llm.with_structured_output(RespostaBot)
            chain = messages | structured_llm

            invoke_data = {
                "historico_context": historico_formatado,
                "dados_empresa": parameters.dados_empresa,
                "dados_treinamento": parameters.dados_treinamento,
                "context": parameters.llm_parameters.context,
            }

            logger.debug("Invocando LLM com Structured Output...")
            resultado: RespostaBot = chain.invoke(invoke_data)
            logger.debug(
                f"Resposta estruturada: resposta_texto={resultado.resposta_texto[:50]}..., "
                f"acao_transferencia={resultado.acao_transferencia}, "
                f"confianca={resultado.confianca}"
            )

            return resultado

        except Exception as e:
            logger.error(f"Erro ao processar análise de mensagem: {e}")
            raise
