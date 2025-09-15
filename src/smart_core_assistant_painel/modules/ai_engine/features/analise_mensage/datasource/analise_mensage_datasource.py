from typing import Any

from ai_engine.features.analise_mensage.datasource.analise_mensagem_langchain import (
    AnaliseMensagemLangchain,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseMensageParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import AMData


class AnaliseMensageDatasource(AMData):
    def __call__(self, parameters: AnaliseMensageParameters) -> AnaliseMensagemLangchain:
        try:

            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )

            messages_spec: list[tuple[str, str]] = [
                ("system", (
                    f"{parameters.llm_parameters.prompt_system}\n\n"
                    f"{parameters.llm_parameters.prompt_human}\n\n"
                    "### Regras de Resposta (siga rigorosamente):\n"
                    "1. **Fonte da Resposta:** Baseie sua resposta exclusivamente nas informações contidas no bloco <contexto_rag>. "
                    "O <historico_conversa> pode ser usado apenas para compreender a intenção do usuário, mas nunca como fonte de informação factual.\n"
                    "2. **Informação Insuficiente:** Se o <contexto_rag> não contiver informações suficientes para responder à <pergunta_usuario>, "
                    "responda exatamente: \"Desculpe, não encontrei informações suficientes para responder. Vou transferir seu atendimento para o setor responsável.\"\n"
                    "3. **Linguagem e Estilo:** Responda sempre em português. A resposta deve ser concisa (máximo de 5 frases), objetiva e educada.\n"
                    "4. **Fidelidade ao Contexto:** Não invente, deduza ou adicione informações que não estejam explicitamente presentes no <contexto_rag>.\n"
                )),
                ("user", (
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
                )),
            ]

            messages = ChatPromptTemplate.from_messages(messages_spec)
            
            
            llm = parameters.llm_parameters.create_llm
            parser = StrOutputParser()
            # Chain com LLM estruturado
            chain = messages | llm | parser

            # Preparar dados para invocação com validação
            invoke_data = {
                "historico_context": historico_formatado,
                "dados_treinamento": parameters.dados_treinamento,
                "context": parameters.llm_parameters.context,
            }
            logger.info(f"Prompt: {messages.invoke(invoke_data)}")
            # Invocar a chain
            resposta_bot = chain.invoke(invoke_data)

            return AnaliseMensagemLangchain(
                resposta_bot=resposta_bot,
                confiabilidade=0.0,
            )

        except Exception as e:
            logger.error(f"Erro ao processar análise prévia: {e}")
            raise

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
