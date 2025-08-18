import re

from langchain_core.prompts import ChatPromptTemplate

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LlmParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import ACData


class AnaliseConteudoLangchainDatasource(ACData):
    """Datasource para interagir com um LLM usando a biblioteca Langchain.

    Esta classe constrói um prompt a partir dos parâmetros, envia para o LLM
    configurado e processa a resposta, removendo tags de pensamento.
    """

    def __call__(self, parameters: LlmParameters) -> str:
        """Executa a chamada para o LLM.

        Args:
            parameters (LlmParameters): Parâmetros contendo o modelo, prompts
                e contexto para a chamada.

        Returns:
            str: A resposta do LLM como uma string limpa.

        Raises:
            TypeError: Se a resposta do LLM não for uma string.
        """
        llm = parameters.create_llm

        messages = ChatPromptTemplate.from_messages(
            [
                ("system", parameters.prompt_system),
                ("human", "{prompt_human}: {context}"),
            ]
        )

        chain = messages | llm

        response = chain.invoke(
            {
                "prompt_human": parameters.prompt_human,
                "context": parameters.context,
            }
        ).content

        if isinstance(response, str):
            # ✅ Filtrar tags <think> e </think>
            cleaned_response = re.sub(
                r"<think>.*?</think>", "", response, flags=re.DOTALL
            )

            return cleaned_response.strip()
        else:
            raise TypeError(
                f"Resposta do LLM deve ser uma string, mas recebeu: {type(response)}"
            )
