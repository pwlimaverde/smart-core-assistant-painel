"""Testes para a interface administrativa do app Operacional."""

from typing import Optional

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase

from ..admin import AtendenteHumanoAdmin
from ..models import AtendenteHumano


class MockRequest:
    """Mock request para testes do admin."""

    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user or User()


class TestAtendenteHumanoAdmin(TestCase):
    """Testes para o admin do modelo AtendenteHumano."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = AtendenteHumanoAdmin(AtendenteHumano, self.site)

        self.atendente = AtendenteHumano.objects.create(
            telefone="5511888888888",
            nome="Atendente Teste",
            cargo="Analista",
            email="atendente@teste.com",
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "nome",
            "cargo",
            "telefone",
            "email",
            "ativo",
            "disponivel",
            "max_atendimentos_simultaneos",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = ["ativo", "disponivel", "cargo"]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = ["nome", "cargo", "telefone", "email"]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)
