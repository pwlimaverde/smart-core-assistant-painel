"""
Testes para o app notion_sync.

Este módulo contém testes unitários para validar o funcionamento
dos models, signals e funcionalidades do sistema de sincronização.
"""

from datetime import datetime
from typing import Any

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase

from ..ui.clientes.models import Cliente, Contato
from .models import ClienteSync, ContatoSync, SyncConfig, SyncLog


class SyncConfigTestCase(TestCase):
    """
    Testes para o model SyncConfig.

    Valida operações de criação, atualização e recuperação de configurações.
    """

    def test_create_config(self) -> None:
        """Testa criação de configuração."""
        config = SyncConfig.objects.create(
            key="test_key",
            value="test_value",
            description="Configuração de teste",
        )

        assert config.key == "test_key"
        assert config.value == "test_value"
        assert config.description == "Configuração de teste"
        assert config.is_active is True

    def test_unique_key(self) -> None:
        """Testa que chaves devem ser únicas."""
        SyncConfig.objects.create(key="duplicate_key", value="value1")

        with pytest.raises(IntegrityError):
            SyncConfig.objects.create(key="duplicate_key", value="value2")

    def test_get_value(self) -> None:
        """Testa recuperação de valor por chave."""
        SyncConfig.objects.create(
            key="notion_token", value="secret_xxx", is_active=True
        )

        value = SyncConfig.get_value("notion_token")
        assert value == "secret_xxx"

    def test_get_value_default(self) -> None:
        """Testa retorno de valor padrão quando chave não existe."""
        value = SyncConfig.get_value(
            "nonexistent_key", default="default_value"
        )
        assert value == "default_value"

    def test_get_value_inactive(self) -> None:
        """Testa que configurações inativas não são retornadas."""
        SyncConfig.objects.create(
            key="inactive_key", value="some_value", is_active=False
        )

        value = SyncConfig.get_value("inactive_key", default="default")
        assert value == "default"

    def test_set_value(self) -> None:
        """Testa definição de valor via método helper."""
        config = SyncConfig.set_value(
            key="new_key", value="new_value", description="Nova configuração"
        )

        assert config.key == "new_key"
        assert config.value == "new_value"
        assert config.is_active is True

    def test_set_value_update(self) -> None:
        """Testa que set_value atualiza configuração existente."""
        SyncConfig.set_value(key="update_key", value="old_value")
        SyncConfig.set_value(key="update_key", value="new_value")

        assert SyncConfig.objects.filter(key="update_key").count() == 1
        config = SyncConfig.objects.get(key="update_key")
        assert config.value == "new_value"

    def test_json_value(self) -> None:
        """Testa armazenamento de valores JSON complexos."""
        complex_value = {
            "database_ids": {"Cliente": "abc-123", "Contato": "xyz-789"},
            "options": {"retry_attempts": 3, "timeout": 30},
        }

        config = SyncConfig.set_value(
            key="complex_config", value=complex_value
        )
        retrieved = SyncConfig.get_value("complex_config")

        assert retrieved == complex_value
        assert retrieved["database_ids"]["Cliente"] == "abc-123"


class SyncLogTestCase(TestCase):
    """
    Testes para o model SyncLog.

    Valida logging de operações de sincronização.
    """

    def test_create_log(self) -> None:
        """Testa criação de log de sincronização."""
        log = SyncLog.objects.create(
            model_name="Cliente",
            django_id=123,
            external_id="notion-page-id",
            operation="create",
            direction="django_to_external",
            status="success",
        )

        assert log.model_name == "Cliente"
        assert log.django_id == 123
        assert log.external_id == "notion-page-id"
        assert log.operation == "create"
        assert log.status == "success"

    def test_log_operation_helper(self) -> None:
        """Testa método helper para criar logs."""
        log = SyncLog.log_operation(
            model_name="Contato",
            django_id=456,
            external_id="page-789",
            operation="update",
            direction="django_to_external",
            status="success",
            duration_ms=250,
        )

        assert log.model_name == "Contato"
        assert log.django_id == 456
        assert log.duration_ms == 250

    def test_log_with_error(self) -> None:
        """Testa log de operação com erro."""
        log = SyncLog.log_operation(
            model_name="Cliente",
            django_id=789,
            external_id=None,
            operation="create",
            direction="django_to_external",
            status="error",
            error_message="API timeout",
            error_details={"code": 500, "message": "Internal Server Error"},
        )

        assert log.status == "error"
        assert log.error_message == "API timeout"
        assert log.error_details is not None
        assert log.error_details["code"] == 500

    def test_log_ordering(self) -> None:
        """Testa que logs são ordenados por data decrescente."""
        SyncLog.log_operation(
            model_name="Cliente",
            django_id=1,
            external_id=None,
            operation="create",
            direction="django_to_external",
            status="success",
        )
        SyncLog.log_operation(
            model_name="Cliente",
            django_id=2,
            external_id=None,
            operation="create",
            direction="django_to_external",
            status="success",
        )

        logs = list(SyncLog.objects.all())
        assert logs[0].django_id == 2  # Mais recente primeiro
        assert logs[1].django_id == 1


class ContatoSyncTestCase(TransactionTestCase):
    """
    Testes para o model ContatoSync.

    Valida tracking de sincronização de Contatos.
    """

    def test_create_tracking(self) -> None:
        """Testa criação de tracking para contato."""
        contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="João Silva"
        )

        sync_meta = ContatoSync.objects.create(contato=contato)

        assert sync_meta.contato == contato
        assert sync_meta.is_synced is False
        assert sync_meta.external_id is None
        assert sync_meta.sync_attempts == 0

    def test_one_to_one_relation(self) -> None:
        """Testa relação one-to-one com Contato."""
        contato = Contato.objects.create(
            telefone="5511888888888", nome_contato="Maria Santos"
        )

        sync_meta = ContatoSync.objects.create(contato=contato)

        # Acessa via related_name
        assert contato.sync_metadata == sync_meta

    def test_mark_as_synced(self) -> None:
        """Testa método para marcar como sincronizado."""
        contato = Contato.objects.create(
            telefone="5511777777777", nome_contato="Pedro Oliveira"
        )
        sync_meta = ContatoSync.objects.create(contato=contato)

        sync_meta.mark_as_synced(external_id="notion-page-123")

        assert sync_meta.is_synced is True
        assert sync_meta.external_id == "notion-page-123"
        assert sync_meta.last_synced_at is not None
        assert sync_meta.sync_error is None
        assert sync_meta.sync_attempts == 1

    def test_mark_as_failed(self) -> None:
        """Testa método para marcar como falha."""
        contato = Contato.objects.create(
            telefone="5511666666666", nome_contato="Ana Costa"
        )
        sync_meta = ContatoSync.objects.create(contato=contato)

        sync_meta.mark_as_failed(error_message="API Error: 500")

        assert sync_meta.is_synced is False
        assert sync_meta.sync_error == "API Error: 500"
        assert sync_meta.sync_attempts == 1

    def test_cascade_delete(self) -> None:
        """Testa que tracking é deletado quando contato é deletado."""
        contato = Contato.objects.create(
            telefone="5511555555555", nome_contato="Carlos Lima"
        )
        sync_meta = ContatoSync.objects.create(contato=contato)
        sync_id = sync_meta.id

        contato.delete()

        assert not ContatoSync.objects.filter(id=sync_id).exists()


class ClienteSyncTestCase(TransactionTestCase):
    """
    Testes para o model ClienteSync.

    Valida tracking de sincronização de Clientes.
    """

    def test_create_tracking(self) -> None:
        """Testa criação de tracking para cliente."""
        cliente = Cliente.objects.create(
            nome_fantasia="Empresa XYZ Ltda", tipo="juridica"
        )

        sync_meta = ClienteSync.objects.create(cliente=cliente)

        assert sync_meta.cliente == cliente
        assert sync_meta.is_synced is False
        assert sync_meta.external_id is None
        assert sync_meta.sync_attempts == 0

    def test_one_to_one_relation(self) -> None:
        """Testa relação one-to-one com Cliente."""
        cliente = Cliente.objects.create(
            nome_fantasia="Consultoria ABC", tipo="juridica"
        )

        sync_meta = ClienteSync.objects.create(cliente=cliente)

        # Acessa via related_name
        assert cliente.sync_metadata == sync_meta

    def test_mark_as_synced(self) -> None:
        """Testa método para marcar como sincronizado."""
        cliente = Cliente.objects.create(
            nome_fantasia="Tech Solutions", tipo="juridica"
        )
        sync_meta = ClienteSync.objects.create(cliente=cliente)

        sync_meta.mark_as_synced(external_id="notion-page-456")

        assert sync_meta.is_synced is True
        assert sync_meta.external_id == "notion-page-456"
        assert sync_meta.last_synced_at is not None
        assert sync_meta.sync_error is None
        assert sync_meta.sync_attempts == 1

    def test_mark_as_failed(self) -> None:
        """Testa método para marcar como falha."""
        cliente = Cliente.objects.create(
            nome_fantasia="Digital Corp", tipo="juridica"
        )
        sync_meta = ClienteSync.objects.create(cliente=cliente)

        sync_meta.mark_as_failed(error_message="Connection timeout")

        assert sync_meta.is_synced is False
        assert sync_meta.sync_error == "Connection timeout"
        assert sync_meta.sync_attempts == 1

    def test_cascade_delete(self) -> None:
        """Testa que tracking é deletado quando cliente é deletado."""
        cliente = Cliente.objects.create(
            nome_fantasia="Test Company", tipo="juridica"
        )
        sync_meta = ClienteSync.objects.create(cliente=cliente)
        sync_id = sync_meta.id

        cliente.delete()

        assert not ClienteSync.objects.filter(id=sync_id).exists()


class SignalsTestCase(TransactionTestCase):
    """
    Testes para os signals de sincronização.

    Valida que signals são disparados e tracking é criado automaticamente.
    """

    def test_contato_signal_on_create(self) -> None:
        """Testa que signal cria tracking ao criar contato."""
        contato = Contato.objects.create(
            telefone="5511444444444", nome_contato="Signal Test"
        )

        # Verifica que tracking foi criado automaticamente
        assert hasattr(contato, "sync_metadata")
        assert ContatoSync.objects.filter(contato=contato).exists()

        sync_meta = contato.sync_metadata
        assert sync_meta.is_synced is False

    def test_contato_signal_on_update(self) -> None:
        """Testa que signal marca para re-sincronização ao atualizar."""
        contato = Contato.objects.create(
            telefone="5511333333333", nome_contato="Update Test"
        )

        # Marca como sincronizado manualmente
        sync_meta = contato.sync_metadata
        sync_meta.mark_as_synced(external_id="page-abc")

        # Atualiza contato
        contato.nome_contato = "Nome Atualizado"
        contato.save()

        # Recarrega do banco
        sync_meta.refresh_from_db()

        # Deve estar marcado como não sincronizado
        assert sync_meta.is_synced is False

    def test_cliente_signal_on_create(self) -> None:
        """Testa que signal cria tracking ao criar cliente."""
        cliente = Cliente.objects.create(
            nome_fantasia="Signal Test Corp", tipo="juridica"
        )

        # Verifica que tracking foi criado automaticamente
        assert hasattr(cliente, "sync_metadata")
        assert ClienteSync.objects.filter(cliente=cliente).exists()

        sync_meta = cliente.sync_metadata
        assert sync_meta.is_synced is False

    def test_cliente_signal_on_update(self) -> None:
        """Testa que signal marca para re-sincronização ao atualizar."""
        cliente = Cliente.objects.create(
            nome_fantasia="Update Test Corp", tipo="juridica"
        )

        # Marca como sincronizado manualmente
        sync_meta = cliente.sync_metadata
        sync_meta.mark_as_synced(external_id="page-xyz")

        # Atualiza cliente
        cliente.nome_fantasia = "Nome Atualizado Corp"
        cliente.save()

        # Recarrega do banco
        sync_meta.refresh_from_db()

        # Deve estar marcado como não sincronizado
        assert sync_meta.is_synced is False

    def test_sync_log_created_on_save(self) -> None:
        """Testa que log é criado quando model é salvo."""
        initial_count = SyncLog.objects.count()

        contato = Contato.objects.create(
            telefone="5511222222222", nome_contato="Log Test"
        )

        # Deve ter criado pelo menos um log
        assert SyncLog.objects.count() > initial_count

        # Verifica que existe log para este contato
        logs = SyncLog.objects.filter(
            model_name="Contato", django_id=contato.id
        )
        assert logs.exists()
        assert logs.first().operation == "create"
        assert logs.first().status == "pending"
