"""Testes para PydanticModelFactory."""

import json
import pytest
from typing import Type
from pydantic import BaseModel

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.pydantic_model_factory import (
    PydanticModelFactory,
    create_dynamic_pydantic_model,
)


class TestPydanticModelFactory:
    """Testes para a classe PydanticModelFactory."""

    @pytest.fixture
    def sample_intent_json(self) -> str:
        """Fixture com JSON de exemplo para intent types."""
        return json.dumps({
            "intent_types": {
                "comunicacao_basica": {
                    "saudacao": "Cumprimentos e saudações",
                    "despedida": "Finalizações de conversa"
                },
                "solicitacoes": {
                    "informacao": "Pedidos de informação",
                    "ajuda": "Solicitações de ajuda"
                }
            }
        })

    @pytest.fixture
    def sample_entity_json(self) -> str:
        """Fixture com JSON de exemplo para entity types."""
        return json.dumps({
            "entity_types": {
                "identificacao_pessoal": {
                    "nome": "Nome da pessoa",
                    "email": "Endereço de email"
                },
                "dados_comerciais": {
                    "empresa": "Nome da empresa",
                    "telefone": "Número de telefone"
                }
            }
        })

    @pytest.fixture
    def invalid_json(self) -> str:
        """Fixture com JSON inválido."""
        return "invalid json string"

    def test_extract_types_from_json_with_intent_types(self, sample_intent_json: str) -> None:
        """Testa extração de tipos de um JSON com intent_types."""
        types = PydanticModelFactory._extract_types_from_json(sample_intent_json)
        
        expected_types = ["saudacao", "despedida", "informacao", "ajuda"]
        assert set(types) == set(expected_types)
        assert len(types) == 4

    def test_extract_types_from_json_with_entity_types(self, sample_entity_json: str) -> None:
        """Testa extração de tipos de um JSON com entity_types."""
        types = PydanticModelFactory._extract_types_from_json(sample_entity_json)
        
        expected_types = ["nome", "email", "empresa", "telefone"]
        assert set(types) == set(expected_types)
        assert len(types) == 4

    def test_extract_types_from_invalid_json(self, invalid_json: str) -> None:
        """Testa extração de tipos com JSON inválido."""
        types = PydanticModelFactory._extract_types_from_json(invalid_json)
        
        assert types == []

    def test_extract_types_from_empty_json(self) -> None:
        """Testa extração de tipos com JSON vazio."""
        empty_json = json.dumps({})
        types = PydanticModelFactory._extract_types_from_json(empty_json)
        
        assert types == []

    def test_generate_documentation_section_with_intent_types(self, sample_intent_json: str) -> None:
        """Testa geração de seção de documentação para intent types."""
        doc = PydanticModelFactory._generate_documentation_section(
            sample_intent_json, "1. INTENTS"
        )
        
        assert "1. INTENTS:" in doc
        assert "COMUNICACAO BASICA:" in doc
        assert "SOLICITACOES:" in doc
        assert "saudacao: Cumprimentos e saudações" in doc
        assert "despedida: Finalizações de conversa" in doc
        assert "informacao: Pedidos de informação" in doc
        assert "ajuda: Solicitações de ajuda" in doc

    def test_generate_documentation_section_with_invalid_json(self, invalid_json: str) -> None:
        """Testa geração de documentação com JSON inválido."""
        doc = PydanticModelFactory._generate_documentation_section(
            invalid_json, "1. INTENTS"
        )
        
        assert "1. INTENTS: Erro ao processar configuração" in doc

    def test_generate_fixed_entities_section(self) -> None:
        """Testa geração da seção de entidades fixas."""
        doc = PydanticModelFactory._generate_fixed_entities_section()
        
        assert "3. ENTIDADES FIXAS" in doc
        assert "CONTATO:" in doc
        assert "CLIENTE:" in doc
        assert "ATENDIMENTO:" in doc
        assert "nome_contato:" in doc
        assert "cnpj_cliente:" in doc
        assert "avaliacao_atendimento:" in doc

    def test_generate_examples_section(self, sample_intent_json: str, sample_entity_json: str) -> None:
        """Testa geração da seção de exemplos."""
        doc = PydanticModelFactory._generate_examples_section(
            sample_intent_json, sample_entity_json
        )
        
        assert "EXEMPLOS DE ANÁLISE:" in doc
        assert "EXEMPLO 1:" in doc
        assert "EXEMPLO 2:" in doc
        assert "REGRAS IMPORTANTES:" in doc
        assert "intent:" in doc
        assert "entities:" in doc

    def test_create_pydantic_model(self, sample_intent_json: str, sample_entity_json: str) -> None:
        """Testa criação do modelo Pydantic dinâmico."""
        model_class = PydanticModelFactory.create_pydantic_model(
            sample_intent_json, sample_entity_json
        )
        
        # Verifica se é uma subclasse de BaseModel
        assert issubclass(model_class, BaseModel)
        
        # Verifica se tem os campos esperados através dos field names
        field_names = set(model_class.model_fields.keys())
        assert 'intent' in field_names
        assert 'entities' in field_names
        
        # Testa instanciação
        instance = model_class()
        assert instance.intent == []
        assert instance.entities == []
        
        # Testa com dados
        instance_with_data = model_class(
            intent=[{"type": "saudacao", "value": "Olá"}],
            entities=[{"type": "nome", "value": "João"}]
        )
        assert len(instance_with_data.intent) == 1
        assert len(instance_with_data.entities) == 1
        assert instance_with_data.intent[0].type == "saudacao"
        assert instance_with_data.intent[0].value == "Olá"
        assert instance_with_data.entities[0].type == "nome"
        assert instance_with_data.entities[0].value == "João"

    def test_pydantic_model_methods(self, sample_intent_json: str, sample_entity_json: str) -> None:
        """Testa os métodos do modelo Pydantic criado."""
        model_class = PydanticModelFactory.create_pydantic_model(
            sample_intent_json, sample_entity_json
        )
        
        instance = model_class()
        
        # Testa add_intent
        instance.add_intent("saudacao", "Olá")
        assert len(instance.intent) == 1
        assert instance.intent[0].type == "saudacao"
        assert instance.intent[0].value == "Olá"
        
        # Testa add_entity
        instance.add_entity("nome", "João")
        assert len(instance.entities) == 1
        assert instance.entities[0].type == "nome"
        assert instance.entities[0].value == "João"
        
        # Adiciona mais dados para testar get_*_by_type
        instance.add_intent("saudacao", "Oi")
        instance.add_intent("despedida", "Tchau")
        instance.add_entity("nome", "Maria")
        instance.add_entity("email", "joao@email.com")
        
        # Testa get_intents_by_type
        saudacoes = instance.get_intents_by_type("saudacao")
        assert set(saudacoes) == {"Olá", "Oi"}
        
        despedidas = instance.get_intents_by_type("despedida")
        assert despedidas == ["Tchau"]
        
        inexistente = instance.get_intents_by_type("inexistente")
        assert inexistente == []
        
        # Testa get_entities_by_type
        nomes = instance.get_entities_by_type("nome")
        assert set(nomes) == {"João", "Maria"}
        
        emails = instance.get_entities_by_type("email")
        assert emails == ["joao@email.com"]
        
        inexistente_entity = instance.get_entities_by_type("inexistente")
        assert inexistente_entity == []


class TestCreateDynamicPydanticModel:
    """Testes para a função create_dynamic_pydantic_model."""

    def test_create_dynamic_pydantic_model(self) -> None:
        """Testa a função utilitária create_dynamic_pydantic_model."""
        intent_json = json.dumps({
            "intent_types": {
                "comunicacao_basica": {
                    "saudacao": "Cumprimentos"
                }
            }
        })
        
        entity_json = json.dumps({
            "entity_types": {
                "identificacao_pessoal": {
                    "nome": "Nome da pessoa"
                }
            }
        })
        
        model_class = create_dynamic_pydantic_model(intent_json, entity_json)
        
        # Verifica se é uma subclasse de BaseModel
        assert issubclass(model_class, BaseModel)
        
        # Testa instanciação
        instance = model_class(
            intent=[{"type": "saudacao", "value": "Olá"}],
            entities=[{"type": "nome", "value": "João"}]
        )
        
        assert len(instance.intent) == 1
        assert len(instance.entities) == 1
        assert instance.intent[0].type == "saudacao"
        assert instance.intent[0].value == "Olá"
        assert instance.entities[0].type == "nome"
        assert instance.entities[0].value == "João"

    def test_create_dynamic_pydantic_model_with_empty_data(self) -> None:
        """Testa criação do modelo com dados vazios."""
        intent_json = json.dumps({"intent_types": {}})
        entity_json = json.dumps({"entity_types": {}})
        
        model_class = create_dynamic_pydantic_model(intent_json, entity_json)
        
        # Verifica se é uma subclasse de BaseModel
        assert issubclass(model_class, BaseModel)
        
        # Testa instanciação
        instance = model_class()
        assert instance.intent == []
        assert instance.entities == []