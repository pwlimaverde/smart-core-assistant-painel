import json
from typing import Any

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model,
)


def test_pydantic_model_docstring_generated_from_jsons() -> None:
    """Garante que a docstring do modelo dinâmico contenha as seções e regras esperadas.

    Cenário baseado em JSONs de intents e entities fornecidos pelo usuário.
    """
    intent_types: dict[str, dict[str, dict[str, str]]] = {
        "intent_types": {
            "gerais": {
                "saudacao": "Mensagens de cumprimento inicial.",
                "agradecimento": "Expressões de gratidão.",
                "despedida": "Encerramentos de conversa.",
            },
            "comercial": {
                "cotacao": "Solicitação de preço/orçamento.",
            },
        }
    }

    entity_types: dict[str, dict[str, dict[str, str]]] = {
        "entity_types": {
            "produtos": {
                "produto": "Nome de um produto mencionado.",
            },
            "pessoa": {
                "nome_contato": "Nome completo do contato.",
            },
        }
    }

    intent_types_json: str = json.dumps(intent_types)
    entity_types_json: str = json.dumps(entity_types)

    PydanticModel = create_dynamic_pydantic_model(
        intent_types_json=intent_types_json,
        entity_types_json=entity_types_json,
    )

    doc: str = getattr(PydanticModel, "__doc__", "") or ""
    assert doc != ""

    # Seções principais
    assert "REGRAS OBRIGATÓRIAS:" in doc
    assert "1. INTENTS (intenções do usuário):" in doc
    assert "2. ENTITIES DINÂMICAS (informações específicas):" in doc
    assert "3. ENTIDADES FIXAS (dados para cadastro no banco)" in doc
    assert "EXEMPLOS DE ANÁLISE:" in doc

    # Regras alinhadas
    assert "Pode haver múltiplos intents e múltiplas entities na mesma mensagem." in doc
    assert "Priorize intents quando a mensagem contiver exatamente o nome de um intent permitido." in doc
    assert "Use o histórico do atendimento SOMENTE como critério de desempate" in doc

    # Listas oficiais reforçadas
    assert "INTENTS PERMITIDAS (valores exatos):" in doc
    for intent in ("saudacao", "agradecimento", "despedida", "cotacao"):
        assert f"- {intent}" in doc

    assert "ENTITIES DINÂMICAS PERMITIDAS (valores exatos):" in doc
    for ent in ("produto", "nome_contato"):
        assert f"- {ent}" in doc

    # Política de decisão por palavras-chave deve aparecer
    assert "POLÍTICA DE DECISÃO POR PALAVRAS-CHAVE" in doc

    # Não deve haver menção a campo de confiança
    assert "confian" not in doc.lower()


def test_pydantic_model_schema_unchanged_no_confidence() -> None:
    """Verifica que o schema permanece compatível (sem campo 'confidence')."""
    intent_types: dict[str, Any] = {
        "intent_types": {
            "gerais": {"saudacao": "..."},
        }
    }
    entity_types: dict[str, Any] = {
        "entity_types": {
            "produtos": {"produto": "..."},
        }
    }
    PydanticModel = create_dynamic_pydantic_model(
        intent_types_json=json.dumps(intent_types),
        entity_types_json=json.dumps(entity_types),
    )

    # Instanciação deve aceitar strings e converter para Enum internamente
    instance = PydanticModel(
        intent=[{"type": "saudacao", "value": "Olá"}],
        entities=[{"type": "produto", "value": "baton"}],
    )

    # Verificações básicas de integridade
    assert hasattr(instance, "intent")
    assert hasattr(instance, "entities")
    assert not hasattr(instance, "confidence")

    assert len(instance.intent) == 1
    assert instance.intent[0].value == "Olá"
    assert len(instance.entities) == 1
    assert instance.entities[0].value == "baton"