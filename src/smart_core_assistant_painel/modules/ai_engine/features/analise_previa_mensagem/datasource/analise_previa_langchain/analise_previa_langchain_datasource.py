from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Dict, Iterable, List

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnalisePreviaMensagemParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import APMData
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.pydantic_model_builder import (
    build_analise_previa_model,
)
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger


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
            logger.info(
                "System prompt gerado:\n{}",
                system_prompt,
            )   
            # 4) Prompt template
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

            # 5) Structured output com preferencia por json_schema
            structured_llm = None
            try:
                structured_llm = llm.with_structured_output(
                    PydanticModel, method="json_schema"
                )
            except Exception as e_json_schema:
                logger.debug(
                    "with_structured_output json_schema falhou: "
                    f"{e_json_schema}"
                )
                try:
                    structured_llm = llm.with_structured_output(PydanticModel)
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

            response = None
            if structured_llm is not None:
                try:
                    chain = messages | structured_llm
                    response = chain.invoke(invoke_data)
                except Exception as exc_structured:
                    logger.warning(
                        "Falha no structured output, fallback para JSON: "
                        f"{exc_structured}"
                    )

            if response is None:
                # Fallback: chama sem structured e tenta extrair JSON do texto
                chain_fallback = messages | llm
                raw = chain_fallback.invoke(invoke_data)
                text = raw.content if hasattr(raw, "content") else str(raw)
                model_obj = self._parse_json_to_model(text, PydanticModel)
            else:
                model_obj = response

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
                base = historico
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
                            base = parsed
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
                mensagens = [str(m) for m in mensagens]

            if isinstance(intents, str):
                intents = [intents]
            elif isinstance(intents, list):
                intents = [str(i) for i in intents]
            else:
                intents = []

            if isinstance(entidades, str):
                entidades = [entidades]
            elif isinstance(entidades, list):
                entidades = [str(e) for e in entidades]
            else:
                entidades = []

            if isinstance(atendimentos_anteriores, str):
                atendimentos_anteriores = [atendimentos_anteriores]
            elif isinstance(atendimentos_anteriores, list):
                atendimentos_anteriores = [str(a) for a in atendimentos_anteriores]
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
            return f"HISTÓRICO DA CONVERSA:\n1. {str(historico)}"

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
                    for group_map in value["intent_types"].values():
                        if not isinstance(group_map, dict):
                            continue
                        for tag, raw_text in group_map.items():
                            if not isinstance(tag, str):
                                continue
                            item: Dict[str, Any] = {"type": tag}
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
                                    item["descricao"] = " ".join(acc_desc)
                                if examples:
                                    item["exemplos"] = examples
                            flattened.append(item)
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
                    for fields_map in value["entity_types"].values():
                        if not isinstance(fields_map, dict):
                            continue
                        for field_name, field_desc in fields_map.items():
                            if not isinstance(field_name, str):
                                continue
                            item_e: Dict[str, Any] = {"type": field_name}
                            if (
                                isinstance(field_desc, str)
                                and field_desc.strip()
                            ):
                                item_e["descricao"] = field_desc.strip()
                            flattened_e.append(item_e)
                    return flattened_e

                # 2.3) Dict genérico (mantém compatibilidade anterior)
                items = [value]

            # 3) Se já for lista, processa itens
            elif isinstance(value, list):
                items = value
            else:
                return []

            # 4) Normalização final: garantir lista de dicts com pelo menos type
            result: List[Dict[str, Any]] = []
            for item in items:
                if isinstance(item, dict):
                    result.append(item)
                elif isinstance(item, str):
                    s = item.strip()
                    if not s:
                        continue
                    result.append({"type": s})
                else:
                    # ignora formatos inesperados
                    continue
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
        self, data: Dict[str, Any], PydanticModel: Any
    ) -> Dict[str, Any]:
        """Ajusta os tipos previstos para valores aceitos antes da validação.

        - Remove itens cujo `type` não puder ser mapeado para os literais
          permitidos, evitando `literal_error`.
        """
        try:
            intents_allowed = set(
                getattr(PydanticModel, "__intent_allowed__", tuple())
            )
            entities_allowed = set(
                getattr(PydanticModel, "__entity_allowed__", tuple())
            )

            result: Dict[str, Any] = dict(data)

            # Normaliza intents
            intents = result.get("intent")
            if isinstance(intents, list):
                norm_intents: List[Dict[str, str]] = []
                for it in intents:
                    if not isinstance(it, dict):
                        continue
                    t = it.get("type")
                    v = it.get("value")
                    if not t:
                        continue
                    mapped = self._map_to_allowed(
                        str(t), intents_allowed, "intent"
                    )
                    if mapped is None:
                        logger.debug(
                            "Descartando intent com tipo não permitido: {}",
                            t,
                        )
                        continue
                    norm_intents.append(
                        {"type": mapped, "value": str(v) if v is not None else ""}
                    )
                result["intent"] = norm_intents

            # Normaliza entities
            entities = result.get("entities")
            if isinstance(entities, list):
                norm_entities: List[Dict[str, str]] = []
                for en in entities:
                    if not isinstance(en, dict):
                        continue
                    t = en.get("type")
                    v = en.get("value")
                    if not t:
                        continue
                    mapped = self._map_to_allowed(
                        str(t), entities_allowed, "entity"
                    )
                    if mapped is None:
                        logger.debug(
                            "Descartando entity com tipo não permitido: {}",
                            t,
                        )
                        continue
                    norm_entities.append(
                        {"type": mapped, "value": str(v) if v is not None else ""}
                    )
                result["entities"] = norm_entities

            return result
        except Exception as exc:
            logger.debug(
                "Falha ao normalizar tipos previstos; usando dados brutos: {}",
                exc,
            )
            return data

    def _parse_json_to_model(self, text: str, PydanticModel: Any) -> Any:
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