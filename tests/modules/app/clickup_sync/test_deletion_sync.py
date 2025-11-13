"""Testes para validar a sincronização de exclusão com ClickUp."""

from unittest.mock import MagicMock, patch


import pytest
from django.test import TestCase
from django.db.models.signals import pre_delete

from smart_core_assistant_painel.app.clickup_sync.models import (
    ClickupList,
    ClickupTask,
    ClickupMember,
    ClickupSpace,
)
from smart_core_assistant_painel.app.clickup_sync.services import (
    FlowSyncService,
    TicketSyncService,
    MemberSyncService,
    DepartmentProvisionService,
)
from smart_core_assistant_painel.app.clickup_sync.tasks import (
    task_fluxo_delete_list,
    task_atendimento_delete_task,
    task_atendente_remove_member,
    task_departamento_delete_folder,
)
from smart_core_assistant_painel.app.ui.operacional.models import (
    FluxoAtendimento,
    EtapaFluxo,
    Departamento,
    Atendente,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento
from smart_core_assistant_painel.app.ui.clientes.models import Contato


class TestDeletionSync(TestCase):
    """Testa as funcionalidades de exclusão e sincronização."""

    def setUp(self) -> None:
        """Configura o ambiente de testes."""
        self.departamento = Departamento.objects.create(
            nome="Departamento Teste"
        )
        self.fluxo = FluxoAtendimento.objects.create(
            nome="Fluxo Teste",
            departamento=self.departamento,
        )
        self.etapa = EtapaFluxo.objects.create(
            nome="Etapa Teste",
            fluxo=self.fluxo,
            ordem=1,
        )
        self.atendente = Atendente.objects.create(
            nome="Atendente Teste",
            email="atendente@teste.com",
        )
        self.contato = Contato.objects.create(
            nome_contato="Contato Teste",
            email="contato@teste.com",
            telefone="11999999999",
        )
        self.atendimento = Atendimento.objects.create(
            assunto="Assunto Teste",
            contato=self.contato,
            fluxo_atendimento=self.fluxo,
            etapa_atual=self.etapa,
            atendente_humano=self.atendente,
        )

    def test_fluxo_delete_list_task(self) -> None:
        """Testa a task de exclusão de lista de fluxo."""
        # Mocka o serviço para simular a exclusão
        with patch.object(
            FlowSyncService, "delete_list_for_fluxo"
        ) as mock_delete:
            task_fluxo_delete_list(self.fluxo.id)
            mock_delete.assert_called_once_with(self.fluxo.id)

    def test_fluxo_delete_list_service(self) -> None:
        """Testa o serviço de exclusão de lista de fluxo."""
        clickup_list = ClickupList.objects.create(
            fluxo_atendimento_id=self.fluxo.id,
            external_id="test-list-id",
            name="Test List",
            space_external_id="test-space-id",
        )

        # Mocka o adapter do ClickUp
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.services.flow_sync_service.ClicupUnifiedDataService"
        ) as mock_adapter:
            mock_service = MagicMock()
            mock_service.delete_list.return_value = True
            mock_adapter.return_value = mock_service

            service = FlowSyncService()
            service.delete_list_for_fluxo(self.fluxo.id)

            # Verifica se o método delete_list foi chamado
            mock_service.delete_list.assert_called_once_with("test-list-id")

            # Verifica se o registro foi removido do banco
            with self.assertRaises(ClickupList.DoesNotExist):
                ClickupList.objects.get(id=clickup_list.id)

    def test_atendimento_delete_task_task(self) -> None:
        """Testa a task de exclusão de task de atendimento."""
        # Mocka o serviço para simular a exclusão
        with patch.object(TicketSyncService, "delete_task") as mock_delete:
            task_atendimento_delete_task(self.atendimento.id)
            mock_delete.assert_called_once_with(self.atendimento.id)

    def test_atendimento_delete_task_service(self) -> None:
        """Testa o serviço de exclusão de task de atendimento."""
        clickup_task = ClickupTask.objects.create(
            atendimento_id=self.atendimento.id,
            external_id="test-task-id",
            name="Test Task",
            list_external_id="test-list-id",
        )

        # Mocka o adapter do ClickUp
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.services.ticket_sync_service.ClicupUnifiedDataService"
        ) as mock_adapter:
            mock_service = MagicMock()
            mock_service.delete_item.return_value = True
            mock_adapter.return_value = mock_service

            service = TicketSyncService()
            result = service.delete_task(self.atendimento.id)

            # Verifica se o método delete_item foi chamado
            mock_service.delete_item.assert_called_once_with("test-task-id")

            # Verifica se o método retornou True
            self.assertTrue(result)

            # Verifica se o registro foi removido do banco
            with self.assertRaises(ClickupTask.DoesNotExist):
                ClickupTask.objects.get(id=clickup_task.id)

    def test_atendente_remove_member_task(self) -> None:
        """Testa a task de remoção de membro atendente."""
        # Mocka o serviço para simular a exclusão
        with patch.object(MemberSyncService, "remove_member") as mock_remove:
            task_atendente_remove_member(self.atendente.id)
            mock_remove.assert_called_once_with(self.atendente.id)

    def test_atendente_remove_member_service_real(self) -> None:
        """Testa o serviço de remoção de membro atendente (ID real)."""
        clickup_member = ClickupMember.objects.create(
            atendente_id=self.atendente.id,
            external_id="real-member-id",
            username="test-username",
        )

        # Mocka o adapter do ClickUp
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.services.member_sync_service.ClicupUnifiedDataService"
        ) as mock_adapter:
            mock_service = MagicMock()
            mock_service.remove_member.return_value = True
            mock_adapter.return_value = mock_service

            service = MemberSyncService()
            result = service.remove_member(self.atendente.id)

            # Verifica se o método remove_member foi chamado
            mock_service.remove_member.assert_called_once_with(
                "real-member-id"
            )

            # Verifica se o método retornou True
            self.assertTrue(result)

            # Verifica se o registro foi removido do banco
            with self.assertRaises(ClickupMember.DoesNotExist):
                ClickupMember.objects.get(id=clickup_member.id)

    def test_atendente_remove_member_service_local(self) -> None:
        """Testa o serviço de remoção de membro atendente (ID local)."""
        clickup_member = ClickupMember.objects.create(
            atendente_id=self.atendente.id,
            external_id="local-123",
            username="test-username",
        )

        # Mocka o adapter do ClickUp
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.services.member_sync_service.ClicupUnifiedDataService"
        ) as mock_adapter:
            mock_service = MagicMock()
            mock_adapter.return_value = mock_service

            service = MemberSyncService()
            result = service.remove_member(self.atendente.id)

            # Verifica que o método remove_member NÃO foi chamado (é ID local)
            mock_service.remove_member.assert_not_called()

            # Verifica se o método retornou True
            self.assertTrue(result)

            # Verifica se o registro foi removido do banco
            with self.assertRaises(ClickupMember.DoesNotExist):
                ClickupMember.objects.get(id=clickup_member.id)

    def test_departamento_delete_folder_task(self) -> None:
        """Testa a task de exclusão de folder de departamento."""
        # Mocka o serviço para simular a exclusão
        with patch.object(
            DepartmentProvisionService, "delete_on_department_delete"
        ) as mock_delete:
            task_departamento_delete_folder(self.departamento.id)
            mock_delete.assert_called_once()

    def test_departamento_delete_folder_service(self) -> None:
        """Testa o serviço de exclusão de folder de departamento."""
        clickup_space = ClickupSpace.objects.create(
            departamento_id=self.departamento.id,
            external_id="test-space-id",
            name="Test Space",
        )

        # Mocka o adapter do ClickUp
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.services.department_provision_service.ClicupUnifiedDataService"
        ) as mock_adapter:
            mock_service = MagicMock()
            mock_service.find_folder_by_name.return_value = {
                "id": "test-folder-id"
            }
            mock_service.delete_folder.return_value = True
            mock_adapter.return_value = mock_service

            service = DepartmentProvisionService()
            service.delete_on_department_delete(self.departamento)

            # Verifica se os métodos foram chamados corretamente
            mock_service.find_folder_by_name.assert_called_once_with(
                "test-space-id", "Departamento Teste"
            )
            mock_service.delete_folder.assert_called_once_with(
                "test-folder-id"
            )

            # Verifica se o registro foi removido do banco
            with self.assertRaises(ClickupSpace.DoesNotExist):
                ClickupSpace.objects.get(id=clickup_space.id)

    def test_signal_fluxo_deleted(self) -> None:
        """Testa se o signal de exclusão de fluxo é disparado corretamente."""
        clickup_list = ClickupList.objects.create(
            fluxo_atendimento_id=self.fluxo.id,
            external_id="test-list-id",
            name="Test List",
            space_external_id="test-space-id",
        )

        # Mocka a task assíncrona
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.signals.async_task"
        ) as mock_async:
            # Dispara o signal
            pre_delete.send(
                sender=FluxoAtendimento,
                instance=self.fluxo,
            )

            # Verifica se a task foi chamada com os parâmetros corretos
            mock_async.assert_called_once_with(
                "smart_core_assistant_painel.app.clickup_sync.tasks.task_fluxo_delete_list",
                self.fluxo.id,
            )

    def test_signal_atendimento_deleted(self) -> None:
        """Testa se o signal de exclusão de atendimento é disparado corretamente."""
        clickup_task = ClickupTask.objects.create(
            atendimento_id=self.atendimento.id,
            external_id="test-task-id",
            name="Test Task",
            list_external_id="test-list-id",
        )

        # Mocka a task assíncrona
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.signals.async_task"
        ) as mock_async:
            # Dispara o signal
            pre_delete.send(
                sender=Atendimento,
                instance=self.atendimento,
            )

            # Verifica se a task foi chamada com os parâmetros corretos
            mock_async.assert_called_once_with(
                "smart_core_assistant_painel.app.clickup_sync.tasks.task_atendimento_delete_task",
                self.atendimento.id,
            )

    def test_signal_atendente_deleted(self) -> None:
        """Testa se o signal de exclusão de atendente é disparado corretamente."""
        clickup_member = ClickupMember.objects.create(
            atendente_id=self.atendente.id,
            external_id="test-member-id",
            username="test-username",
        )

        # Mocka a task assíncrona
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.signals.async_task"
        ) as mock_async:
            # Dispara o signal
            pre_delete.send(
                sender=Atendente,
                instance=self.atendente,
            )

            # Verifica se a task foi chamada com os parâmetros corretos
            mock_async.assert_called_once_with(
                "smart_core_assistant_painel.app.clickup_sync.tasks.task_atendente_remove_member",
                self.atendente.id,
            )

    def test_signal_departamento_deleted(self) -> None:
        """Testa se o signal de exclusão de departamento é disparado corretamente."""
        clickup_space = ClickupSpace.objects.create(
            departamento_id=self.departamento.id,
            external_id="test-space-id",
            name="Test Space",
        )

        # Mocka a task assíncrona
        with patch(
            "smart_core_assistant_painel.app.clickup_sync.signals.async_task"
        ) as mock_async:
            # Dispara o signal
            pre_delete.send(
                sender=Departamento,
                instance=self.departamento,
            )

            # Verifica se a task foi chamada com os parâmetros corretos
            mock_async.assert_called_once_with(
                "smart_core_assistant_painel.app.clickup_sync.tasks.task_departamento_delete_folder",
                self.departamento.id,
            )

    def test_clickup_adapter_delete_item(self) -> None:
        """Testa o método delete_item do adapter do ClickUp."""
        from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
            ClicupUnifiedDataService,
        )
        from smart_core_assistant_painel.modules.services.utils.parameters import (
            UnifieldDataServicesParameters,
        )
        from smart_core_assistant_painel.modules.services.utils.erros import (
            UnifieldDataServicesError,
        )

        # Mocka os parâmetros e o token
        with patch(
            "smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config"
        ) as mock_config:
            mock_config.side_effect = lambda key, default=None: default
            with patch.object(
                ClicupUnifiedDataService,
                "_get_team_id",
                return_value="test-team-id",
            ):
                params = UnifieldDataServicesParameters(
                    data_source_id="",
                    provider="clickup",
                    root_container_name="Unified Data Root",
                    enable_observability=True,
                    error=UnifieldDataServicesError(
                        message="UDS ClickUp error"
                    ),
                )

                # Mocka o método _request
                with patch.object(
                    ClicupUnifiedDataService, "_request", return_value={}
                ) as mock_request:
                    adapter = ClicupUnifiedDataService(params)

                    # Testa exclusão bem sucedida
                    result = adapter.delete_item("test-task-id")

                    mock_request.assert_called_once_with(
                        "DELETE", "/task/test-task-id"
                    )
                    self.assertTrue(result)

    def test_clickup_adapter_delete_list(self) -> None:
        """Testa o método delete_list do adapter do ClickUp."""
        from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
            ClicupUnifiedDataService,
        )
        from smart_core_assistant_painel.modules.services.utils.parameters import (
            UnifieldDataServicesParameters,
        )
        from smart_core_assistant_painel.modules.services.utils.erros import (
            UnifieldDataServicesError,
        )

        # Mocka os parâmetros e o token
        with patch(
            "smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter.config"
        ) as mock_config:
            mock_config.side_effect = lambda key, default=None: default
            with patch.object(
                ClicupUnifiedDataService,
                "_get_team_id",
                return_value="test-team-id",
            ):
                params = UnifieldDataServicesParameters(
                    data_source_id="",
                    provider="clickup",
                    root_container_name="Unified Data Root",
                    enable_observability=True,
                    error=UnifieldDataServicesError(
                        message="UDS ClickUp error"
                    ),
                )

                # Mocka o método _request
                with patch.object(
                    ClicupUnifiedDataService, "_request", return_value={}
                ) as mock_request:
                    adapter = ClicupUnifiedDataService(params)

                    # Testa exclusão bem sucedida
                    result = adapter.delete_list("test-list-id")

                    mock_request.assert_called_once_with(
                        "DELETE", "/list/test-list-id"
                    )
                    self.assertTrue(result)
