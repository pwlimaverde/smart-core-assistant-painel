"""
Testes para o MensagemMapper, focando na sincronização do campo confiança.
"""

from unittest.mock import Mock
import pytest
from datetime import datetime

from smart_core_assistant_painel.app.notion_sync.services.mappers.mensagem_mapper import (
    MensagemMapper,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import Mensagem, Atendimento, Contato
from smart_core_assistant_painel.app.notion_sync.models import MensagemSync, AtendimentoSync


class TestMensagemMapper:
    """Testes para o mapper de mensagens."""

    def test_to_notion_properties_inclui_confianca_resposta(self) -> None:
        """
        Testa se o campo confianca_resposta é incluído corretamente nas propriedades do Notion.

        Este teste valida o problema reportado onde o campo de confiança da resposta
        não estava sendo atualizado na tabela de mensagens do Notion.
        """
        # Arrange
        mock_mensagem = Mock(spec=Mensagem)
        mock_mensagem.conteudo = "Mensagem de teste"
        mock_mensagem.remetente = "cliente"
        mock_mensagem.timestamp = datetime.now()
        mock_mensagem.tipo = "extendedTextMessage"
        mock_mensagem.confianca_resposta = 0.85  # Campo importante para o teste
        mock_mensagem.resposta_bot = "Resposta do bot"
        mock_mensagem.respondida = True
        mock_mensagem.intent_detectado = [{"type": "saudacao", "value": "Olá"}]
        mock_mensagem.entidades_extraidas = [{"type": "pessoa", "value": "João"}]
        mock_mensagem.metadados = {"fonte": "whatsapp"}

        mock_atendimento = Mock(spec=Atendimento)
        mock_atendimento.id = 1
        mock_mensagem.atendimento = mock_atendimento

        mock_atendimento_sync = Mock(spec=AtendimentoSync)
        mock_atendimento_sync.external_id = "page-id-123"
        mock_atendimento_sync.atendimento = mock_atendimento

        mock_sync = Mock(spec=MensagemSync)
        mock_sync.mensagem = mock_mensagem
        mock_sync.atendimento_sync = mock_atendimento_sync

        # Act
        props = MensagemMapper.to_notion_properties(mock_sync)

        # Assert
        assert "Confiança Resposta" in props, "Campo 'Confiança Resposta' deve estar presente nas propriedades"
        assert props["Confiança Resposta"]["number"] == 0.85, "Valor da confiança deve ser 0.85"

    def test_to_notion_properties_sem_confianca(self) -> None:
        """
        Testa que o campo 'Confiança Resposta' não é incluído quando o valor é None.
        """
        # Arrange
        mock_mensagem = Mock(spec=Mensagem)
        mock_mensagem.conteudo = "Mensagem de teste"
        mock_mensagem.remetente = "cliente"
        mock_mensagem.timestamp = datetime.now()
        mock_mensagem.tipo = "extendedTextMessage"
        mock_mensagem.confianca_resposta = None  # Sem confiança
        mock_mensagem.atendimento = Mock(spec=Atendimento)

        mock_atendimento_sync = Mock(spec=AtendimentoSync)
        mock_atendimento_sync.external_id = "page-id-123"

        mock_sync = Mock(spec=MensagemSync)
        mock_sync.mensagem = mock_mensagem
        mock_sync.atendimento_sync = mock_atendimento_sync

        # Act
        props = MensagemMapper.to_notion_properties(mock_sync)

        # Assert
        assert "Confiança Resposta" not in props, "Campo 'Confiança Resposta' não deve estar presente quando valor é None"

    def test_to_notion_properties_confianca_zero(self) -> None:
        """
        Testa que confiança igual a 0 é incluída (valor válido).
        """
        # Arrange
        mock_mensagem = Mock(spec=Mensagem)
        mock_mensagem.conteudo = "Mensagem de teste"
        mock_mensagem.remetente = "cliente"
        mock_mensagem.timestamp = datetime.now()
        mock_mensagem.tipo = "extendedTextMessage"
        mock_mensagem.confianca_resposta = 0.0  # Zero é um valor válido
        mock_mensagem.atendimento = Mock(spec=Atendimento)

        mock_atendimento_sync = Mock(spec=AtendimentoSync)
        mock_atendimento_sync.external_id = "page-id-123"

        mock_sync = Mock(spec=MensagemSync)
        mock_sync.mensagem = mock_mensagem
        mock_sync.atendimento_sync = mock_atendimento_sync

        # Act
        props = MensagemMapper.to_notion_properties(mock_sync)

        # Assert
        assert "Confiança Resposta" in props, "Campo 'Confiança Resposta' deve estar presente mesmo com valor 0"
        assert props["Confiança Resposta"]["number"] == 0.0, "Valor da confiança deve ser 0.0"

    def test_to_notion_properties_confianca_um(self) -> None:
        """
        Testa que confiança igual a 1 é incluída (valor máximo válido).
        """
        # Arrange
        mock_mensagem = Mock(spec=Mensagem)
        mock_mensagem.conteudo = "Mensagem de teste"
        mock_mensagem.remetente = "cliente"
        mock_mensagem.timestamp = datetime.now()
        mock_mensagem.tipo = "extendedTextMessage"
        mock_mensagem.confianca_resposta = 1.0  # Valor máximo
        mock_mensagem.atendimento = Mock(spec=Atendimento)

        mock_atendimento_sync = Mock(spec=AtendimentoSync)
        mock_atendimento_sync.external_id = "page-id-123"

        mock_sync = Mock(spec=MensagemSync)
        mock_sync.mensagem = mock_mensagem
        mock_sync.atendimento_sync = mock_atendimento_sync

        # Act
        props = MensagemMapper.to_notion_properties(mock_sync)

        # Assert
        assert "Confiança Resposta" in props, "Campo 'Confiança Resposta' deve estar presente com valor 1.0"
        assert props["Confiança Resposta"]["number"] == 1.0, "Valor da confiança deve ser 1.0"
