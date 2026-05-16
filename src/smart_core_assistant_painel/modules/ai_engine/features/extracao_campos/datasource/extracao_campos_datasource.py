# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
"""Datasource para extração de campos personalizados via LLM com Structured Output.

Monta dinamicamente um schema Pydantic a partir dos campos configurados no
tenant, invoca o LLM com `with_structured_output` e retorna a lista de
`CampoExtraido` com confiança.
"""

from __future__ import annotations

from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field, create_model

from smart_core_assistant_painel.modules.ai_engine.features.extracao_campos.domain.model.campo_extraido import (
    CampoExtraido,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    CampoDefinicao,
    ExtracaoCamposParameters,
)


def _campo_pydantic_field(campo: CampoDefinicao) -> tuple[Any, Any]:
    """Converte um CampoDefinicao em (tipo, Field) para create_model."""
    descricao = campo.descricao or campo.nome
    hint = campo.hint or ""
    field_description = f"{descricao}. {hint}".strip()

    tipo = campo.tipo
    if tipo == "numero":
        return (
            Optional[float],
            Field(default=None, description=field_description),
        )
    if tipo == "booleano":
        return (
            Optional[bool],
            Field(default=None, description=field_description),
        )
    if tipo in ("escolha", "multipla_escolha"):
        return (
            Optional[str],
            Field(default=None, description=field_description),
        )
    # texto, data, padrão
    return (Optional[str], Field(default=None, description=field_description))


def _build_confianca_field() -> tuple[Any, Any]:
    return (
        float,
        Field(default=0.5, ge=0.0, le=1.0, description="Confiança (0.0-1.0)"),
    )


def _build_dynamic_schema(campos: list[CampoDefinicao]) -> type[BaseModel]:
    """Cria um modelo Pydantic dinâmico com um campo por CampoDefinicao + confiança."""
    field_definitions: dict[str, Any] = {}
    for campo in campos:
        field_definitions[campo.slug] = _campo_pydantic_field(campo)
    field_definitions["confianca_geral"] = _build_confianca_field()
    return create_model("ExtractionResult", **field_definitions)


def _formatar_historico(historico: list[dict[str, Any]]) -> str:
    """Formata o histórico de conversa para inclusão no prompt."""
    linhas: list[str] = []
    for msg in historico[
        -30:
    ]:  # últimas 30 mensagens para não extrapolar contexto
        remetente = msg.get("remetente", "?")
        conteudo = str(msg.get("conteudo") or msg.get("texto") or "").strip()
        if not conteudo:
            continue
        prefixo = {
            "CONTATO": "Cliente",
            "ASSISTENTE_VIRTUAL": "Bot",
            "ATENDENTE_HUMANO": "Atendente",
        }.get(remetente, remetente)
        linhas.append(f"{prefixo}: {conteudo}")
    return "\n".join(linhas) or "Sem histórico."


class ExtracaoCamposDatasource:
    """Invoca o LLM para extrair campos personalizados da conversa.

    Retorna lista de `CampoExtraido` — um por campo onde `encontrado=True`
    e `confianca >= 0.6`.
    """

    THRESHOLD = 0.6

    def __call__(
        self, parameters: ExtracaoCamposParameters
    ) -> list[CampoExtraido]:
        campos = parameters.campos_a_extrair
        if not campos:
            return []

        schema = _build_dynamic_schema(campos)

        # Monta descrição dos campos para o prompt
        campos_desc = "\n".join(
            f"- **{c.slug}** ({c.nome}): {c.descricao}"
            + (f" [hint: {c.hint}]" if c.hint else "")
            for c in campos
        )

        historico_txt = _formatar_historico(parameters.historico_conversa)

        prompt = (
            "Você é um extrator de dados estruturados. Analise a conversa abaixo "
            "e extraia APENAS os valores que aparecem EXPLICITAMENTE no texto. "
            "Não invente informações. Retorne null para campos ausentes.\n\n"
            f"### CAMPOS A EXTRAIR:\n{campos_desc}\n\n"
            f"### CONVERSA:\n{historico_txt}\n\n"
            "Extraia os valores e indique sua confiança geral (0.0 a 1.0)."
        )

        try:
            llm = parameters.llm_parameters.create_llm
            structured_llm = llm.with_structured_output(
                schema, method="json_schema"
            )
            resultado = structured_llm.invoke(prompt)
        except Exception as exc:
            logger.error(
                "ExtracaoCamposDatasource: falha ao invocar LLM para atendimento {}: {}",
                parameters.atendimento_id,
                exc,
            )
            raise

        extraidos: list[CampoExtraido] = []
        confianca_geral = float(getattr(resultado, "confianca_geral", 0.5))

        for campo in campos:
            valor = getattr(resultado, campo.slug, None)
            if valor is None:
                continue
            # Usa confiança geral como proxy por campo (LLM retorna uma só)
            if confianca_geral < self.THRESHOLD:
                logger.debug(
                    "Extração ignorada para campo '{}': confiança {:.2f} < {:.2f}",
                    campo.slug,
                    confianca_geral,
                    self.THRESHOLD,
                )
                continue
            extraidos.append(
                CampoExtraido(
                    slug=campo.slug,
                    valor=valor,
                    confianca=confianca_geral,
                    encontrado=True,
                )
            )

        logger.info(
            "ExtracaoCamposDatasource: atendimento {} — {} campos extraídos de {}",
            parameters.atendimento_id,
            len(extraidos),
            len(campos),
        )
        return extraidos
