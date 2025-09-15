"""Testes para os modelos do app Treinamento."""

import logging
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from langchain.docstore.document import Document

from smart_core_assistant_painel.app.ui.treinamento.models import (
    QueryCompose,
    Treinamento,
    validate_identificador,
)

# Configurar logging para testes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestTreinamentoTreinamentos(TestCase):
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


class TestTreinamentoValidators(TestCase):
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


class TestTreinamentoTreinamentosAdvanced(TestCase):
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


class TestQueryCompose(TestCase):
    """Testes para o modelo QueryCompose."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.query_compose = QueryCompose.objects.create(
            tag="orcamento",
            grupo="vendas",
            descricao="Solicitação de orçamento para produtos ou serviços",
            exemplo="Preciso de um orçamento para 100 camisetas personalizadas",
            comportamento="Você deve solicitar detalhes específicos sobre o produto e fornecer informações de preço."
        )

    def test_query_compose_creation(self) -> None:
        """Testa a criação de um QueryCompose."""
        self.assertEqual(self.query_compose.tag, "orcamento")
        self.assertEqual(self.query_compose.grupo, "vendas")
        self.assertEqual(self.query_compose.descricao, "Solicitação de orçamento para produtos ou serviços")
        self.assertEqual(self.query_compose.exemplo, "Preciso de um orçamento para 100 camisetas personalizadas")
        self.assertIsNotNone(self.query_compose.created_at)
        self.assertIsNotNone(self.query_compose.updated_at)

    def test_query_compose_str_representation(self) -> None:
        """Testa a representação string do QueryCompose."""
        self.assertEqual(str(self.query_compose), "orcamento")
        
        # Teste com tag vazia
        query_sem_tag = QueryCompose.objects.create(
            tag="",
            grupo="teste",
            descricao="Teste sem tag",
            exemplo="Exemplo teste",
            comportamento="Comportamento teste"
        )
        self.assertEqual(str(query_sem_tag), "sem-tag")



    def test_to_embedding_text(self) -> None:
        """Testa o método to_embedding_text."""
        result = self.query_compose.to_embedding_text()
        
        # Verifica se contém a descrição
        self.assertIn("Solicitação de orçamento para produtos ou serviços", result)
        
        # Verifica se contém o exemplo formatado
        self.assertIn("Exemplo: Preciso de um orçamento para 100 camisetas personalizadas", result)
        
        # Verifica se contém a categoria (tag)
        self.assertIn("Categoria: orcamento", result)
        
        # Verifica a estrutura com quebras de linha
        lines = result.split("\n")
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "Categoria: orcamento")
        self.assertEqual(lines[1], "Solicitação de orçamento para produtos ou serviços")
        self.assertEqual(lines[2], "Exemplo: Preciso de um orçamento para 100 camisetas personalizadas")

    def test_to_embedding_text_campos_vazios(self) -> None:
        """Testa o método to_embedding_text com campos vazios."""
        query_minimo = QueryCompose.objects.create(
            tag="teste",
            grupo="grupo_teste",
            descricao="Apenas descrição",
            exemplo="",
            comportamento="Comportamento teste"
        )
        
        result = query_minimo.to_embedding_text()
        
        # Deve conter apenas descrição e categoria
        self.assertIn("Apenas descrição", result)
        self.assertIn("Categoria: teste", result)
        self.assertNotIn("Exemplo:", result)
        
        lines = result.split("\n")
        self.assertEqual(len(lines), 2)

    def test_to_embedding_text_sem_descricao(self) -> None:
        """Testa o método to_embedding_text sem descrição."""
        query_sem_desc = QueryCompose.objects.create(
            tag="teste",
            grupo="grupo_teste",
            descricao="",
            exemplo="Apenas exemplo",
            comportamento="Comportamento teste"
        )
        
        result = query_sem_desc.to_embedding_text()
        
        # Deve conter exemplo e categoria
        self.assertIn("Exemplo: Apenas exemplo", result)
        self.assertIn("Categoria: teste", result)
        
        lines = result.split("\n")
        self.assertEqual(len(lines), 2)

    def test_to_embedding_text_todos_campos_vazios(self) -> None:
        """Testa o método to_embedding_text com campos de conteúdo vazios."""
        query_vazio = QueryCompose.objects.create(
            tag="",
            grupo="grupo_teste",
            descricao="",
            exemplo="",
            comportamento="Comportamento teste"
        )
        
        result = query_vazio.to_embedding_text()
        
        # Deve retornar string vazia quando não há conteúdo relevante
        self.assertEqual(result, "")

    def test_validate_identificador_query_compose(self) -> None:
        """Testa validação de identificador nos campos tag e grupo do QueryCompose."""
        # Teste com identificador válido
        query_valido = QueryCompose(
            tag="tag_valida",
            grupo="grupo_valido",
            descricao="Teste",
            exemplo="Exemplo",
            comportamento="Comportamento"
        )
        query_valido.full_clean()  # Não deve gerar exceção
        
        # Teste com tag inválida
        with self.assertRaises(ValidationError):
            query_invalido = QueryCompose(
                tag="Tag Inválida",
                grupo="grupo_valido",
                descricao="Teste",
                exemplo="Exemplo",
                comportamento="Comportamento"
            )
            query_invalido.full_clean()
        
        # Teste com grupo inválido
        with self.assertRaises(ValidationError):
            query_invalido = QueryCompose(
                tag="tag_valida",
                grupo="Grupo Inválido",
                descricao="Teste",
                exemplo="Exemplo",
                comportamento="Comportamento"
            )
            query_invalido.full_clean()

    def test_buscar_comportamento_similar_com_threshold(self) -> None:
        """Testa a busca de comportamento similar com threshold interno fixo usando mock do queryset para evitar dependência de pgvector/SQL."""
        from unittest.mock import patch  # import local para evitar alterar imports globais

        # Stub simples que emula a cadeia do QuerySet usado no método
        class _DummyQS:
            def __init__(self, obj: object):
                self._obj = obj

            def annotate(self, *args, **kwargs):
                return self

            def only(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def __getitem__(self, item):
                # O método usa [:top_k] resultando em uma lista e depois acessa [0]
                return [self._obj]

            def __bool__(self) -> bool:
                return True

        # Objetos simulados para os dois cenários
        high_distance_obj = type(
            "Obj",
            (),
            {
                "distance": 0.9,
                "tag": "teste_threshold_unico",
                "descricao": "",
                "comportamento": "Você deve responder sobre testes únicos",
            },
        )()

        low_distance_obj = type(
            "Obj",
            (),
            {
                "distance": 0.05,
                "tag": "teste_threshold_unico",
                "descricao": "",
                "comportamento": "Você deve responder sobre testes únicos",
            },
        )()

        # Patch da chamada objects.filter para retornar os stubs em sequência (primeira chamada: distância alta -> None; segunda: baixa -> retorno válido)
        with patch.object(
            QueryCompose.objects, "filter", side_effect=[_DummyQS(high_distance_obj), _DummyQS(low_distance_obj)]
        ):
            # Cenário 1: vetor muito diferente (simulado por distância alta) -> None
            result_high = QueryCompose.buscar_comportamento_similar(
                query_vec=[0.0] + [1.0] * 1023
            )
            self.assertIsNone(result_high)

            # Cenário 2: vetor idêntico (simulado por distância baixa) -> retorna prompt com comportamento
            result_low = QueryCompose.buscar_comportamento_similar(
                query_vec=[0.5, 0.5] + [0.0] * 1022
            )
            self.assertIsNotNone(result_low)
            assert result_low is not None
            self.assertIn("📚 Comportamento que deve ser seguido:", result_low)
            self.assertIn("Você deve responder sobre testes únicos", result_low)
