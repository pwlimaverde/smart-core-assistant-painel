import json
from typing import List, Type

from pydantic import BaseModel, Field


class PydanticModelFactory:
    """
    Factory para criar dinamicamente a classe PydanticModel baseada em
    configurações JSON de intent_types e entity_types.
    """

    @staticmethod
    def _extract_types_from_json(types_json: str) -> List[str]:
        """
        Extrai os tipos individuais de um JSON de configuração.

        Args:
            types_json: JSON string com a estrutura de tipos

        Returns:
            Lista com todos os tipos disponíveis
        """
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return []

        types_list: List[str] = []

        # Se há uma chave "intent_types" ou "entity_types", usar seus valores
        if "intent_types" in data:
            data = data["intent_types"]
        elif "entity_types" in data:
            data = data["entity_types"]

        for category_dict in data.values():
            if isinstance(category_dict, dict):
                types_list.extend(category_dict.keys())

        return types_list

    @staticmethod
    def _generate_documentation_section(
            types_json: str, section_title: str) -> str:
        """
        Gera uma seção da documentação baseada no JSON de configuração.

        Args:
            types_json: JSON string com a estrutura de tipos
            section_title: Título da seção (ex: "INTENTS", "ENTITIES")

        Returns:
            String formatada com a documentação da seção
        """
        try:
            data = json.loads(types_json)
        except json.JSONDecodeError:
            return f"       {section_title}: Erro ao processar configuração\n"

        documentation = f"    {section_title}:\n"

        # Se há uma chave "intent_types" ou "entity_types", usar seus valores
        if "intent_types" in data:
            data = data["intent_types"]
        elif "entity_types" in data:
            data = data["entity_types"]

        for category_key, category_dict in data.items():
            if isinstance(category_dict, dict):
                # Converter category_key para formato de título
                category_title = category_key.replace('_', ' ').upper()
                documentation += f"       {category_title}:\n"

                for type_key, description in category_dict.items():
                    documentation += f"       - {type_key}: {description}\n"

                documentation += "\n"

        return documentation

    @staticmethod
    def _generate_examples_section(intent_types_json: str,
                                   entity_types_json: str) -> str:
        """
        Gera a seção de exemplos da documentação.

        Args:
            intent_types_json: JSON com tipos de intent
            entity_types_json: JSON com tipos de entity

        Returns:
            String formatada com exemplos
        """
        examples = '''
    EXEMPLO 1: "Olá, tudo bem? meu nome é Paulo"
    - intent: [
        {"type": "saudacao", "value": "Olá, tudo bem?"},
        {"type": "apresentacao", "value": "meu nome é Paulo"}
      ]
    - entities: [
        {"type": "cliente", "value": "Paulo"}
      ]

    EXEMPLO 2: "Oi! Meu CPF é 123.456.789-00. Preciso urgentemente falar com supervisor sobre o pedido #PED123 que está atrasado. Paguei R$ 1.500 no cartão em 3x mas não recebi ainda"
    - intent: [
        {"type": "saudacao", "value": "Oi!"},
        {"type": "escalar_supervisor", "value": "falar com supervisor"},
        {"type": "reclamacao", "value": "está atrasado"},
        {"type": "urgente", "value": "urgentemente"},
        {"type": "consulta", "value": "não recebi ainda"}
      ]
    - entities: [
        {"type": "cpf", "value": "123.456.789-00"},
        {"type": "id_pedido", "value": "PED123"},
        {"type": "valor_total", "value": "R$ 1.500"},
        {"type": "forma_pagamento", "value": "cartão"},
        {"type": "numero_parcelas", "value": "3x"},
        {"type": "status_pedido", "value": "atrasado"}
      ]

    EXEMPLO 3: "Isso mesmo" (sem contexto histórico suficiente)
    - intent: []
    - entities: []

    EXEMPLO 4: "Perfeito!" (com histórico sobre agendamento para "amanhã às 14h")
    - intent: [
        {"type": "confirmacao", "value": "Perfeito!"}
      ]
    - entities: [
        {"type": "data", "value": "amanhã"},
        {"type": "horario", "value": "14h"}
      ]

    REGRAS IMPORTANTES:
    - Extraia nomes próprios como entidade "cliente" quando mencionados
    - A intenção "apresentacao" captura o ATO de se apresentar
    - A entidade "cliente" captura o NOME mencionado
    - Use o histórico para resolver referências implícitas quando o contexto for claro
    - É PERFEITAMENTE NORMAL retornar listas vazias quando não há identificações claras
    - Seja conservador: prefira precisão a recall
        '''
        return examples

    @classmethod
    def create_pydantic_model(cls,
                              intent_types_json: str,
                              entity_types_json: str) -> Type[BaseModel]:
        """
        Cria dinamicamente uma classe PydanticModel baseada nas configurações JSON.

        Args:
            intent_types_json: JSON com os tipos de intent
            entity_types_json: JSON com os tipos de entity

        Returns:
            Classe PydanticModel gerada dinamicamente
        """
        # Gerar documentação dinamicamente
        intent_docs = cls._generate_documentation_section(
            intent_types_json,
            "1. INTENTS (intenções do usuário) - identifique quando presentes")
        entity_docs = cls._generate_documentation_section(
            entity_types_json,
            "2. ENTITIES (informações específicas) - extraia quando presentes")
        examples_docs = cls._generate_examples_section(
            intent_types_json, entity_types_json)

        # Documentação completa
        full_documentation = f'''
    Analise a mensagem do cliente considerando o histórico fornecido e extraia intents e entities relevantes.

    PRINCÍPIO FUNDAMENTAL: Seja conservador e preciso. É perfeitamente normal retornar listas vazias
    quando não há identificações claras. Prefira precisão a recall.

    INSTRUÇÕES PARA ANÁLISE:
{intent_docs}
{entity_docs}
{examples_docs}
        '''

        # Criar classes Item
        class IntentItem(BaseModel):
            type: str
            value: str

        class EntityItem(BaseModel):
            type: str
            value: str

        # Criar a classe PydanticModel dinamicamente
        class PydanticModel(BaseModel):
            __doc__ = full_documentation.strip()

            intent: List[IntentItem] = Field(
                default_factory=list,
                description="Lista de intenções extraídas da mensagem - pode ser vazia quando não identificadas claramente")
            entities: List[EntityItem] = Field(
                default_factory=list,
                description="Lista de entidades extraídas da mensagem - pode ser vazia quando não identificadas")

            def add_intent(self, tipo: str, conteudo: str) -> None:
                self.intent.append(IntentItem(type=tipo, value=conteudo))

            def add_entity(self, tipo: str, valor: str) -> None:
                self.entities.append(EntityItem(type=tipo, value=valor))

            def get_intents_by_type(self, tipo: str) -> List[str]:
                return [item.value for item in self.intent if item.type == tipo]

            def get_entities_by_type(self, tipo: str) -> List[str]:
                return [
                    item.value for item in self.entities if item.type == tipo]

        return PydanticModel


def create_dynamic_pydantic_model(intent_types_json: str,
                                  entity_types_json: str) -> Type[BaseModel]:
    """
    Função utilitária para criar uma PydanticModel dinâmica.

    Args:
        intent_types_json: JSON com os tipos de intent
        entity_types_json: JSON com os tipos de entity

    Returns:
        Classe PydanticModel gerada dinamicamente

    Example:
        >>> intent_json = '{"comunicacao_basica": {"saudacao": "cumprimentos"}}'
        >>> entity_json = '{"identificacao_pessoal": {"cliente": "nome do cliente"}}'
        >>> Model = create_dynamic_pydantic_model(intent_json, entity_json)
        >>> instance = Model(intent=[{"type": "saudacao", "value": "Olá"}], entities=[])
    """
    return PydanticModelFactory.create_pydantic_model(
        intent_types_json, entity_types_json)
