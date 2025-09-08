"""Testes para a interface administrativa do app Treinamento."""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from smart_core_assistant_painel.app.ui.treinamento.admin import TreinamentoAdmin
from smart_core_assistant_painel.app.ui.treinamento.models import Treinamento


class TestTreinamentoTreinamentosAdmin(TestCase):
    """Testes para o admin do modelo Treinamentos."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = TreinamentoAdmin(Treinamento, self.site)

        self.treinamento = Treinamento.objects.create(
            tag="teste",
            grupo="grupo_teste",
            conteudo="Documento de teste",
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "id",
            "tag",
            "grupo",
            "treinamento_finalizado",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = ["tag"]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_readonly_fields(self) -> None:
        """Testa os campos somente leitura."""
        self.assertEqual(self.admin.readonly_fields, ["embedding_preview"])
