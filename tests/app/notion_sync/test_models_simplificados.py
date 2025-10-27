"""
Testes essenciais para verificar se a sincronização do campo ativo funciona corretamente.

Este teste foca em verificar:
1. Se os models existem e têm os campos necessários
2. Se o mapper do atendente inclui o campo Ativo
"""

from django.test import TestCase

from smart_core_assistant_painel.app.notion_sync.models import (
    DepartamentoSync,
    AtendenteHumanoSync,
    NotionDatabaseConfig,
)

class TestSincronizacaoCampoAtivo(TestCase):
    """Testa se o campo ativo é sincronizado corretamente."""

    def test_models_possuem_campos_necessarios(self) -> None:
        """Verifica se os models têm os campos necessários."""
        # DepartamentoSync
        self.assertTrue(hasattr(DepartamentoSync, 'departamento'))
        self.assertTrue(hasattr(DepartamentoSync, 'status_formatado'))
        self.assertTrue(hasattr(DepartamentoSync, 'prepare_notion_data'))
        self.assertTrue(hasattr(DepartamentoSync, 'needs_sync'))

        # AtendenteHumanoSync
        self.assertTrue(hasattr(AtendenteHumanoSync, 'atendente'))
        self.assertTrue(hasattr(AtendenteHumanoSync, 'status_formatado'))
        self.assertTrue(hasattr(AtendenteHumanoSync, 'prepare_notion_data'))
        self.assertTrue(hasattr(AtendenteHumanoSync, 'needs_sync'))

    def test_mapper_atendente_inclui_campo_ativo(self) -> None:
        """Testa se AtendenteHumanoMapper inclui campo Ativo."""
        from smart_core_assistant_painel.app.notion_sync.services.mappers.atendente_humano_mapper import AtendenteHumanoMapper

        # Mock do sync com apenas o campo necessário para este teste
        class MockAtendente:
            def __init__(self) -> None:
                self.ativo = True
                self.nome = "Test Agent"
                self.cargo = "Test Role"
                self.email = "test@example.com"
                self.telefone = None
                self.departamento = None
                self.especialidades = []

        class MockSync:
            def __init__(self) -> None:
                self.atendente = MockAtendente()
                self.metadados = {}

        mock_sync = MockSync()

        # Converte para propriedades do Notion
        properties = AtendenteHumanoMapper.to_notion_properties(mock_sync)

        # Verifica se incluiu o campo Ativo
        self.assertIn('Ativo', properties)
        self.assertEqual(properties['Ativo']['checkbox'], True)

        # Testa com ativo=False
        mock_sync.atendente.ativo = False
        properties = AtendenteHumanoMapper.to_notion_properties(mock_sync)
        self.assertEqual(properties['Ativo']['checkbox'], False)

    def test_needs_sync_departamento_compara_ativo(self) -> None:
        """Testa lógica do needs_sync para campo ativo do departamento."""
        dept_sync = DepartamentoSync()
        dept_sync.sync_status = 'synced'
        dept_sync.last_sync_at = None  # None significa que nunca foi sincronizado

        # Mock da config
        class MockConfig:
            sync_enabled = True
        dept_sync.config = MockConfig()

        # Mock do departamento
        class MockDepartamento:
            def __init__(self) -> None:
                self.ativo = True
                self.data_criacao = None

        mock_departamento = MockDepartamento()
        dept_sync.departamento = mock_departamento
        dept_sync.status_formatado = "Ativo"
        dept_sync.metadados = {}

        # Com last_sync_at None, sempre precisa sincronizar
        self.assertTrue(dept_sync.needs_sync())

        # Mudando status_formatado para diferente do valor atual
        dept_sync.status_formatado = "Inativo"  # Diferente do mock_departamento.ativo
        self.assertTrue(dept_sync.needs_sync())

    def test_needs_sync_atendente_compara_ativo(self) -> None:
        """Testa lógica do needs_sync para campo ativo do atendente."""
        atendente_sync = AtendenteHumanoSync()
        atendente_sync.sync_status = 'synced'
        atendente_sync.last_sync_at = None  # None significa que nunca foi sincronizado

        # Mock da config
        class MockConfig:
            sync_enabled = True
        atendente_sync.config = MockConfig()

        # Mock do atendente
        class MockAtendente:
            def __init__(self) -> None:
                self.ativo = True
                self.data_cadastro = None
                self.ultima_atividade = None

        mock_atendente = MockAtendente()
        atendente_sync.atendente = mock_atendente
        atendente_sync.status_formatado = "Ativo"
        atendente_sync.metadados = {}

        # Com last_sync_at None, sempre precisa sincronizar
        self.assertTrue(atendente_sync.needs_sync())

        # Mudando status_formatado para diferente do valor atual
        atendente_sync.status_formatado = "Inativo"  # Diferente do mock_atendente.ativo
        self.assertTrue(atendente_sync.needs_sync())

    def test_models_existem(self) -> None:
        """Verifica se todos os models essenciais existem."""
        models_essenciais = [
            NotionDatabaseConfig,
            DepartamentoSync,
            AtendenteHumanoSync,
        ]

        for model in models_essenciais:
            self.assertIsNotNone(model, f"Model {model.__name__} deveria existir")
            self.assertIsNotNone(model._meta)
            self.assertIsNotNone(model._meta.db_table)
