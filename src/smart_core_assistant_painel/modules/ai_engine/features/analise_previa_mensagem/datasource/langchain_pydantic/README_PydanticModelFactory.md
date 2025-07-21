# PydanticModelFactory

A `PydanticModelFactory` é uma factory para criar dinamicamente a classe `PydanticModel` baseada em configurações JSON de `intent_types` e `entity_types`.

## Objetivo

Esta factory permite gerar dinamicamente:
1. **Listas de tipos**: `IntentType` e `EntityType` baseadas nos JSONs de configuração
2. **Documentação**: Documentação da classe `PydanticModel` formatada automaticamente
3. **Classe PydanticModel**: Classe completa com validação e métodos auxiliares

## Uso

### Exemplo básico

```python
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    create_dynamic_pydantic_model
)

# JSONs de configuração
intent_types_json = {
    "intent_types": {
        "comunicacao_basica": {
            "saudacao": "cumprimentos e apresentações",
            "despedida": "finalizações de conversa",
            "agradecimento": "expressões de gratidão"
        }
    }
}

entity_types_json = {
    "entity_types": {
        "identificacao_pessoal": {
            "cliente": "nome ou identificação do cliente",
            "email": "endereço de email"
        }
    }
}

# Criar modelo dinâmico
PydanticModel = create_dynamic_pydantic_model(
    intent_types_json, 
    entity_types_json
)

# Usar o modelo
exemplo = PydanticModel(
    intent=[
        {"type": "saudacao", "value": "Olá, tudo bem?"}
    ],
    entities=[
        {"type": "cliente", "value": "Paulo"}
    ]
)
```

### Integração com o sistema existente

A factory foi integrada ao `AnalisePreviaMensagemLangchainDatasource` para criar dinamicamente o modelo baseado nos parâmetros recebidos:

```python
def __call__(self, parameters: AnalisePreviaMensagemParameters) -> AnalisePreviaMensagemLangchain:
    # Criar modelo PydanticModel dinâmico baseado nos parâmetros
    PydanticModel = create_dynamic_pydantic_model(
        intent_types_json=parameters.valid_intent_types,
        entity_types_json=parameters.valid_entity_types
    )
    
    # Usar o modelo criado dinamicamente...
```

## Formato dos JSONs

Os JSONs devem seguir a estrutura:

```json
{
  "intent_types": {
    "categoria1": {
      "tipo1": "descrição do tipo1",
      "tipo2": "descrição do tipo2"
    },
    "categoria2": {
      "tipo3": "descrição do tipo3"
    }
  }
}
```

```json
{
  "entity_types": {
    "categoria1": {
      "entidade1": "descrição da entidade1",
      "entidade2": "descrição da entidade2"
    }
  }
}
```

## Benefícios

1. **Flexibilidade**: Os tipos e documentação são gerados dinamicamente
2. **Manutenibilidade**: Mudanças nos tipos requerem apenas atualização dos JSONs
3. **Consistência**: A documentação é sempre sincronizada com os tipos disponíveis
4. **Reutilização**: A factory pode ser usada em diferentes contextos

## Documentação gerada

A factory gera automaticamente a documentação da classe `PydanticModel` formatada como:

```
COMUNICAÇÃO BÁSICA:
- saudacao: cumprimentos e apresentações
- despedida: finalizações de conversa
- agradecimento: expressões de gratidão
```

Incluindo exemplos de uso e regras importantes para a análise de mensagens.
