import json
import re
from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import APMData


class AnalisePreviaMensagemSmallLLMDatasource(APMData):
    """
    Datasource otimizado para modelos de IA menores locais como llama3.2:3b.

    Esta implementação usa uma abordagem mais simples sem function calling,
    focando em prompts diretos e parsing de resposta JSON para garantir
    compatibilidade com modelos menores que podem ter limitações em
    structured output.
    """

    def __call__(
        self, parameters: AnalisePreviaMensagemParameters
    ) -> AnalisePreviaMensagemLangchain:
        """
        Processa análise prévia de mensagem usando modelo pequeno local.

        Args:
            parameters: Parâmetros de configuração da análise

        Returns:
            Resultado da análise com intents e entities extraídas
        """
        try:
            # Processar histórico do atendimento
            historico_formatado = self._formatar_historico_atendimento(
                parameters.historico_atendimento
            )

            # Criar prompt otimizado para modelos menores
            prompt_completo = self._criar_prompt_otimizado(
                parameters, historico_formatado
            )

            # Configurar template de mensagens simples
            messages = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Você é um assistente especializado em análise de mensagens. Responda APENAS com JSON válido no formato solicitado.",
                    ),
                    ("user", "{prompt_completo}"),
                ]
            )

            # Usar LLM sem structured output para compatibilidade
            llm = parameters.llm_parameters.create_llm

            # Chain simples
            chain = messages | llm

            # Invocar com dados preparados
            response = chain.invoke({"prompt_completo": prompt_completo})

            # Extrair conteúdo da resposta
            if hasattr(response, "content"):
                response_text = response.content
            else:
                response_text = str(response)

            # Fazer parsing da resposta JSON
            resultado_parsed = self._parse_response_json(response_text)

            # Converter para formato esperado
            resultado = AnalisePreviaMensagemLangchain(
                intent=resultado_parsed.get("intent", []),
                entities=resultado_parsed.get("entities", []),
            )

            logger.info(
                f"✅ Análise concluída - Intents: {len(resultado.intent)}, Entities: {len(resultado.entities)}"
            )
            return resultado

        except Exception as e:
            logger.error(f"Erro ao processar análise prévia com modelo pequeno: {e}")
            # Retornar resultado vazio em caso de erro
            return AnalisePreviaMensagemLangchain(intent=[], entities=[])

    def _criar_prompt_otimizado(
        self, parameters: AnalisePreviaMensagemParameters, historico_formatado: str
    ) -> str:
        """
        Cria prompt otimizado para modelos menores com instruções claras.

        Args:
            parameters: Parâmetros da análise
            historico_formatado: Histórico formatado do atendimento

        Returns:
            Prompt completo otimizado
        """
        # Extrair tipos válidos dos JSONs
        intent_types = self._extrair_tipos_validos(parameters.valid_intent_types)
        entity_types = self._extrair_tipos_validos(parameters.valid_entity_types)

        prompt = f"""{parameters.llm_parameters.prompt_system}

## TIPOS VÁLIDOS DISPONÍVEIS:

### INTENTS VÁLIDOS:
{", ".join(intent_types) if intent_types else "Nenhum tipo específico definido"}

### ENTITIES VÁLIDOS:
{", ".join(entity_types) if entity_types else "Nenhum tipo específico definido"}

## CONTEXTO DO ATENDIMENTO:
{historico_formatado}

## MENSAGEM ATUAL PARA ANÁLISE:
{parameters.llm_parameters.context}

## FORMATO DE RESPOSTA OBRIGATÓRIO:
Responda APENAS com um JSON válido no seguinte formato exato:
{{
    "intent": [
        {{"type": "tipo_intent", "value": "texto_extraído"}}
    ],
    "entities": [
        {{"type": "tipo_entity", "value": "valor_extraído"}}
    ]
}}

IMPORTANTE:
- Use APENAS os tipos listados acima
- Ambas as listas podem ser vazias []
- Seja conservador: prefira listas vazias a identificações duvidosas
- Responda APENAS com o JSON, sem texto adicional"""

        return prompt

    def _extrair_tipos_validos(self, types_json: str) -> List[str]:
        """
        Extrai lista de tipos válidos do JSON de configuração.

        Args:
            types_json: JSON string com tipos válidos

        Returns:
            Lista de tipos válidos
        """
        try:
            data = json.loads(types_json)
            tipos = []

            # Navegar pela estrutura JSON para extrair tipos
            for categoria in data.values():
                if isinstance(categoria, dict):
                    tipos.extend(categoria.keys())

            return tipos
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Erro ao extrair tipos válidos: {e}")
            return []

    def _parse_response_json(
        self, response_text: str
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Faz parsing da resposta JSON do modelo, com fallbacks para casos problemáticos.

        Args:
            response_text: Texto de resposta do modelo

        Returns:
            Dicionário com intent e entities parseados
        """
        try:
            # Tentar extrair JSON da resposta
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
                resultado = json.loads(json_text)

                # Validar estrutura
                if isinstance(resultado, dict):
                    intent = resultado.get("intent", [])
                    entities = resultado.get("entities", [])

                    # Garantir que são listas
                    if not isinstance(intent, list):
                        intent = []
                    if not isinstance(entities, list):
                        entities = []

                    # Validar estrutura dos itens
                    intent_valido = self._validar_items_lista(intent)
                    entities_valido = self._validar_items_lista(entities)

                    return {"intent": intent_valido, "entities": entities_valido}

            logger.warning("Não foi possível extrair JSON válido da resposta")
            return {"intent": [], "entities": []}

        except json.JSONDecodeError as e:
            logger.warning(f"Erro ao fazer parsing do JSON: {e}")
            return {"intent": [], "entities": []}
        except Exception as e:
            logger.error(f"Erro inesperado no parsing: {e}")
            return {"intent": [], "entities": []}

    def _validar_items_lista(self, items: List[Any]) -> List[Dict[str, str]]:
        """
        Valida e limpa itens de uma lista de intent/entities.

        Args:
            items: Lista de itens para validar

        Returns:
            Lista validada com estrutura correta
        """
        items_validos = []

        for item in items:
            if isinstance(item, dict) and "type" in item and "value" in item:
                # Garantir que type e value são strings
                tipo = str(item["type"]).strip()
                valor = str(item["value"]).strip()

                if tipo and valor:  # Não aceitar valores vazios
                    items_validos.append({"type": tipo, "value": valor})

        return items_validos

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
