from typing import List

from pydantic import BaseModel, Field

# NOTA: Os tipos IntentType e EntityType agora são gerados dinamicamente pela PydanticModelFactory
# Este arquivo serve apenas como fallback/compatibilidade quando a factory
# não é usada
IntentType = str
EntityType = str


class IntentItem(BaseModel):
    type: IntentType
    value: str


class EntityItem(BaseModel):
    type: EntityType
    value: str


class PydanticModel(BaseModel):
    """
    NOTA: Esta é a versão estática da PydanticModel mantida para compatibilidade.
    Para uso dinâmico com tipos personalizados, utilize a PydanticModelFactory.

    Analise a mensagem do cliente e extraia intents e entities relevantes.

    ATENÇÃO: Os tipos e documentação específicos são gerados dinamicamente
    pela PydanticModelFactory baseados em configurações JSON.

    INSTRUÇÕES PARA ANÁLISE:
    1. INTENTS (intenções do usuário) - SEMPRE identifique pelo menos uma
    2. ENTITIES (informações específicas) - extraia quando presentes

    Esta documentação é genérica. A documentação específica é gerada
    automaticamente pela factory com base nos JSONs de configuração.

    Para documentação completa e tipos específicos, consulte a PydanticModelFactory.
    """
    intent: List[IntentItem] = Field(
        default_factory=list,
        description="Lista de intenções extraídas da mensagem - NUNCA vazia"
    )
    entities: List[EntityItem] = Field(
        default_factory=list,
        description="Lista de entidades extraídas da mensagem"
    )

    def add_intent(self, tipo: IntentType, conteudo: str) -> None:
        self.intent.append(IntentItem(type=tipo, value=conteudo))

    def add_entity(self, tipo: EntityType, valor: str) -> None:
        self.entities.append(EntityItem(type=tipo, value=valor))

    def get_intents_by_type(self, tipo: IntentType) -> List[str]:
        return [item.value for item in self.intent if item.type == tipo]

    def get_entities_by_type(self, tipo: EntityType) -> List[str]:
        return [item.value for item in self.entities if item.type == tipo]
