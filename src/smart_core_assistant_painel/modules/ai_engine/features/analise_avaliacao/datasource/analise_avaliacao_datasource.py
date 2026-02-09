from langchain_core.prompts import ChatPromptTemplate
from py_return_success_or_error import ErrorReturn

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseAvaliacaoParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    AAData,
    AnaliseAvaliacao,
)

PROMPT_SYSTEM = """Você é um especialista em análise de satisfação do cliente.
Sua tarefa é analisar a resposta do usuário a uma solicitação de feedback e extrair:
1. A nota numérica (1 a 5).
2. O sentimento (apenas 'positivo' ou 'negativo').
3. O feedback textual.

REGRAS:
- Nota: Extraia o número 1-5. Se for > 5, normalize (ex: 10 -> 5). Se não houver número, infira pelo sentimento (Positivo=5, Negativo=1).
- Sentimento: Classifique estritamente como 'positivo' (notas 4-5 ou elogios) ou 'negativo' (notas 1-3 ou críticas). Evite 'neutro'.
- Feedback: Extraia o texto explicativo. Se for apenas a nota, retorne None.
"""

PROMPT_HUMAN = """Histórico da conversa recentes (foco na última mensagem do usuário):
{chat_history}

Analise a última resposta do usuário."""


class AnaliseAvaliacaoDatasource(AAData):
    def __call__(
        self, parameters: AnaliseAvaliacaoParameters
    ) -> AnaliseAvaliacao | ErrorReturn:
        try:
            llm = parameters.llm_parameters.create_llm
            structured_llm = llm.with_structured_output(AnaliseAvaliacao)

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", PROMPT_SYSTEM),
                    ("human", PROMPT_HUMAN),
                ]
            )

            chain = prompt | structured_llm

            # Converter chat_history para string ou formato adequado se necessário
            # Assumindo que parameters.chat_history é uma lista de BaseMessage
            # O prompt espera uma string ou lista de mensagens.
            # Vamos passar como string formatada para garantir.
            chat_str = "\n".join(
                [
                    f"{msg.type}: {msg.content}"
                    for msg in parameters.chat_history
                ]
            )

            result: AnaliseAvaliacao = chain.invoke({"chat_history": chat_str})  # type: ignore

            return result

        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - {str(e)}"
            return ErrorReturn(error)
