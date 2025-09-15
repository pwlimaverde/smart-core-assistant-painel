import re
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

            # Calcular confiabilidade da resposta (0 a 1)
            confiabilidade: float = self._compute_reliability(
                str(resposta_bot),
                parameters.dados_treinamento or "",
                parameters.llm_parameters.context or "",
            )

            logger.info(f"Confiabilidade calculada: {confiabilidade:.2f}")

            return AnaliseMensagemLangchain(
                resposta_bot=resposta_bot,
                confiabilidade=confiabilidade,
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

    def _compute_reliability(self, answer: str, rag_context: str, user_question: str) -> float:
        """Calcula um score de confiabilidade (0.0 a 1.0) para a resposta.

        Heurística utilizada:
        - Similaridade léxica (Jaccard) entre a resposta e o contexto RAG.
        - Penalização por respostas longas (> 5 frases).
        - Penalização por sobreposição excessiva com a pergunta.
        - Penalização quando números da resposta não estão no contexto; pequeno
        bônus quando todos os números da resposta estão no contexto.
        - Teto (cap) de confiança quando o contexto é curto.

        Args:
            answer: Resposta gerada pela LLM (texto).
            rag_context: Texto do contexto RAG utilizado na pergunta.
            user_question: Pergunta original do usuário.

        Returns:
            float: Score de confiabilidade normalizado entre 0.0 e 1.0.
        """
        # Caso especial: resposta padrão de falta de informação => 0.0
        lower = answer.lower()
        if (
            "desculpe, não encontrei informações suficientes" in lower
        ):
            return 0.0

        # Tokenização simples com remoção de stopwords comuns em PT-BR
        def _tok(s: str) -> set[str]:
            tokens = re.findall(r"\b\w+\b", s.lower())
            stop = {
                "de", "da", "do", "das", "dos", "em", "um",
                "uma", "e", "a", "o", "para", "com", "no",
                "na", "que", "se", "por", "as", "os", "ao",
                "à", "às", "uns", "umas", "sua", "seu", "suas",
                "seus", "é", "ser", "foi", "são", "tem", "ter",
                "há", "como", "mais", "menos", "muito", "muita",
                "muitos", "muitas", "já", "também",
            }
            return {t for t in tokens if len(t) > 2 and t not in stop}

        ans_tokens = _tok(answer)
        ctx_tokens = _tok(rag_context or "")
        q_tokens = _tok(user_question or "")

        inter = ans_tokens & ctx_tokens
        union = ans_tokens | ctx_tokens
        jaccard = (len(inter) / len(union)) if union else 0.0

        # Penalização por respostas muito longas (> 5 frases)
        sent_count = len(re.findall(r"[\.!\?…]+", answer))
        length_penalty = max(0.0, min(0.5, 0.1 * max(0, sent_count - 5)))

        # Penalização por copiar excessivamente a pergunta
        overlap_question = (
            (len(ans_tokens & q_tokens) / len(ans_tokens)) if ans_tokens else 0.0
        )
        question_penalty = 0.0
        if overlap_question > 0.6:
            question_penalty = min(0.3, (overlap_question - 0.6) * 0.75)

        # Checagem de números: penaliza números na resposta não presentes no contexto
        nums_answer = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", answer))
        nums_context = set(
            re.findall(r"\b\d+(?:[\.,]\d+)?\b", rag_context or "")
        )
        numbers_penalty = 0.0
        if nums_answer:
            if nums_answer - nums_context:
                numbers_penalty = 0.2
            else:
                # Pequeno bônus se todos os números da resposta estão no contexto
                numbers_penalty = -0.05

        # Limite superior em caso de contexto muito curto
        ctx_len = len(ctx_tokens)
        cap = 1.0
        if ctx_len < 20:
            cap = 0.6
        elif ctx_len < 50:
            cap = 0.8

        # Score base: alinhamento com o contexto e presença de termos do contexto
        base = 0.7 * jaccard + 0.3 * min(1.0, len(inter) / 10.0)

        score = max(0.0, base - length_penalty - question_penalty - numbers_penalty)
        return max(0.0, min(cap, score))
