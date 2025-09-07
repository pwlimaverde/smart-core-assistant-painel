"""Testes para os modelos do app Treinamento."""

from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from langchain.docstore.document import Document

from ..models import Treinamento, validate_identificador


class TestTreinamentos(TestCase):
    """Testes para o modelo Treinamentos."""

    def test_treinamentos_creation(self) -> None:
        """Testa a criação de um treinamento."""
        treinamento = Treinamento.objects.create(
            tag="teste",
            grupo="grupo_teste",
            conteudo="Documento de teste",
        )

        self.assertEqual(treinamento.tag, "teste")
        self.assertEqual(treinamento.grupo, "grupo_teste")
        self.assertFalse(treinamento.treinamento_finalizado)
        self.assertEqual(treinamento.conteudo, "Documento de teste")

    def test_treinamentos_finalizacao(self) -> None:
        """Testa a finalização de um treinamento."""
        treinamento = Treinamento.objects.create(
            tag="teste_finalizado",
            grupo="grupo_teste",
            conteudo="Documento finalizado",
            treinamento_finalizado=True,
        )

        self.assertTrue(treinamento.treinamento_finalizado)


class TestValidators(TestCase):
    """Testes para os validadores dos modelos."""

    def test_validate_identificador(self):
        """Testa o validador de identificador."""
        validate_identificador("tag_valida")
        validate_identificador("tag123")
        validate_identificador("test_tag_123")

        with self.assertRaises(ValidationError):
            validate_identificador("Tag com maiúscula")

        with self.assertRaises(ValidationError):
            validate_identificador("tag com espaço")

        with self.assertRaises(ValidationError):
            validate_identificador("a" * 41)

        with self.assertRaises(ValidationError):
            validate_identificador("tag-com-traço")


class TestTreinamentosAdvanced(TestCase):
    """Testes avançados para o modelo Treinamentos."""

    def setUp(self):
        """Configuração inicial."""
        self.treinamento = Treinamento.objects.create(
            tag="teste_avancado", grupo="grupo_avancado"
        )

    def test_clean_validation_tag_igual_grupo(self):
        """Testa validação que impede tag igual ao grupo."""
        with self.assertRaises(ValidationError):
            treinamento = Treinamento(tag="mesma_tag", grupo="mesma_tag")
            treinamento.full_clean()

    def test_str_representation(self):
        """Testa a representação string do treinamento."""
        self.assertEqual(str(self.treinamento), "teste_avancado")

        treinamento_sem_tag = Treinamento.objects.create(
            tag="tag_temp", grupo="grupo_temp"
        )
        treinamento_sem_tag.tag = None
        result = str(treinamento_sem_tag)
        self.assertTrue(result.startswith("Treinamento"))
