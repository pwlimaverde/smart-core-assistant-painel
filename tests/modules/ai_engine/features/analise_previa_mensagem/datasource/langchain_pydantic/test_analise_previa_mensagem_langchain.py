"""Testes para AnalisePreviaMensagemLangchain."""

import pytest
from typing import Any, Optional

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain,
)
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.interface.analise_previa_mensagem import (
    AnalisePreviaMensagem,
)


class TestAnalisePreviaMensagemLangchain:
    """Testes para a classe AnalisePreviaMensagemLangchain."""

    def test_init_with_default_values(self) -> None:
        """Testa a inicialização com valores padrão."""
        analise = AnalisePreviaMensagemLangchain()
        
        assert analise.intent == []
        assert analise.entities == []

    def test_init_with_intent_and_entities(self) -> None:
        """Testa a inicialização com intenções e entidades."""
        intent_data = [{"saudacao": "Olá"}]
        entities_data = [{"nome": "João"}]
        
        analise = AnalisePreviaMensagemLangchain(
            intent=intent_data,
            entities=entities_data
        )
        
        assert analise.intent == intent_data
        assert analise.entities == entities_data

    def test_init_with_none_values(self) -> None:
        """Testa a inicialização com valores None."""
        analise = AnalisePreviaMensagemLangchain(
            intent=None,
            entities=None
        )
        
        assert analise.intent == []
        assert analise.entities == []

    def test_inheritance(self) -> None:
        """Testa se a classe herda corretamente de AnalisePreviaMensagem."""
        analise = AnalisePreviaMensagemLangchain()
        
        assert isinstance(analise, AnalisePreviaMensagem)

    def test_init_with_empty_lists(self) -> None:
        """Testa a inicialização com listas vazias."""
        analise = AnalisePreviaMensagemLangchain(
            intent=[],
            entities=[]
        )
        
        assert analise.intent == []
        assert analise.entities == []

    def test_init_with_complex_data(self) -> None:
        """Testa a inicialização com dados complexos."""
        intent_data = [
            {"tipo": "saudacao", "valor": "Olá", "confianca": 0.95},
            {"tipo": "pergunta", "valor": "Como está?", "confianca": 0.87}
        ]
        entities_data = [
            {"tipo": "pessoa", "valor": "João", "posicao": 10},
            {"tipo": "local", "valor": "São Paulo", "posicao": 25}
        ]
        
        analise = AnalisePreviaMensagemLangchain(
            intent=intent_data,
            entities=entities_data
        )
        
        assert analise.intent == intent_data
        assert analise.entities == entities_data
        assert len(analise.intent) == 2
        assert len(analise.entities) == 2