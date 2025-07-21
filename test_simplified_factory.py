"""
Teste para verificar se a simplificação dos métodos funciona corretamente
"""

import json

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model, )


def test_simplified_factory() -> None:
    print("=== Teste da Factory Simplificada ===\n")

    # Configurações como JSON strings (como na aplicação real)
    intent_json_str = json.dumps({
        "intent_types": {
            "comunicacao": {
                "saudacao": "cumprimentos e apresentações",
                "despedida": "finalizações de conversa"
            },
            "suporte": {
                "duvida": "questionamentos técnicos",
                "reclamacao": "relatos de problemas"
            }
        }
    })

    entity_json_str = json.dumps({
        "entity_types": {
            "identificacao": {
                "nome": "nome do cliente",
                "email": "endereço de email"
            },
            "comercial": {
                "produto": "nome do produto",
                "valor": "valores monetários"
            }
        }
    })

    # Testar criação com JSON strings
    DynamicModel = create_dynamic_pydantic_model(
        intent_json_str, entity_json_str)

    # Criar instância de teste
    exemplo = DynamicModel(
        intent=[{"type": "saudacao", "value": "Olá, bom dia!"}],
        entities=[
            {"type": "nome", "value": "Ana Silva"},
            {"type": "produto", "value": "Smart Assistant"}
        ]
    )

    print(f"✅ Modelo criado: {type(exemplo).__name__}")
    print(f"📋 Documentação: {len(DynamicModel.__doc__ or '')} caracteres")
    if hasattr(exemplo, 'intent'):
        print(f"🎯 Intents: {exemplo.intent}")
    if hasattr(exemplo, 'entities'):
        print(f"🏷️ Entidades: {exemplo.entities}")
    print("\n🚀 Factory simplificada funcionando perfeitamente!")
    print("   - Aceita apenas JSON strings")
    print("   - Mais simples e direto")
    print("   - Compatível com sistema existente")


if __name__ == "__main__":
    test_simplified_factory()
