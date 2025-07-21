from typing import List, Literal

from pydantic import BaseModel, Field

# Definir os tipos Literal como aliases de tipo
IntentType = Literal[
    "saudacao",
    "pergunta",
    "cotacao",
    "agradecimento",
    "reclamacao",
    "elogio",
]

EntityType = Literal[
    "cliente",
    "produto",
    "preco",
    "marca",
    "telefone",
    "email",
]


class IntentItem(BaseModel):
    type: IntentType
    value: str


class EntityItem(BaseModel):
    type: EntityType
    value: str


class PydanticModel(BaseModel):
    """
    Analise a mensagem do cliente e extraia intents e entities relevantes.

    INSTRUÇÕES PARA ANÁLISE:
    1. INTENTS (intenções do usuário) - SEMPRE identifique pelo menos uma:
       - saudacao: cumprimentos como "oi", "olá", "bom dia", "tudo bem"
       - pergunta: questionamentos ou dúvidas
       - cotacao: pedidos de preço ou orçamento
       - agradecimento: "obrigado", "valeu", "agradecido"
       - reclamacao: insatisfação ou problemas
       - elogio: satisfação ou elogios

    2. ENTITIES (informações específicas) - extraia quando presentes:
       - cliente: nomes de pessoas ("Paulo", "Maria", "João")
       - produto: nomes de produtos ou serviços
       - preco: valores monetários
       - marca: marcas ou fabricantes
       - telefone: números de telefone
       - email: endereços de email

    EXEMPLO: "Olá, tudo bem? meu nome é Paulo"
    - intent: [{"type": "saudacao", "value": "Olá, tudo bem?"}]
    - entities: [{"type": "cliente", "value": "Paulo"}]

    IMPORTANTE: NUNCA retorne listas vazias. Sempre identifique pelo menos uma intenção.
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


# Alias para compatibilidade com o código existente
AnalisePreviaMensagemLangchain = PydanticModel
