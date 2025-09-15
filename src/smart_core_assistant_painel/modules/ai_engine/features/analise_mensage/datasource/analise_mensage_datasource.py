import re
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.features.analise_mensage.datasource.analise_mensagem_langchain import (
    AnaliseMensagemLangchain,
)
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
                    "2. **Informação Incorreta:** Se o <contexto_rag> não contiver informações relacionadas a <pergunta_usuario>, "
                    "responda exatamente: \"Desculpe, não encontrei informações relacionadas à sua pergunta.\n"
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

    def _compute_reliability(
        self, answer: str, rag_context: str, user_question: str
    ) -> float:
        """Calcula um score de confiabilidade (0.0 a 1.0) para a resposta.

        Ajustado para basear a análise principalmente em ``dados_treinamento``
        (argumento ``rag_context``), incluindo também a aderência à pergunta
        do usuário. Avalia por blocos do contexto para evitar diluição quando
        o contexto é grande.

        Heurística utilizada:
        - Similaridade por bloco: precisão (|∩|/|ans|), Jaccard e suporte
          (|∩| normalizado), escolhendo o melhor bloco.
        - Penalização por respostas longas (> 5 frases).
        - Bônus/penalização baseados em números e horários presentes na
          resposta e no contexto (por bloco).
        - Teto (cap) de confiança quando o bloco de contexto é curto.

        Args:
            answer: Resposta gerada pela LLM (texto).
            rag_context: Texto do contexto RAG utilizado (dados_treinamento).
            user_question: Pergunta original (usada na avaliação de aderência).

        Returns:
            float: Score de confiabilidade normalizado entre 0.0 e 1.0.
        """
        # Caso especial: resposta padrão de falta de informação => 0.0
        lower = answer.lower()
        if (
            "não encontrei informações" in lower
        ):
            return 0.0

        # Palavras/expressões relacionadas a transferência de atendimento
        transfer_markers = {
            "transferir", "transferência", "transferencia", "transferido",
            "encaminhar", "encaminharei", "encaminhado", "encaminho",
            "vou transferir", "vou encaminhar", "direcionar", "direcionarei",
            "setor responsável", "setor responsavel", "equipe responsável",
            "equipe responsavel", "atendente humano", "suporte humano",
        }

        request_transfer_markers = {
            "transferir", "transferência", "transferencia", "encaminhar",
            "falar com atendente", "falar com humano", "setor responsável",
            "setor responsavel", "quero falar com", "transferência de atendimento",
        }

        user_lower = (user_question or "").lower()
        user_requested_transfer = any(m in user_lower for m in request_transfer_markers)

        # Tokenização simples com remoção de stopwords comuns em PT-BR e
        # termos genéricos que tendem a aparecer em saudações/respostas
        # educadas (evita diluir a métrica quando a resposta é correta).
        def _tok(s: str) -> set[str]:
            tokens = re.findall(r"\b\w+\b", s.lower())
            stop = {
                # Stopwords comuns
                "de", "da", "do", "das", "dos", "em", "um",
                "uma", "e", "a", "o", "para", "com", "no",
                "na", "que", "se", "por", "as", "os", "ao",
                "à", "às", "uns", "umas", "sua", "seu", "suas",
                "seus", "é", "ser", "foi", "são", "tem", "ter",
                "há", "como", "mais", "menos", "muito", "muita",
                "muitos", "muitas", "já", "também",
                # Termos genéricos/sociais
                "ola", "olá", "prazer", "conhecer", "duvida",
                "dúvida", "informacao", "informação", "precisar",
                "precise", "perguntar", "pergunta", "estou", "aqui",
                "ajudar", "posso", "ajuda", "obrigado", "obrigada",
            }
            return {t for t in tokens if len(t) > 2 and t not in stop}

        # Divide o contexto em blocos relevantes para reduzir diluição
        # por partes não relacionadas (ex.: separados por '---').
        def _split_blocks(s: str) -> list[str]:
            if not s:
                return []
            parts = re.split(r"\n?-{3,}\n?", s)
            parts = [p.strip() for p in parts if p.strip()]
            return parts or [s]

        ans_tokens = _tok(answer)
        ctx_blocks = _split_blocks(rag_context or "")
        question_tokens = _tok(user_question or "")

        # Padrões numéricos e horários (genéricos)
        time_pattern = r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b"
        num_pattern = r"\b\d+(?:[\.,]\d+)?\b"

        times_answer = set(re.findall(time_pattern, answer))
        nums_answer = set(re.findall(num_pattern, answer))

        # Penalização por respostas muito longas (> 5 frases)
        sent_count = len(re.findall(r"[\.!.?…]+", answer))
        length_penalty = max(0.0, min(0.5, 0.1 * max(0, sent_count - 5)))

        # Avalia por bloco e escolhe o melhor score
        best_score = 0.0
        best_content_score = 0.0
        best_question_coverage = 0.0
        max_intersection_tokens = 0

        # Se não houver blocos (contexto vazio), avalia uma vez com bloco
        # vazio para manter comportamento definido.
        blocks = ctx_blocks if ctx_blocks else [""]

        for block in blocks:
            ctx_tokens = _tok(block)
            inter = ans_tokens & ctx_tokens
            union = ans_tokens | ctx_tokens

            # Métricas principais por bloco
            jaccard = (len(inter) / len(union)) if union else 0.0
            precision = (
                (len(inter) / len(ans_tokens)) if ans_tokens else 0.0
            )
            support = min(1.0, len(inter) / 7.0)  # valoriza interseções curtas

            # Checagens numéricas/horários por bloco (genéricas)
            times_ctx = set(re.findall(time_pattern, block))
            nums_ctx = set(re.findall(num_pattern, block))

            times_alignment = (
                len(times_answer & times_ctx) / len(times_answer)
                if times_answer
                else 0.0
            )
            nums_alignment = (
                len(nums_answer & nums_ctx) / len(nums_answer)
                if nums_answer
                else 0.0
            )

            # Alinhamento estrutural médio quando existem elementos
            struct_parts = [
                p for p in (times_alignment, nums_alignment) if p > 0.0
            ]
            struct_alignment = (
                sum(struct_parts) / len(struct_parts)
                if struct_parts
                else 0.0
            )

            # Aderência da resposta à pergunta do usuário
            inter_q = ans_tokens & question_tokens
            question_coverage = (
                len(inter_q) / len(question_tokens)
                if question_tokens
                else 0.0
            )

            # Limite superior em caso de bloco muito curto
            ctx_len = len(ctx_tokens)
            cap = 1.0
            if ctx_len < 20:
                cap = 0.6
            elif ctx_len < 50:
                cap = 0.8

            # Score de conteúdo baseado no contexto
            content_score = 0.6 * precision + 0.25 * jaccard + 0.15 * support

            # Score estrutural valoriza aderência de números/horários, com
            # fallback para conteúdo quando não houver elementos estruturados
            structural_score = max(struct_alignment, 0.5 * content_score)

            # Composição final inclui aderência à pergunta do usuário
            combined = 0.7 * structural_score + 0.3 * question_coverage

            # Ajuste fino com números/horários
            if (times_answer and times_alignment >= 0.8) or (
                nums_answer and nums_alignment >= 0.8
            ):
                combined += 0.05
            elif (times_answer and times_alignment < 0.4) or (
                nums_answer and nums_alignment < 0.4
            ):
                combined -= 0.05

            # Penalização por tamanho da resposta
            combined -= length_penalty

            score_block = max(0.0, min(cap, combined))
            if score_block > best_score:
                best_score = score_block
                best_content_score = content_score
                best_question_coverage = question_coverage
                max_intersection_tokens = max(max_intersection_tokens, len(inter))

        # Regras de transferência de atendimento
        has_transfer = any(m in lower for m in transfer_markers)
        # Contexto suficiente: conteúdo forte + alguma cobertura da pergunta
        context_sufficient = (
            (best_content_score >= 0.5 and best_question_coverage >= 0.3)
            or max_intersection_tokens >= 2
            or best_score >= 0.6
        )

        # 1) Se o usuário pediu transferência => 0.0
        if user_requested_transfer:
            return 0.0

        # 2) Se há menção de transferência na resposta sem ter sido solicitada
        # trata como violação de política (transferência injustificada) => 0.0
        if has_transfer and not user_requested_transfer:
            return 0.0

        # 3) Se não há contexto suficiente => 0.0 para acionar fluxo correto
        if not context_sufficient:
            return 0.0

        return best_score
