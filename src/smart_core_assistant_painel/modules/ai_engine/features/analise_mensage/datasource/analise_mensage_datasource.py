from datetime import datetime
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseMensageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import AMData


class AnaliseMensageDatasource(AMData):
    def __call__(self, parameters: AnaliseMensageParameters) -> str:
        result: str = self._run(parameters)
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

        fluxos_info += (
            "\n### REGRAS DE TRANSFERÊNCIA:\n"
            "1. Analise a intenção do usuário e verifique se há um setor específico adequado\n"
            "2. Se houver um setor correspondente exato na lista acima, use-o\n"
            "3. Se não houver correspondência exata, escolha o setor mais próximo\n"
            "4. Use sempre o nome exato do setor conforme listado acima\n"
            "5. A transferência deve ser mencionada apenas se for realmente necessária\n"
        )

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
    def _run(self, parameters: AnaliseMensageParameters) -> str:
        try:
            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )

            fluxos_disponiveis = self._formatar_fluxos_disponiveis(
                parameters.fluxos_disponiveis
            )
            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            dia_semana = datetime.now().strftime("%A")
            messages_spec: list[tuple[str, str]] = [
                (
                    "system",
                    (
                        f"Data e Hora Atual: {data_atual} - {dia_semana}\n\n"
                        f"{parameters.llm_parameters.prompt_system}\n\n"
                        f"{parameters.llm_parameters.prompt_human}\n\n"
                        "### Regras de Resposta (siga rigorosamente):\n"
                        "1. **Fonte da Resposta:** Baseie sua resposta exclusivamente nas informações contidas no bloco <contexto_rag>. "
                        "O <historico_conversa> pode ser usado apenas para compreender a intenção do usuário, mas nunca como fonte de informação factual.\n"
                        "2. **Informação Incorreta:** Se o <contexto_rag> não contiver informações relacionadas a <pergunta_usuario>, "
                        'responda exatamente: "Desculpe, não encontrei informações relacionadas à sua pergunta."\n'
                        "3. **Linguagem e Estilo:** Responda sempre em português. A resposta deve ser concisa (máximo de 5 frases), objetiva e educada.\n"
                        "4. **Fidelidade ao Contexto:** Não invente, deduza ou adicione informações que não estejam explicitamente presentes no <contexto_rag>.\n"
                        "5. **Análise de Transferência:** Analise se o usuário precisa ser transferido para um setor específico com base nos setores disponíveis listados abaixo.\n"
                        "6. **Regra de Transferência:** Se identificar que uma transferência é necessária, responda exatamente: 'Estarei transferindo seu atendimento para [NOME EXATO DO SETOR]'.\n"
                        f"{fluxos_disponiveis}"
                    ),
                ),
                (
                    "user",
                    (
                        "<historico_conversa>\n"
                        "(Apenas para referência de contexto, não como fonte factual)\n"
                        "{historico_context}\n"
                        "</historico_conversa>\n\n"
                        "<contexto_rag>\n"
                        "{dados_treinamento}\n"
                        "</contexto_rag>\n\n"
                        "<pergunta_usuario>\n"
                        "{context}\n"
                        "</pergunta_usuario>\n\n"
                        "Com base apenas nas regras acima, elabore a resposta final ao usuário."
                    ),
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
            parser = StrOutputParser()
            chain = messages | llm | parser
            invoke_data = {
                "historico_context": historico_formatado,
                "dados_treinamento": parameters.dados_treinamento,
                "context": parameters.llm_parameters.context,
            }
            resposta_bot = chain.invoke(invoke_data)

            return resposta_bot

        except Exception as e:
            logger.error(f"Erro ao processar análise prévia: {e}")
            raise
