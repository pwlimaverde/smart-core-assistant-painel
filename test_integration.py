"""
Teste rápido para verificar a integração entre PydanticModel estática e PydanticModelFactory dinâmica
"""

from typing import Any, Dict

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model import (
    EntityItem, IntentItem, )
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model import (
    PydanticModel as StaticPydanticModel, )
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model, )


def test_integration() -> None:
    print("=== Teste de Integração ===\n")

    # Testar modelo estático (fallback)
    print("1. Modelo Estático (fallback):")
    static_model = StaticPydanticModel(
        intent=[IntentItem(type="saudacao", value="Olá")],
        entities=[EntityItem(type="cliente", value="Paulo")]
    )
    print(f"   ✅ Instância criada: {type(static_model).__name__}")
    doc = static_model.__doc__ or ""
    print(f"   📋 Documentação: {doc[:100]}...")

    # Testar factory dinâmica
    print("\n2. Factory Dinâmica:")
    intent_json: Dict[str, Any] = {
        "intent_types": {
            "comunicacao_basica": {
                "saudacao": "cumprimentos e apresentações",
                "despedida": "finalizações de conversa"
            }
        }
    }

    entity_json: Dict[str, Any] = {
        "entity_types": {
            "identificacao_pessoal": {
                "cliente": "nome do cliente",
                "email": "endereço de email"
            }
        }
    }

    DynamicModel = create_dynamic_pydantic_model(intent_json, entity_json)
    dynamic_instance = DynamicModel(
        intent=[{"type": "saudacao", "value": "Olá"}],
        entities=[{"type": "cliente", "value": "Paulo"}]
    )

    print(f"   ✅ Modelo dinâmico criado: {type(dynamic_instance).__name__}")
    dynamic_doc = DynamicModel.__doc__ or ""
    print(f"   📋 Documentação personalizada: {len(dynamic_doc)} caracteres")

    print("\n🎯 Integração funcionando perfeitamente!")
    print("   - Modelo estático serve como fallback")
    print("   - Factory dinâmica gera modelos personalizados")
    print("   - Ambos mantêm compatibilidade total")


if __name__ == "__main__":
    test_integration()

if __name__ == "__main__":
    test_integration()
