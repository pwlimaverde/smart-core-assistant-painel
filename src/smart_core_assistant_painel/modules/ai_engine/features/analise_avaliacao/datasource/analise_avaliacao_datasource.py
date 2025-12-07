from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from py_return_success_or_error import ErrorReturn, SuccessReturn

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseAvaliacaoParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    AAData,
    AnaliseAvaliacao,
)

PROMPT_SYSTEM = """Você é um especialista em análise de satisfação do cliente (CSAT/NPS).
Sua tarefa é analisar a resposta do usuário a uma solicitação de feedback e extrair:
1. A nota numérica (se presente).
2. O sentimento (positivo, negativo, neutro).
3. O feedback textual original.

REGRAS:
- Extraia a nota EXATAMENTE como o usuário escreveu (ex: 10, 5, 3.5). Se for texto (ex: "cinco"), converta para número.
- Se não houver nota explícita, tente inferir pelo sentimento (Muito Bom=5, Bom=4, Regular=3, Ruim=2, Péssimo=1), mas a prioridade é o número.
- Se não conseguir identificar nota, use 0 ou -1 para indicar ausência (o sistema tratará).
"""

PROMPT_HUMAN = """Histórico da conversa recentes (foco na última mensagem do usuário):
{chat_history}

Analise a última resposta do usuário."""


class AnaliseAvaliacaoDatasource(AAData):
    def __call__(
        self, parameters: AnaliseAvaliacaoParameters
    ) -> SuccessReturn[AnaliseAvaliacao] | ErrorReturn:
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

            result: AnaliseAvaliacao = chain.invoke({"chat_history": chat_str})

            return SuccessReturn(success=result)

        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - {str(e)}"
            return ErrorReturn(result=error)
