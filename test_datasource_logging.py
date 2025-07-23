#!/usr/bin/env python3
"""
Script de teste para demonstrar o logging quando o datasource usa create_dynamic_pydantic_model.
"""

from src.smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model, )

# JSON simples para teste
intent_json = '''
{
  "intent_types": {
    "comunicacao_basica": {
      "saudacao": "cumprimentos e apresentações",
      "despedida": "finalizações de conversa"
    }
  }
}
'''

entity_json = '''
{
  "entity_types": {
    "produtos_servicos": {
      "produto": "Nome específico do produto mencionado",
      "preco": "Valor ou preço informado na conversa"
    }
  }
}
'''


def test_datasource_logging():
    """
    Testa o logging quando create_dynamic_pydantic_model é chamado
    (simulando chamada do datasource).
    """
    print("=" * 80)
    print("TESTE: LOGGING QUANDO CHAMADO PELO DATASOURCE")
    print("=" * 80)

    # Simular a chamada que o datasource faz
    PydanticModel = create_dynamic_pydantic_model(
        intent_types_json=intent_json,
        entity_types_json=entity_json
    )

    print("\n✅ Teste concluído - verifique os logs acima!")
    print("=" * 80)


if __name__ == "__main__":
    test_datasource_logging()
