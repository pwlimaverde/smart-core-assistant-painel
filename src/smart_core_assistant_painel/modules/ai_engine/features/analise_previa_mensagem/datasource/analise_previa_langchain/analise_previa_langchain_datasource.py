from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Tuple, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from loguru import logger
from pydantic import BaseModel

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.pydantic_model_builder import (
    build_analise_previa_model,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import APMData


class AnalisePreviaLangchainDatasource(APMData):
    """Datasource simplificado para análise de intenções e entidades.

    Mantém o comportamento dinâmico (schema Pydantic gerado em tempo de
    execução) com descrições e exemplos derivados da configuração atual.
    """

    def __call__(
        self, parameters: AnalisePreviaMensagemParameters
    ) -> AnalisePreviaMensagemLangchain:
        """Executa a análise com structured output, com fallback seguro.

        - Constrói modelo Pydantic dinâmico com descrições e exemplos.
        - Formata histórico do atendimento.
        - Tenta structured output via json_schema, com fallback para parsing.
        """
        try:
            # 1) Modelo dinâmico
            # Normaliza configurações de tipos (podem vir como string JSON)
            intent_types_json = self._normalize_types_config(
                parameters.valid_intent_types
            )
            entity_types_json = self._normalize_types_config(
                parameters.valid_entity_types
            )
            PydanticModel = build_analise_previa_model(
                intent_types_json=intent_types_json,
                entity_types_json=entity_types_json,
            )
            historico_formatado = self._format_service_history(
                parameters.historico_atendimento
            )
            doc = getattr(PydanticModel, "__doc__", "") or ""

            raw_system_prompt = (
                parameters.llm_parameters.prompt_system
                if getattr(parameters.llm_parameters, "prompt_system", None)
                else doc
            )
            system_prompt = raw_system_prompt.replace("{", "{{").replace(
                "}", "}}"
            )
            messages_spec: List[Tuple[str, str]] = [
                ("system", system_prompt),
                (
                    "user",
                    "{historico_context}\n\n{prompt_human}: {context}",
                ),
            ]
            messages: ChatPromptTemplate = ChatPromptTemplate.from_messages(  # type: ignore[reportUnknownMemberType]
                messages_spec
            )

            llm: BaseChatModel = parameters.llm_parameters.create_llm

            # 5) Structured output com preferencia por json_schema
            structured_llm: Runnable[Any, BaseModel | Dict[str, Any]] | None = None
            try:
                structured_llm = cast(
                    Runnable[Any, BaseModel | Dict[str, Any]],
                    llm.with_structured_output(  # type: ignore[reportUnknownMemberType]
                        PydanticModel, method="json_schema"
                    ),
                )
            except Exception as e_json_schema:
                logger.debug(
                    "with_structured_output json_schema falhou: "
                    f"{e_json_schema}"
                )
                try:
                    structured_llm = cast(
                        Runnable[Any, BaseModel | Dict[str, Any]],
                        llm.with_structured_output(PydanticModel),  # type: ignore[reportUnknownMemberType]
                    )
                except Exception as e_default:
                    logger.debug(
                        "with_structured_output padrão falhou: "
                        f"{e_default}"
                    )
                    structured_llm = None

            invoke_data = {
                "prompt_human": parameters.llm_parameters.prompt_human,
                "context": parameters.llm_parameters.context,
                "historico_context": historico_formatado,
            }

            response: Any | None = None
            if structured_llm is not None:
                try:
                    # Define o tipo explicitamente para evitar Unknown
                    chain: Runnable[Dict[str, Any], BaseModel | Dict[str, Any]] = cast(
                        Runnable[Dict[str, Any], BaseModel | Dict[str, Any]],
                        messages | structured_llm,
                    )
                    response = chain.invoke(invoke_data)
                except Exception as exc_structured:
                    logger.warning(
                        "Falha no structured output, fallback para JSON: "
                        f"{exc_structured}"
                    )

            if response is None:
                # Fallback: chama sem structured e tenta extrair JSON do texto
                # Define o tipo explicitamente para evitar Unknown no input
                chain_fallback: Runnable[Dict[str, Any], Any] = cast(
                    Runnable[Dict[str, Any], Any],
                    messages | llm,
                )
                raw = chain_fallback.invoke(invoke_data)
                # Normaliza para string, pois content pode ser str ou lista/objeto
                content = getattr(raw, "content", raw)
                if isinstance(content, str):
                    text = content
                else:
                    try:
                        text = json.dumps(content, ensure_ascii=False)
                    except Exception:
                        text = str(content)
                model_obj: BaseModel = self._parse_json_to_model(text, PydanticModel)
            else:
                # Garante que model_obj seja sempre BaseModel
                if isinstance(response, BaseModel):
                    model_obj = response
                elif isinstance(response, dict):
                    try:
                        model_obj = PydanticModel.model_validate(response)
                    except Exception:
                        model_obj = self._parse_json_to_model(
                            json.dumps(response, ensure_ascii=False), PydanticModel
                        )
                else:
                    model_obj = self._parse_json_to_model(str(response), PydanticModel)

            # 6) Pós-processamento: converter em dicts simples {type: value}
            intent_dicts = self._filter_and_convert_items(
                getattr(model_obj, "intent", [])
            )
            entity_dicts = self._filter_and_convert_items(
                getattr(model_obj, "entities", [])
            )

            return AnalisePreviaMensagemLangchain(
                intent=intent_dicts, entities=entity_dicts
            )

        except Exception as e:  # pragma: no cover (mapeado por testes mais altos)
            logger.error(f"Erro ao processar análise prévia: {e}")
            raise

    # ----------------------- Helpers internos -----------------------
    def _format_service_history(self, historico: Any) -> str:
        """Formata histórico do atendimento para o prompt da LLM.

        Aceita dict, str, list ou None. Se for str JSON, tenta parsear para
        dict. Se for str livre, assume como única mensagem. Se for list,
        assume lista de mensagens.
        """
        try:
            if historico is None:
                base: Dict[str, Any] = {}
            elif isinstance(historico, dict):
                base = cast(Dict[str, Any], historico)
            elif isinstance(historico, str):
                stripped = historico.strip()
                is_json_like = (
                    (stripped.startswith("{") and stripped.endswith("}"))
                    or (stripped.startswith("[") and stripped.endswith("]"))
                )
                if is_json_like:
                    try:
                        parsed = json.loads(stripped)
                        if isinstance(parsed, dict):
                            base = cast(Dict[str, Any], parsed)
                        elif isinstance(parsed, list):
                            base = {"conteudo_mensagens": parsed}
                        else:
                            base = {"conteudo_mensagens": [str(historico)]}
                    except Exception:
                        base = {"conteudo_mensagens": [str(historico)]}
                else:
                    base = {"conteudo_mensagens": [str(historico)]}
            elif isinstance(historico, list):
                base = {"conteudo_mensagens": historico}
            else:
                base = {"conteudo_mensagens": [str(historico)]}

            mensagens = base.get("conteudo_mensagens", [])
            intents = base.get("intents_detectados", [])
            entidades = base.get("entidades_extraidas", [])
            atendimentos_anteriores = base.get("historico_atendimentos", [])

            # Normalizações de tipo para listas de strings
            if isinstance(mensagens, str):
                mensagens = [mensagens]
            elif not isinstance(mensagens, list):
                mensagens = [str(mensagens)]
            else:
                mensagens = [str(m) for m in cast(List[Any], mensagens)]

            if isinstance(intents, str):
                intents = [intents]
            elif isinstance(intents, list):
                intents = [str(i) for i in cast(List[Any], intents)]
            else:
                intents = []

            if isinstance(entidades, str):
                entidades = [entidades]
            elif isinstance(entidades, list):
                entidades = [str(e) for e in cast(List[Any], entidades)]
            else:
                entidades = []

            if isinstance(atendimentos_anteriores, str):
                atendimentos_anteriores = [atendimentos_anteriores]
            elif isinstance(atendimentos_anteriores, list):
                atendimentos_anteriores = [str(a) for a in cast(List[Any], atendimentos_anteriores)]
            else:
                atendimentos_anteriores = []

            parts: List[str] = [
                "REGISTROS PARA ANÁLISE DO CONTEXTO DO ATENDIMENTO:"
            ]

            if atendimentos_anteriores:
                parts.append("")
                parts.append("HISTÓRICO DE ATENDIMENTOS ANTERIORES:")
                for i, atendimento in enumerate(atendimentos_anteriores, 1):
                    parts.append(f"{i}. {atendimento}")

            parts.append("\n\nHISTÓRICO DO ATENDIMENTO ATUAL:")

            if entidades:
                parts.append("")
                parts.append("ENTIDADES IDENTIFICADAS:")
                for entidade in entidades:
                    parts.append(f"- {entidade}")

            if intents:
                parts.append("")
                parts.append("INTENÇÕES PREVIAMENTE DETECTADAS:")
                for intent in intents:
                    parts.append(f"- {intent}")

            parts.append("")
            parts.append("HISTÓRICO DA CONVERSA:")
            if mensagens:
                for i, msg in enumerate(mensagens, 1):
                    parts.append(f"{i}. {msg}")
            else:
                parts.append("Nenhuma mensagem anterior disponível.")

            return "\n".join(parts)
        except Exception as exc:
            logger.debug(
                "Falha ao formatar histórico; aplicando fallback simples: {}",
                exc,
            )
            return f"HISTÓRICO DA CONVERSA:\n1. {str(cast(object, historico))}"

    def _normalize_types_config(self, value: Any) -> List[Dict[str, Any]]:
        """Normaliza configuração de tipos (intents/entities) para lista de dicts.

        Aceita:
        - str (JSON) -> faz json.loads
        - list -> usa como base, convertendo strings simples em {"type": s}
        - dict -> detecta formatos legados com chaves raiz "intent_types" ou
          "entity_types" e os achata; caso contrário, envolve em lista
        - outros -> retorna lista vazia
        """
        try:
            if value is None:
                return []

            # 1) Se vier como string JSON, tentar parsear
            if isinstance(value, str):
                stripped = value.strip()
                try:
                    parsed = json.loads(stripped)
                except Exception:
                    logger.debug(
                        "Falha ao parsear JSON de tipos; valor bruto será "
                        "ignorado"
                    )
                    return []
                value = parsed

            # Lista tipada que será preenchida nos casos 2.x ou 3
            items: List[Dict[str, Any] | str] = []

            # 2) Se for dict, checar formatos esperados e achatar
            if isinstance(value, dict):
                # 2.1) Formato de intents gerado pelo UI
                # {
                #   "intent_types": { "<grupo>": { "<tag>": "texto..." } }
                # }
                if (
                    "intent_types" in value
                    and isinstance(value["intent_types"], dict)
                ):
                    flattened: List[Dict[str, Any]] = []
                    typed_intent_types: Dict[str, Any] = cast(
                        Dict[str, Any], value["intent_types"]
                    )
                    for group_map_any in typed_intent_types.values():
                         if not isinstance(group_map_any, dict):
                             continue
                         typed_group_map: Dict[str, Any] = cast(Dict[str, Any], group_map_any)
                         for tag, raw_text in typed_group_map.items():
                             intent_item: Dict[str, Any] = {"type": tag}
                             # Extrai descricao e exemplos de uma string com
                             # possíveis linhas "Exemplos:" seguidas de "- ..."
                             if isinstance(raw_text, str) and raw_text.strip():
                                 desc_lines = [
                                     ln.strip() for ln in raw_text.splitlines()
                                 ]
                                 examples: List[str] = []
                                 acc_desc: List[str] = []
                                 in_examples = False
                                 for ln in desc_lines:
                                     low = ln.lower()
                                     if low.startswith("exemplos"):
                                         in_examples = True
                                         continue
                                     if in_examples and ln.startswith("-"):
                                         ex = ln.lstrip("-").strip()
                                         if ex:
                                             examples.append(ex)
                                     else:
                                         if ln:
                                             acc_desc.append(ln)
                                 if acc_desc:
                                     intent_item["descricao"] = " ".join(acc_desc)
                                 if examples:
                                     intent_item["exemplos"] = examples
                             flattened.append(intent_item)
                    return flattened

                # 2.2) Formato de entidades fornecido pelo usuário
                # {
                #   "entity_types": {
                #       "<categoria>": { "<campo>": "descricao" }
                #   }
                # }
                if (
                    "entity_types" in value
                    and isinstance(value["entity_types"], dict)
                ):
                    flattened_e: List[Dict[str, Any]] = []
                    typed_entity_types: Dict[str, Any] = cast(
                        Dict[str, Any], value["entity_types"]
                    )
                    for fields_map_any in typed_entity_types.values():
                         if not isinstance(fields_map_any, dict):
                             continue
                         typed_fields_map: Dict[str, Any] = cast(
                             Dict[str, Any], fields_map_any
                         )
                         for field_name, field_desc in typed_fields_map.items():
                             item_e: Dict[str, Any] = {"type": field_name}
                             if (
                                 isinstance(field_desc, str)
                                 and field_desc.strip()
                             ):
                                 item_e["descricao"] = field_desc.strip()
                             flattened_e.append(item_e)
                    return flattened_e

                # 2.3) Dict genérico (mantém compatibilidade anterior)
                items = [cast(Dict[str, Any], value)]

            # 3) Se já for lista, processa itens
            elif isinstance(value, list):
                items = []
                i: Any
                for i in cast(List[Any], value):
                    if isinstance(i, dict):
                        items.append(cast(Dict[str, Any], i))
                    elif isinstance(i, str):
                        items.append(i)
                    else:
                        continue
            else:
                return []

            # 4) Normalização final: garantir lista de dicts com pelo menos type
            result: List[Dict[str, Any]] = []
            for item in items:
                if isinstance(item, str):
                    s = item.strip()
                    if not s:
                        continue
                    result.append({"type": s})
                    continue
                # Neste ponto, assumimos dict pois 'items' só contém Dict[str, Any] ou str
                result.append(item)
            return result
        except Exception as exc:  # proteção defensiva
            logger.debug(
                "Falha ao normalizar configuração de tipos: {}", exc
            )
            return []

    def _filter_and_convert_items(
        self, items: Iterable[Any]
    ) -> List[Dict[str, str]]:
        """Converte itens válidos no formato {type: value}."""
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
                results.append({type_str: value_str})
            except Exception as exc:
                logger.debug(f"Falha ao processar item '{item}': {exc}")
                continue
        return results

    # ==================== Normalização pré-validação ====================
    def _slugify_type(self, raw: str) -> str:
        """Normaliza o nome do tipo para ascii, snake_case e minúsculas.

        Remove acentos, converte espaços e separadores em underscore e compacta
        múltiplos underscores.
        """
        try:
            txt = unicodedata.normalize("NFKD", str(raw))
            ascii_txt = txt.encode("ascii", "ignore").decode("ascii")
            ascii_txt = ascii_txt.lower()
            ascii_txt = re.sub(r"[^a-z0-9]+", "_", ascii_txt)
            ascii_txt = re.sub(r"_+", "_", ascii_txt).strip("_")
            return ascii_txt
        except Exception:
            return str(raw).strip().lower()

    def _map_to_allowed(
        self, raw: str, allowed: set[str], kind: str
    ) -> str | None:
        """Mapeia um valor previsto para um valor aceito quando possível.

        Regras:
        - slugify e checar inclusão direta em allowed;
        - se possuir underscore, tentar o prefixo antes do primeiro underscore;
        - tentar casar por prefixo (ex.: 'horario_funcionamento' -> 'horario');
        - casos especiais: 'nome' -> 'nome_contato' quando disponível;
        - para intents, 'pergunta_foo' -> 'pergunta' quando 'pergunta' é aceito.
        """
        v = self._slugify_type(raw)
        if v in allowed:
            return v
        # tenta prefixo pelo primeiro underscore
        if "_" in v:
            prefix = v.split("_", 1)[0]
            if prefix in allowed:
                logger.debug(
                    "Mapeando {kind} '{raw}' -> '{prefix}' por prefixo.",
                    kind=kind,
                    raw=raw,
                    prefix=prefix,
                )
                return prefix
        # tenta allowed como prefixo
        for av in allowed:
            if v.startswith(av):
                logger.debug(
                    "Mapeando {kind} '{raw}' -> '{av}' por casamento de prefixo.",
                    kind=kind,
                    raw=raw,
                    av=av,
                )
                return av
        # casos especiais
        if v == "nome" and "nome_contato" in allowed:
            logger.debug(
                "Mapeando {kind} '{raw}' -> 'nome_contato' por regra especial.",
                kind=kind,
                raw=raw,
            )
            return "nome_contato"
        if v.startswith("horario") and "horario" in allowed:
            logger.debug(
                "Mapeando {kind} '{raw}' -> 'horario' por regra especial.",
                kind=kind,
                raw=raw,
            )
            return "horario"
        return None

    def _normalize_prediction_types(
        self, data: Dict[str, Any], PydanticModel: type[BaseModel]
    ) -> Dict[str, Any]:
        """Ajusta os tipos previstos para valores aceitos antes da validação.

        - Remove itens cujo `type` não puder ser mapeado para os literais
          permitidos, evitando `literal_error`.
        """
        try:
            intent_attr: Any = getattr(PydanticModel, "__intent_allowed__", None)
            if isinstance(intent_attr, tuple):
                intents_allowed_tuple = cast(Tuple[str, ...], intent_attr)
            else:
                intents_allowed_tuple = cast(Tuple[str, ...], ())

            entity_attr: Any = getattr(PydanticModel, "__entity_allowed__", None)
            if isinstance(entity_attr, tuple):
                entities_allowed_tuple = cast(Tuple[str, ...], entity_attr)
            else:
                entities_allowed_tuple = cast(Tuple[str, ...], ())

            intents_allowed: set[str] = set(intents_allowed_tuple)
            entities_allowed: set[str] = set(entities_allowed_tuple)

            result: Dict[str, Any] = dict(data)

            # Normaliza intents
            intents_obj: Any = result.get("intent")
            if isinstance(intents_obj, list):
                norm_intents: List[Dict[str, str]] = []
                typed_intents: List[Dict[str, Any]] = []
                for _obj in cast(List[Any], intents_obj):
                    if isinstance(_obj, dict):
                        typed_intents.append(cast(Dict[str, Any], _obj))
                for intent_item in typed_intents:
                    intent_type: Any = intent_item.get("type")
                    intent_value: Any = intent_item.get("value")
                    if not intent_type:
                        continue
                    mapped = self._map_to_allowed(
                        str(intent_type), intents_allowed, "intent"
                    )
                    if mapped is None:
                        logger.debug(
                            "Descartando intent com tipo não permitido: {}",
                            intent_type,
                        )
                        continue
                    if intent_value is None:
                        continue
                    norm_intents.append({"type": mapped, "value": str(intent_value)})
                result["intent"] = norm_intents

            # Normaliza entidades
            entities_obj: Any = result.get("entities")
            if isinstance(entities_obj, list):
                norm_entities: List[Dict[str, str]] = []
                typed_entities: List[Dict[str, Any]] = []
                for _obj in cast(List[Any], entities_obj):
                    if isinstance(_obj, dict):
                        typed_entities.append(cast(Dict[str, Any], _obj))
                for entity_item in typed_entities:
                    entity_type: Any = entity_item.get("type")
                    entity_value: Any = entity_item.get("value")
                    if not entity_type:
                        continue
                    mapped = self._map_to_allowed(
                        str(entity_type), entities_allowed, "entity"
                    )
                    if mapped is None:
                        logger.debug(
                            "Descartando entity com tipo não permitido: {}",
                            entity_type,
                        )
                        continue
                    if entity_value is None:
                        continue
                    norm_entities.append({"type": mapped, "value": str(entity_value)})
                result["entities"] = norm_entities

            return result
        except Exception as exc:
            logger.debug(
                "Falha ao normalizar tipos previstos: {}",
                exc,
            )
            return data

    def _parse_json_to_model(self, text: str, PydanticModel: type[BaseModel]) -> BaseModel:
        """Normaliza a resposta textual para JSON e valida com Pydantic."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError(
                "Não foi possível identificar um objeto JSON na resposta."
            )
        data = json.loads(match.group(0))
        # Ajuste de tipos não permitidos antes da validação Pydantic
        data = self._normalize_prediction_types(data, PydanticModel)
        return PydanticModel.model_validate(data)