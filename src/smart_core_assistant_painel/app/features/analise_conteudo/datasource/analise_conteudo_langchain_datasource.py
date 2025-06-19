

import re

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from smart_core_assistant_painel.utils.parameters import LlmParameters
from smart_core_assistant_painel.utils.types import ACData


class AnaliseConteudoLangchainDatasource(ACData):

    def __call__(self, parameters: LlmParameters) -> str:
        logger.warning('inicio do datasource analise_conteudo')
        llm = parameters.create_llm
        logger.warning('llm criado com sucesso')

        messages = ChatPromptTemplate.from_messages([
            ('system', parameters.prompt_system),
            ('human', '{prompt_human}: {context}')
        ])
        logger.warning('messages criado com sucesso')
        logger.warning(f'messages {messages.messages}')
        chain = messages | llm
        logger.warning('chain criado com sucesso')
        logger.warning(f'chain {chain}')

        response = chain.invoke(
            {'prompt_human': parameters.prompt_human, 'context': parameters.context, }).content
        logger.error(f"Resposta do LLM: {response}")
        if isinstance(response, str):
            # ✅ Filtrar tags <think> e </think>
            cleaned_response = re.sub(
                r'<think>.*?</think>',
                '',
                response,
                flags=re.DOTALL)

            return cleaned_response.strip()
        else:
            raise TypeError(
                f"Resposta do LLM deve ser uma string, mas recebeu: {
                    type(response)}")
