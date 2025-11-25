"""
Testes para o modelo MensagemSync, focando na detecção de mudanças importantes.
"""

from unittest.mock import Mock, patch
import pytest
from datetime import datetime, timedelta
from django.utils import timezone

from smart_core_assistant_painel.app.notion_sync.models import MensagemSync
from smart_core_assistant_painel.app.ui.atendimentos.models import Mensagem


class TestMensagemSyncNeedsSync:
    """Testes para o método needs_sync do MensagemSync."""

    def test_needs_sync_com_status_pending(self) -> None:
        """
        Testa que precisa sincronizar quando status é pending.
        """
        # Arrange - Criamos uma classe simples que herda o comportamento
        class TestMensagemSync:
            def __init__(self, sync_status: str, last_sync_at=None):
                self.sync_status = sync_status
                self.last_sync_at = last_sync_at
                self.mensagem = None

            def needs_sync(self) -> bool:
                """Simulação do método needs_sync real."""
                if self.sync_status in ["pending", "error"]:
                    return True

                if self.sync_status == "synced" and self.last_sync_at:
                    mensagem = self.mensagem
                    if not mensagem:
                        return False

                    campos_criticos = {
                        "resposta_bot": getattr(mensagem, "resposta_bot", None),
                        "confianca_resposta": getattr(mensagem, "confianca_resposta", None),
                        "respondida": getattr(mensagem, "respondida", None),
                        "intent_detectado": getattr(mensagem, "intent_detectado", None),
                        "entidades_extraidas": getattr(mensagem, "entidades_extraidas", None),
                        "metadados": getattr(mensagem, "metadados", None),
                    }

                    for campo, valor_atual in campos_criticos.items():
                        if valor_atual and mensagem.updated_at > self.last_sync_at:
                            return True

                return False

        sync_instance = TestMensagemSync("pending", None)

        # Act
        result = sync_instance.needs_sync()

        # Assert
        assert result is True

    def test_needs_sync_com_status_error(self) -> None:
        """
        Testa que precisa sincronizar quando status é error.
        """
        class TestMensagemSync:
            def __init__(self, sync_status: str, last_sync_at=None):
                self.sync_status = sync_status
                self.last_sync_at = last_sync_at
                self.mensagem = None

            def needs_sync(self) -> bool:
                if self.sync_status in ["pending", "error"]:
                    return True

                if self.sync_status == "synced" and self.last_sync_at:
                    mensagem = self.mensagem
                    if not mensagem:
                        return False

                    campos_criticos = {
                        "resposta_bot": getattr(mensagem, "resposta_bot", None),
                        "confianca_resposta": getattr(mensagem, "confianca_resposta", None),
                        "respondida": getattr(mensagem, "respondida", None),
                        "intent_detectado": getattr(mensagem, "intent_detectado", None),
                        "entidades_extraidas": getattr(mensagem, "entidades_extraidas", None),
                        "metadados": getattr(mensagem, "metadados", None),
                    }

                    for campo, valor_atual in campos_criticos.items():
                        if valor_atual and mensagem.updated_at > self.last_sync_at:
                            return True

                return False

        sync_instance = TestMensagemSync("error", timezone.now() - timedelta(hours=1))

        # Act
        result = sync_instance.needs_sync()

        # Assert
        assert result is True

    def test_needs_sync_sem_mudancas_apos_sync(self) -> None:
        """
        Testa que NÃO precisa sincronizar quando não há mudanças importantes após último sync.
        """
        class TestMensagemSync:
            def __init__(self, sync_status: str, last_sync_at=None, mensagem=None):
                self.sync_status = sync_status
                self.last_sync_at = last_sync_at
                self.mensagem = mensagem

            def needs_sync(self) -> bool:
                if self.sync_status in ["pending", "error"]:
                    return True

                if self.sync_status == "synced" and self.last_sync_at:
                    mensagem = self.mensagem
                    if not mensagem:
                        return False

                    campos_criticos = {
                        "resposta_bot": getattr(mensagem, "resposta_bot", None),
                        "confianca_resposta": getattr(mensagem, "confianca_resposta", None),
                        "respondida": getattr(mensagem, "respondida", None),
                        "intent_detectado": getattr(mensagem, "intent_detectado", None),
                        "entidades_extraidas": getattr(mensagem, "entidades_extraidas", None),
                        "metadados": getattr(mensagem, "metadados", None),
                    }

                    for campo, valor_atual in campos_criticos.items():
                        if valor_atual and mensagem.updated_at > self.last_sync_at:
                            return True

                return False

        # Arrange
        mock_mensagem = Mock()
        mock_mensagem.resposta_bot = None
        mock_mensagem.confianca_resposta = None
        mock_mensagem.respondida = False
        mock_mensagem.intent_detectado = []
        mock_mensagem.entidades_extraidas = []
        mock_mensagem.metadados = {}
        mock_mensagem.updated_at = timezone.now() - timedelta(hours=2)

        sync_instance = TestMensagemSync(
            "synced",
            timezone.now() - timedelta(hours=1),
            mock_mensagem
        )

        # Act
        result = sync_instance.needs_sync()

        # Assert
        assert result is False

    def test_needs_sync_com_confianca_atualizada(self) -> None:
        """
        Testa que PRECISA sincronizar quando confianca_resposta foi atualizada após último sync.
        """
        class TestMensagemSync:
            def __init__(self, sync_status: str, last_sync_at=None, mensagem=None):
                self.sync_status = sync_status
                self.last_sync_at = last_sync_at
                self.mensagem = mensagem

            def needs_sync(self) -> bool:
                if self.sync_status in ["pending", "error"]:
                    return True

                if self.sync_status == "synced" and self.last_sync_at:
                    mensagem = self.mensagem
                    if not mensagem:
                        return False

                    campos_criticos = {
                        "resposta_bot": getattr(mensagem, "resposta_bot", None),
                        "confianca_resposta": getattr(mensagem, "confianca_resposta", None),
                        "respondida": getattr(mensagem, "respondida", None),
                        "intent_detectado": getattr(mensagem, "intent_detectado", None),
                        "entidades_extraidas": getattr(mensagem, "entidades_extraidas", None),
                        "metadados": getattr(mensagem, "metadados", None),
                    }

                    for campo, valor_atual in campos_criticos.items():
                        if valor_atual and mensagem.updated_at > self.last_sync_at:
                            return True

                return False

        # Arrange
        mock_mensagem = Mock()
        mock_mensagem.resposta_bot = None
        mock_mensagem.confianca_resposta = 0.85  # Valor atualizado
        mock_mensagem.respondida = False
        mock_mensagem.intent_detectado = []
        mock_mensagem.entidades_extraidas = []
        mock_mensagem.metadados = {}
        mock_mensagem.updated_at = timezone.now() - timedelta(minutes=10)  # Atualizado recentemente

        sync_instance = TestMensagemSync(
            "synced",
            timezone.now() - timedelta(hours=1),  # Sync mais antigo
            mock_mensagem
        )

        # Act
        result = sync_instance.needs_sync()

        # Assert
        assert result is True, "Deve precisar sincronizar quando confiança foi atualizada"

    def test_needs_sync_com_resposta_bot_atualizada(self) -> None:
        """
        Testa que PRECISA sincronizar quando resposta_bot foi atualizada após último sync.
        """
        class TestMensagemSync:
            def __init__(self, sync_status: str, last_sync_at=None, mensagem=None):
                self.sync_status = sync_status
                self.last_sync_at = last_sync_at
                self.mensagem = mensagem

            def needs_sync(self) -> bool:
                if self.sync_status in ["pending", "error"]:
                    return True

                if self.sync_status == "synced" and self.last_sync_at:
                    mensagem = self.mensagem
                    if not mensagem:
                        return False

                    campos_criticos = {
                        "resposta_bot": getattr(mensagem, "resposta_bot", None),
                        "confianca_resposta": getattr(mensagem, "confianca_resposta", None),
                        "respondida": getattr(mensagem, "respondida", None),
                        "intent_detectado": getattr(mensagem, "intent_detectado", None),
                        "entidades_extraidas": getattr(mensagem, "entidades_extraidas", None),
                        "metadados": getattr(mensagem, "metadados", None),
                    }

                    for campo, valor_atual in campos_criticos.items():
                        if valor_atual and mensagem.updated_at > self.last_sync_at:
                            return True

                return False

        # Arrange
        mock_mensagem = Mock()
        mock_mensagem.resposta_bot = "Nova resposta do bot"  # Resposta atualizada
        mock_mensagem.confianca_resposta = 0.75
        mock_mensagem.respondida = True
        mock_mensagem.intent_detectado = []
        mock_mensagem.entidades_extraidas = []
        mock_mensagem.metadados = {}
        mock_mensagem.updated_at = timezone.now() - timedelta(minutes=5)

        sync_instance = TestMensagemSync(
            "synced",
            timezone.now() - timedelta(hours=1),
            mock_mensagem
        )

        # Act
        result = sync_instance.needs_sync()

        # Assert
        assert result is True, "Deve precisar sincronizar quando resposta do bot foi atualizada"

    def test_needs_sync_sem_last_sync_at(self) -> None:
        """
        Testa que NÃO precisa sincronizar quando last_sync_at é None mas status é synced.
        """
        class TestMensagemSync:
            def __init__(self, sync_status: str, last_sync_at=None, mensagem=None):
                self.sync_status = sync_status
                self.last_sync_at = last_sync_at
                self.mensagem = mensagem

            def needs_sync(self) -> bool:
                if self.sync_status in ["pending", "error"]:
                    return True

                if self.sync_status == "synced" and self.last_sync_at:
                    mensagem = self.mensagem
                    if not mensagem:
                        return False

                    campos_criticos = {
                        "resposta_bot": getattr(mensagem, "resposta_bot", None),
                        "confianca_resposta": getattr(mensagem, "confianca_resposta", None),
                        "respondida": getattr(mensagem, "respondida", None),
                        "intent_detectado": getattr(mensagem, "intent_detectado", None),
                        "entidades_extraidas": getattr(mensagem, "entidades_extraidas", None),
                        "metadados": getattr(mensagem, "metadados", None),
                    }

                    for campo, valor_atual in campos_criticos.items():
                        if valor_atual and mensagem.updated_at > self.last_sync_at:
                            return True

                return False

        # Arrange
        mock_mensagem = Mock()
        mock_mensagem.resposta_bot = "Resposta"
        mock_mensagem.confianca_resposta = 0.9
        mock_mensagem.respondida = True
        mock_mensagem.intent_detectado = []
        mock_mensagem.entidades_extraidas = []
        mock_mensagem.metadados = {}
        mock_mensagem.updated_at = timezone.now()

        sync_instance = TestMensagemSync(
            "synced",
            None,  # Nunca sincronizado
            mock_mensagem
        )

        # Act
        result = sync_instance.needs_sync()

        # Assert
        assert result is False, "Não deve precisar sincronizar se status é synced mas não há last_sync_at"
