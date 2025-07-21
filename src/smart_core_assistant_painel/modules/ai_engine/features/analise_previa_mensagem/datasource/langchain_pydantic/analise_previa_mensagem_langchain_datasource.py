from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain, )
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import APMData


class AnalisePreviaMensagemLangchainDatasource(APMData):

    def __call__(
            self,
            parameters: AnalisePreviaMensagemParameters) -> AnalisePreviaMensagemLangchain:

        try:
            # Processar histórico do atendimento
            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )

            # Escapar chaves JSON no prompt system para evitar conflito com
            # variáveis do template
            prompt_system_escaped = parameters.llm_parameters.prompt_system.replace(
                '{', '{{').replace('}', '}}')

            messages = ChatPromptTemplate.from_messages([
                ('system', prompt_system_escaped),
                ('user', '{historico_context}\n\n{prompt_human}: {context}')
            ])

            llm = parameters.llm_parameters.create_llm

            # Aplicar structured output diretamente no LLM
            structured_llm = llm.with_structured_output(
                AnalisePreviaMensagemLangchain, method="function_calling")

            # Chain com LLM estruturado
            chain = messages | structured_llm

            # Preparar dados para invocação com validação
            invoke_data = {
                'prompt_human': parameters.llm_parameters.prompt_human,
                'context': parameters.llm_parameters.context,
                'historico_context': historico_formatado,
            }

            # Debug: Log dos dados de entrada
            logger.debug(f"Prompt System: {prompt_system_escaped}")
            logger.debug(
                f"Prompt Human: {
                    parameters.llm_parameters.prompt_human}")
            logger.debug(f"Context: {parameters.llm_parameters.context}")
            logger.debug(f"Histórico formatado: {historico_formatado}")
            logger.debug(f"Invoke data: {invoke_data}")

            response = chain.invoke(invoke_data)

            logger.debug(
                f"Resposta da chain: {response} tipo: {
                    type(response)}")

            # Debug adicional: verificar conteúdo das listas
            if hasattr(response, 'intent'):
                logger.debug(
                    f"Intent encontrados: {len(response.intent)} itens: {response.intent}")
            if hasattr(response, 'entities'):
                logger.debug(
                    f"Entities encontradas: {len(response.entities)} itens: {response.entities}")

            if isinstance(response, AnalisePreviaMensagemLangchain):
                return response
            else:
                logger.warning(
                    f"Resposta não é AnalisePreviaMensagemLangchain: {
                        type(response)}")
                raise ValueError(
                    f"Resposta inesperada: {
                        type(response)}. Esperado: AnalisePreviaMensagemLangchain")

        except Exception as e:
            logger.error(f"Erro ao processar análise prévia: {e}")
            raise

    def _formatar_historico_atendimento(
            self, historico_atendimento: Any) -> str:
        """
        Formata o histórico do atendimento para contexto do prompt.

        Args:
            historico_atendimento: Lista de mensagens ou dados do histórico

        Returns:
            String formatada para o contexto ou mensagem indicando ausência
        """
        try:
            # Se for None, lista vazia ou falsy
            if not historico_atendimento:
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Se for uma lista vazia
            if isinstance(historico_atendimento, list) and len(
                    historico_atendimento) == 0:
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Se for uma lista com mensagens
            if isinstance(historico_atendimento, list):
                historico_texto = "HISTÓRICO DO ATENDIMENTO:\n"
                for i, mensagem in enumerate(
                        historico_atendimento[-10:], 1):  # Últimas 10 mensagens
                    if isinstance(mensagem, str):
                        historico_texto += f"{i}. {mensagem}\n"
                    elif isinstance(mensagem, dict):
                        conteudo = mensagem.get(
                            'conteudo', mensagem.get(
                                'texto', str(mensagem)))
                        remetente = mensagem.get('remetente', 'Usuario')
                        historico_texto += f"{i}. [{remetente}]: {conteudo}\n"
                    else:
                        historico_texto += f"{i}. {str(mensagem)}\n"
                return historico_texto.strip()

            # Se for um dicionário com estrutura específica
            if isinstance(historico_atendimento, dict):
                mensagens = historico_atendimento.get('mensagens', [])
                if mensagens:
                    return self._formatar_historico_atendimento(mensagens)
                else:
                    # Tentar outras chaves possíveis
                    conteudo = (historico_atendimento.get('conteudo_mensagens') or
                                historico_atendimento.get('historico') or
                                historico_atendimento.get('mensagens_anteriores', []))
                    if conteudo:
                        return self._formatar_historico_atendimento(conteudo)

                # Se chegou aqui, é um dicionário sem mensagens válidas
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Se for uma string (histórico já formatado)
            if isinstance(historico_atendimento, str):
                if historico_atendimento.strip():
                    return f"HISTÓRICO DO ATENDIMENTO:\n{historico_atendimento}"
                else:
                    return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Fallback: tentar converter para string
            try:
                historico_str = str(historico_atendimento)
                if historico_str and historico_str not in ['[]', '{}', 'None']:
                    return f"HISTÓRICO DO ATENDIMENTO:\n{historico_str}"
            except Exception:
                pass

            # Último recurso
            return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

        except Exception as format_error:
            logger.warning(
                f'Erro ao formatar histórico, usando fallback: {format_error}')
            return "HISTÓRICO DO ATENDIMENTO:\nErro ao processar histórico de mensagens."
