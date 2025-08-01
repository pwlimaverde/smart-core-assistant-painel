from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import APMData


class AnalisePreviaMensagemLangchainDatasource(APMData):
    def __call__(
        self, parameters: AnalisePreviaMensagemParameters
    ) -> AnalisePreviaMensagemLangchain:
        try:
            # Criar modelo PydanticModel dinâmico baseado nos parâmetros
            PydanticModel = create_dynamic_pydantic_model(
                intent_types_json=parameters.valid_intent_types,
                entity_types_json=parameters.valid_entity_types,
            )

            # Processar histórico do atendimento
            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )

            # Escapar chaves JSON no prompt system para evitar conflito com
            # variáveis do template
            prompt_system_escaped = parameters.llm_parameters.prompt_system.replace(
                "{", "{{"
            ).replace("}", "}}")

            messages = ChatPromptTemplate.from_messages(
                [
                    ("system", prompt_system_escaped),
                    ("user", "{historico_context}\n\n{prompt_human}: {context}"),
                ]
            )

            llm = parameters.llm_parameters.create_llm

            # Aplicar structured output
            structured_llm = llm.with_structured_output(PydanticModel)

            # Chain com LLM estruturado
            chain = messages | structured_llm

            # Preparar dados para invocação com validação
            invoke_data = {
                "prompt_human": parameters.llm_parameters.prompt_human,
                "context": parameters.llm_parameters.context,
                "historico_context": historico_formatado,
            }

            # Invocar a chain
            response = chain.invoke(invoke_data)

            # Converter PydanticModel para AnalisePreviaMensagem
            # Verificar se response é dict ou BaseModel e extrair dados adequadamente
            if isinstance(response, dict):
                # Se for dict, acessar como chaves
                intent_list = response.get("intent", [])
                entities_list = response.get("entities", [])
                # Converter para formato esperado se necessário
                intent_dicts = [
                    {str(item.get("type", "")): item.get("value", "")}
                    for item in intent_list
                    if isinstance(item, dict)
                ]
                entity_dicts = [
                    {str(item.get("type", "")): item.get("value", "")}
                    for item in entities_list
                    if isinstance(item, dict)
                ]
            else:
                # Se for BaseModel, verificar se tem os atributos necessários
                if hasattr(response, "intent") and hasattr(response, "entities"):
                    # Extrair intent como lista de dicionários {tipo: valor}
                    intent_dicts = [
                        {str(item.type): item.value} for item in response.intent
                    ]

                    # Extrair entities como lista de dicionários {tipo: valor}
                    entity_dicts = [
                        {str(item.type): item.value} for item in response.entities
                    ]
                else:
                    # Fallback para caso o BaseModel não tenha os atributos esperados
                    logger.warning(
                        f"BaseModel response não possui atributos 'intent' ou 'entities': {type(response)}"
                    )
                    intent_dicts = []
                    entity_dicts = []

            # Criar instância de AnalisePreviaMensagem
            resultado = AnalisePreviaMensagemLangchain(
                intent=intent_dicts, entities=entity_dicts
            )

            return resultado

        except Exception as e:
            logger.error(f"Erro ao processar análise prévia: {e}")
            raise

    def _formatar_historico_atendimento(self, historico_atendimento: Any) -> str:
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
            if (
                isinstance(historico_atendimento, list)
                and len(historico_atendimento) == 0
            ):
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."

            # Se for uma lista com mensagens
            if isinstance(historico_atendimento, list):
                historico_texto = "HISTÓRICO DO ATENDIMENTO:\n"
                for i, mensagem in enumerate(
                    historico_atendimento[-10:], 1
                ):  # Últimas 10 mensagens
                    if isinstance(mensagem, str):
                        historico_texto += f"{i}. {mensagem}\n"
                    elif isinstance(mensagem, dict):
                        conteudo = mensagem.get(
                            "conteudo", mensagem.get("texto", str(mensagem))
                        )
                        remetente = mensagem.get("remetente", "Usuario")
                        historico_texto += f"{i}. [{remetente}]: {conteudo}\n"
                    else:
                        historico_texto += f"{i}. {str(mensagem)}\n"
                return historico_texto.strip()

            # Se for um dicionário com estrutura específica
            if isinstance(historico_atendimento, dict):
                mensagens = historico_atendimento.get("mensagens", [])
                if mensagens:
                    return self._formatar_historico_atendimento(mensagens)
                else:
                    # Tentar outras chaves possíveis
                    conteudo = (
                        historico_atendimento.get("conteudo_mensagens")
                        or historico_atendimento.get("historico")
                        or historico_atendimento.get("mensagens_anteriores", [])
                    )
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
                if historico_str and historico_str not in ["[]", "{}", "None"]:
                    return f"HISTÓRICO DO ATENDIMENTO:\n{historico_str}"
            except Exception:
                pass

            # Último recurso
            return (
                "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."
            )

        except Exception as format_error:
            logger.warning(
                f"Erro ao formatar histórico, usando fallback: {format_error}"
            )
            return (
                "HISTÓRICO DO ATENDIMENTO:\nErro ao processar histórico de mensagens."
            )
