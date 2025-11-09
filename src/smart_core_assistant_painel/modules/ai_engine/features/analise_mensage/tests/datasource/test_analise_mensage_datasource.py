"""Testes para o datasource de análise de mensagem."""

from django.test import TestCase

from smart_core_assistant_painel.modules.ai_engine.features.analise_mensage.datasource.analise_mensage_datasource import (
    AnaliseMensageDatasource,
)


class TestAnaliseMensageDatasource(TestCase):
    """Testes para o AnaliseMensageDatasource."""

    def setUp(self) -> None:
        """Configura o ambiente de testes."""
        self.datasource = AnaliseMensageDatasource()

    def test_formatar_fluxos_disponiveis_com_dados(self) -> None:
        """Testa formatação com fluxos disponíveis."""
        fluxos_disponiveis = {
            "Atendimento Comercial - Vendas": "Quadro responsável por centralizar e organizar os atendimentos aos clientes que precisam de atendimento comercial",
            "Suporte Técnico - Suporte": "Fluxo para atendimento de suporte técnico",
        }

        resultado = self.datasource._formatar_fluxos_disponiveis(
            fluxos_disponiveis
        )

        self.assertIn("SETORES DISPONÍVEIS PARA TRANSFERÊNCIA:", resultado)
        self.assertIn("Atendimento Comercial - Vendas", resultado)
        self.assertIn("Quadro responsável por centralizar", resultado)
        self.assertIn("Suporte Técnico - Suporte", resultado)
        self.assertIn("Fluxo para atendimento de suporte técnico", resultado)
        self.assertIn("REGRAS DE TRANSFERÊNCIA:", resultado)

    def test_formatar_fluxos_disponiveis_vazio(self) -> None:
        """Testa formatação com dicionário vazio."""
        resultado = self.datasource._formatar_fluxos_disponiveis({})

        self.assertIn("Nenhum setor disponível", resultado)
        self.assertIn("SETORES DISPONÍVEIS PARA TRANSFERÊNCIA:", resultado)

    def test_formatar_fluxos_disponiveis_none(self) -> None:
        """Testa formatação com None."""
        resultado = self.datasource._formatar_fluxos_disponiveis(None)

        self.assertIn("Nenhum setor disponível", resultado)
        self.assertIn("SETORES DISPONÍVEIS PARA TRANSFERÊNCIA:", resultado)
