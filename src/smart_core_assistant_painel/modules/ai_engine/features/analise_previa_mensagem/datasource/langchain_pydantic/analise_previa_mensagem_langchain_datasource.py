from typing import Any, cast

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel

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
            # O with_structured_output sempre retorna uma instância da classe BaseModel
            pydantic_response = cast(BaseModel, response)
            intent_dicts = [
                {str(item.type): item.value} for item in pydantic_response.intent  # type: ignore[attr-defined]
            ]

            entity_dicts = [
                {str(item.type): item.value} for item in pydantic_response.entities  # type: ignore[attr-defined]
            ]

            # Criar instância de AnalisePreviaMensagem
            resultado = AnalisePreviaMensagemLangchain(
                intent=intent_dicts, entities=entity_dicts
            )

            return resultado

        except Exception as e:
            logger.error(f"Erro ao processar análise prévia: {e}")
            raise

    def _formatar_historico_atendimento(self, historico_atendimento: dict[str, Any]) -> str:
        """
        Formata o histórico do atendimento para contexto do prompt.
        
        Processa todas as mensagens do histórico (não apenas as últimas 10) e inclui
        intents detectados e entidades extraídas quando disponíveis.

        Args:
            historico_atendimento: Dicionário com dados do histórico do atendimento
                Esperado: {
                    "conteudo_mensagens": ["mensagem1", "mensagem2", ...],
                    "intents_detectados": [
                        {"tipo": "saudacao", "confianca": 0.95}, ...
                    ],
                    "entidades_extraidas": [
                        {"entidade": "nome", "valor": "João", "posicao": [0, 4]}, ...
                    ]
                }

        Returns:
            String formatada para o contexto contendo:
            - HISTÓRICO DO ATENDIMENTO: Lista numerada de todas as mensagens
            - INTENTS DETECTADOS: Lista de intents com confiança (se disponível)
            - ENTIDADES EXTRAÍDAS: Lista de entidades com valores e posições (se disponível)
            Ou mensagem indicando ausência de histórico
        """
        try:
            # Busca por conteúdo de mensagens na estrutura do dicionário
            conteudo_mensagens = historico_atendimento.get("conteudo_mensagens", [])
            intents_detectados = historico_atendimento.get("intents_detectados", [])
            entidades_extraidas = historico_atendimento.get("entidades_extraidas", [])
            
            # Se não há mensagens, retorna mensagem padrão
            if not conteudo_mensagens:
                return "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."
            
            # Formata todas as mensagens (não apenas as últimas 10)
            historico_texto = "HISTÓRICO DO ATENDIMENTO:\n"
            for i, mensagem in enumerate(conteudo_mensagens, 1):
                historico_texto += f"{i}. {mensagem}\n"
            
            # Adiciona intents detectados se disponíveis
            if intents_detectados:
                historico_texto += "\nINTENTS DETECTADOS:\n"
                for intent in intents_detectados:
                    if isinstance(intent, dict):
                        tipo = intent.get("tipo", "")
                        confianca = intent.get("confianca", "")
                        historico_texto += f"- {tipo} (confiança: {confianca})\n"
                    else:
                        historico_texto += f"- {intent}\n"
            
            # Adiciona entidades extraídas se disponíveis
            if entidades_extraidas:
                historico_texto += "\nENTIDADES EXTRAÍDAS:\n"
                for entidade in entidades_extraidas:
                    if isinstance(entidade, dict):
                        nome = entidade.get("entidade", "")
                        valor = entidade.get("valor", "")
                        posicao = entidade.get("posicao", "")
                        historico_texto += f"- {nome}: {valor} (posição: {posicao})\n"
                    else:
                        historico_texto += f"- {entidade}\n"
            
            return historico_texto.strip()

        except Exception as format_error:
            logger.warning(
                f"Erro ao formatar histórico, usando fallback: {format_error}"
            )
            return (
                "HISTÓRICO DO ATENDIMENTO:\nNenhum histórico de mensagens disponível."
            )
