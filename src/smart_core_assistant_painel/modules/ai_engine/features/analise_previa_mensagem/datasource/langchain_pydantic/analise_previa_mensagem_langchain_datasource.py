from typing import Any, Dict, Iterable, List

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
    """Datasource para extrair intenções e entidades usando LLM com Langchain.

    Esta classe utiliza a funcionalidade de 'structured output' da Langchain
    para forçar o LLM a retornar uma resposta em um formato Pydantic
    específico, garantindo a extração confiável de dados.
    """

    def __call__(
        self, parameters: AnalisePreviaMensagemParameters
    ) -> AnalisePreviaMensagemLangchain:
        """Executa a extração de intenções e entidades.

        O método cria dinamicamente um modelo Pydantic a partir das intenções
        e entidades válidas, formata um prompt com o histórico da conversa e
        o texto atual, e invoca um LLM com 'structured output' para obter
        os dados estruturados.

        Args:
            parameters (AnalisePreviaMensagemParameters): Os parâmetros
                necessários, incluindo o histórico, texto, e configurações
                do LLM.

        Returns:
            AnalisePreviaMensagemLangchain: Um objeto contendo as listas de
                intenções e entidades extraídas.

        Raises:
            Exception: Propaga exceções que podem ocorrer durante a
                interação com o LLM ou na criação do modelo dinâmico.
        """
        try:
            # Criar modelo PydanticModel dinâmico baseado nos parâmetros
            PydanticModel = create_dynamic_pydantic_model(
                intent_types_json=parameters.valid_intent_types,
                entity_types_json=parameters.valid_entity_types,
            )

            # Log de prévia da documentação dinâmica gerada a partir dos JSONs
            # (limitada para evitar excesso de log)
            # doc = getattr(PydanticModel, "__doc__", "") or ""
            # if doc:
            #     preview = "\n".join(doc.splitlines())
            #     logger.debug(
            #         f"Prévia da documentação dinâmica (completa):\n{preview}"
            #     )
            # else:
            #     logger.warning(
            #         "Documentação dinâmica não encontrada em "
            #         "PydanticModel.__doc__"
            #     )

            # Processar histórico do atendimento
            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )

            # Seleção do system prompt:
            # - Prioriza o prompt_system vindo dos parâmetros (se fornecido)
            # - Usa a docstring do modelo como fallback
            # Observação: escapamos chaves para não conflitar com o template
            raw_system_prompt = (
                parameters.llm_parameters.prompt_system
                if getattr(parameters.llm_parameters, "prompt_system", None)
                else doc
            )
            system_prompt = raw_system_prompt.replace("{", "{{").replace("}", "}}")

            messages = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    (
                        "user",
                        "{historico_context}\n\n{prompt_human}: {context}",
                    ),
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

            # Pós-processamento: conversão simples mantendo itens válidos
            intent_data = getattr(response, "intent", [])
            entities_data = getattr(response, "entities", [])

            intent_dicts = self._filter_and_convert_items(intent_data)
            entity_dicts = self._filter_and_convert_items(entities_data)

            # Criar instância de AnalisePreviaMensagem
            resultado = AnalisePreviaMensagemLangchain(
                intent=intent_dicts, entities=entity_dicts
            )

            return resultado

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

    def _filter_and_convert_items(
        self, items: Iterable[Any]
    ) -> List[Dict[str, str]]:
        """Converte itens válidos no formato {type: value}.

        - Mantém somente itens cujo `type` e `value` existam e sejam strings
          não vazias (após strip).
        - Converte cada item válido para o formato {type: value}.
        - Ignora itens inválidos; quando nenhum for válido, retorna lista vazia.

        Args:
            items: Iterável de objetos com atributos `type` e `value`.

        Returns:
            Lista de dicionários convertidos com pares {type: value}.
        """
        results: List[Dict[str, str]] = []
        if not items:
            return results

        for item in items:
            try:
                item_type = getattr(item, "type", None)
                item_value = getattr(item, "value", None)
                if item_type is None or item_value is None:
                    continue
                type_str = str(item_type).strip()
                value_str = str(item_value).strip()
                if not type_str or not value_str:
                    continue
                # Conversão simples sem exigir literalidade no contexto
                results.append({type_str: value_str})
            except Exception as exc:  # proteção defensiva
                # Log em nível debug para não poluir saída de produção
                logger.debug(f"Falha ao processar item '{item}': {exc}")
                continue
        return results
