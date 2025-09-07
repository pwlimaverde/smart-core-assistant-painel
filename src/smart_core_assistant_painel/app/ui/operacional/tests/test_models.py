"""Testes para os modelos do app Operacional."""

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import (
    AtendenteHumano,
    Departamento,
    validate_api_key,
    validate_telefone_instancia,
)


class TestAtendenteHumano(TestCase):
    """Testes para o modelo AtendenteHumano."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.atendente = AtendenteHumano.objects.create(
            telefone="5511888888888",
            nome="Atendente Teste",
            cargo="Analista",
            email="atendente@teste.com",
        )

    def test_atendente_humano_creation(self) -> None:
        """Testa a criação de um atendente humano."""
        self.assertEqual(self.atendente.nome, "Atendente Teste")
        self.assertEqual(self.atendente.cargo, "Analista")
        self.assertTrue(self.atendente.ativo)
        self.assertTrue(self.atendente.disponivel)
        self.assertEqual(self.atendente.max_atendimentos_simultaneos, 5)

    def test_atendente_str_representation(self) -> None:
        """Testa a representação string do atendente."""
        expected = f"{self.atendente.nome} - {self.atendente.cargo}"
        self.assertEqual(str(self.atendente), expected)


class TestDepartamento(TestCase):
    """Testes para o modelo Departamento."""

    def setUp(self):
        """Configuração inicial."""
        self.departamento = Departamento.objects.create(
            nome="Departamento Teste",
            telefone_instancia="11999999999",
            api_key="chave_teste_12345",
        )

    def test_departamento_creation(self):
        """Testa a criação de um departamento."""
        self.assertEqual(self.departamento.nome, "Departamento Teste")
        self.assertEqual(self.departamento.telefone_instancia, "11999999999")
        self.assertEqual(self.departamento.api_key, "chave_teste_12345")
        self.assertTrue(self.departamento.ativo)

    def test_departamento_str_representation(self):
        """Testa a representação string do departamento."""
        expected = "Departamento Teste (11999999999)"
        self.assertEqual(str(self.departamento), expected)

    def test_departamento_save_normalizes_phone(self):
        """Testa que o save normaliza o telefone."""
        dept = Departamento(
            nome="Teste Normalização",
            telefone_instancia="+55 (11) 99999-9999",
            api_key="chave_normalizar_123",
        )
        dept.save()
        self.assertEqual(dept.telefone_instancia, "5511999999999")

    def test_departamento_clean_validates_api_key(self):
        """Testa que clean valida a API key."""
        dept = Departamento(
            nome="Teste Validação",
            telefone_instancia="11999999999",
            api_key="curta",
        )
        with self.assertRaises(ValidationError):
            dept.clean()

    def test_validar_api_key_method(self):
        """Testa validar_api_key."""
        data = {"apikey": "chave_teste_12345", "instance": "11999999999"}
        result = Departamento.validar_api_key(data)
        self.assertEqual(result, self.departamento)

        data_sem_key = {"instance": "11999999999"}
        with patch("smart_core_assistant_painel.app.ui.operacional.models.logger") as mock_logger:
            result = Departamento.validar_api_key(data_sem_key)
            self.assertIsNone(result)
            mock_logger.warning.assert_called()

        data_sem_instance = {"apikey": "chave_teste_12345"}
        with patch("smart_core_assistant_painel.app.ui.operacional.models.logger") as mock_logger:
            result = Departamento.validar_api_key(data_sem_instance)
            self.assertIsNone(result)
            mock_logger.warning.assert_called()

        data_invalida = {
            "apikey": "chave_inexistente",
            "instance": "11000000000",
        }
        with patch("smart_core_assistant_painel.app.ui.operacional.models.logger") as mock_logger:
            result = Departamento.validar_api_key(data_invalida)
            self.assertIsNone(result)
            mock_logger.warning.assert_called()
