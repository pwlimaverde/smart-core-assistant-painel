"""Teste do sinal de Departamento para provisionamento no ClickUp.

Valida que ao criar um `Departamento`, o serviço de provisionamento
`DepartmentProvisionService` é acionado para garantir Space e Folder.
"""

from __future__ import annotations

from typing import Any

from django.test import TestCase
from unittest.mock import patch

from smart_core_assistant_painel.app.ui.operacional.models import Departamento


class TestDepartamentoSignalClickUp(TestCase):
    """Testes para sinal post_save de Departamento (ClickUp)."""

    def test_dispara_provisionamento_ao_criar_departamento(self) -> None:
        """Criar Departamento deve acionar o serviço de provisionamento."""
        with patch(
            (
                "smart_core_assistant_painel.app.clickup_sync.signals."
                "DepartmentProvisionService.provision_on_department_create"
            )
        ) as mocked:
            dep = Departamento.objects.create(nome="Suporte")
            # Asserta que foi chamado com a instância criada
            mocked.assert_called_once()
            args: tuple[Any, ...] = mocked.call_args[0]
            assert args and args[0].id == dep.id