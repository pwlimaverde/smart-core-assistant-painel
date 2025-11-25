"""Testes para a interface administrativa do app Clientes."""

from typing import Optional

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from smart_core_assistant_painel.app.ui.clientes.admin import ContatoAdmin
from smart_core_assistant_painel.app.ui.clientes.models import Contato


class MockRequest:
    """Mock request para testes do admin."""

    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user or User()


class TestClientesContatoAdmin(TestCase):
    """Testes para o admin do modelo Contato."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = ContatoAdmin(Contato, self.site)
        self.factory = RequestFactory()

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "telefone",
            "nome_contato",
            "nome_perfil_whatsapp",
            "data_cadastro",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = ["telefone", "nome_contato", "nome_perfil_whatsapp"]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = ["data_cadastro", "ultima_interacao", "ativo"]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_readonly_fields(self) -> None:
        """Testa os campos somente leitura."""
        expected_readonly = ["data_cadastro", "ultima_interacao"]
        for field in expected_readonly:
            self.assertIn(field, self.admin.readonly_fields)
