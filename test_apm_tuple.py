#!/usr/bin/env python3
"""
Teste para verificar se a APMTuple NamedTuple está funcionando corretamente
"""

from src.smart_core_assistant_painel.modules.ai_engine.utils.types import APMTuple


def test_apm_tuple():
    """Testa a criação e uso da APMTuple"""

    # Dados de exemplo
    intent_data = [
        {"type": "saudacao", "description": "cumprimentos"},
        {"type": "pergunta", "description": "solicitações de informação"}
    ]

    entity_data = [
        {"type": "cliente", "description": "nome do cliente"},
        {"type": "produto", "description": "nome do produto"}
    ]

    # Criar tupla nomeada
    apm_tuple = APMTuple(
        intent_types=intent_data,
        entity_types=entity_data
    )

    print("✅ Teste APMTuple NamedTuple:")
    print(f"  Tipo: {type(apm_tuple)}")
    print(f"  É uma tupla: {isinstance(apm_tuple, tuple)}")
    print(f"  Campos: {apm_tuple._fields}")

    # Acesso por nome (novo)
    print(f"  Intent types (por nome): {len(apm_tuple.intent_types)} items")
    print(f"  Entity types (por nome): {len(apm_tuple.entity_types)} items")

    # Acesso por índice (compatibilidade)
    print(f"  Intent types (por índice): {len(apm_tuple[0])} items")
    print(f"  Entity types (por índice): {len(apm_tuple[1])} items")

    # Desempacotamento (compatibilidade)
    intents, entities = apm_tuple
    print(
        f"  Desempacotamento: {
            len(intents)} intents, {
            len(entities)} entities")

    print("✅ Todos os testes passaram!")


if __name__ == "__main__":
    test_apm_tuple()
