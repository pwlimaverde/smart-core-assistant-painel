"""Tests for the Treinamento app views."""

from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile

from smart_core_assistant_painel.app.ui.treinamento.models import Treinamento, Documento
from smart_core_assistant_painel.app.ui.treinamento.services import TreinamentoService


class TestTreinamentoViews(TestCase):
    """Tests for the Treinamento app views."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_get_initial(self, mock_has_permission: MagicMock) -> None:
        """Test treinar_ia view GET request with no session data."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.get(reverse('treinamento:treinar_ia'))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'treinamento/treinar_ia.html')
        self.assertFalse(response.context['modo_edicao'])
        self.assertIsNone(response.context['treinamento_id'])

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_get_with_session_data(self, mock_has_permission: MagicMock) -> None:
        """Test treinar_ia view GET request with session data."""
        # Arrange
        mock_has_permission.return_value = True
        session = self.client.session
        session['treinamento_edicao'] = {
            'id': 1,
            'tag': 'test_tag',
            'grupo': 'test_grupo',
            'conteudo': 'test_conteudo'
        }
        session.save()
    
        # Act
        response = self.client.get(reverse('treinamento:treinar_ia'))
    
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'treinamento/treinar_ia.html')
        self.assertTrue(response.context['modo_edicao'])
        self.assertEqual(response.context['treinamento_id'], 1)
        self.assertEqual(response.context['tag_inicial'], 'test_tag')

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_no_permission(self, mock_has_permission: MagicMock) -> None:
        """Test treinar_ia view when user has no permission."""
        # Arrange
        mock_has_permission.return_value = False

        # Act
        response = self.client.get(reverse('treinamento:treinar_ia'))

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Você não tem permissão para acessar esta página.")

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_post_missing_tag_and_group(self, mock_has_permission: MagicMock) -> None:
        """Test treinar_ia POST with missing tag and group."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:treinar_ia'), {
            'conteudo': 'test content'
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'treinamento/treinar_ia.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Tag e Grupo são obrigatórios" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_post_missing_content_and_document(self, mock_has_permission: MagicMock) -> None:
        """Test treinar_ia POST with missing content and document."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:treinar_ia'), {
            'tag': 'test_tag',
            'grupo': 'test_grupo'
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'treinamento/treinar_ia.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("É necessário fornecer conteúdo ou documento" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.TreinamentoService')
    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_post_success_with_content(self, mock_has_permission: MagicMock, mock_treinamento_service: MagicMock) -> None:
        """Test treinar_ia POST success with content."""
        # Arrange
        mock_has_permission.return_value = True
        mock_treinamento_service.processar_arquivo_upload.return_value = None
        mock_treinamento_service.limpar_arquivo_temporario.return_value = None

        # Act
        response = self.client.post(reverse('treinamento:treinar_ia'), {
            'tag': 'test_tag',
            'grupo': 'test_grupo',
            'conteudo': 'test content'
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(Treinamento.objects.count(), 1)
        treinamento = Treinamento.objects.first()
        self.assertEqual(treinamento.tag, 'test_tag')
        self.assertEqual(treinamento.grupo, 'test_grupo')
        self.assertEqual(treinamento.conteudo, 'test content')

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.TreinamentoService')
    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_post_success_with_document(self, mock_has_permission: MagicMock, mock_treinamento_service: MagicMock) -> None:
        """Test treinar_ia POST success with document."""
        # Arrange
        mock_has_permission.return_value = True
        mock_document = MagicMock()
        mock_document.page_content = "Document content"
        mock_treinamento_service.processar_arquivo_upload.return_value = "/tmp/test.txt"
        mock_treinamento_service.processar_arquivo_documento.return_value = [mock_document]
        mock_treinamento_service.limpar_arquivo_temporario.return_value = None

        # Create a simple text file
        test_file = SimpleUploadedFile(
            "test.txt",
            b"test document content",
            content_type="text/plain"
        )

        # Act
        response = self.client.post(reverse('treinamento:treinar_ia'), {
            'tag': 'test_tag',
            'grupo': 'test_grupo',
            'documento': test_file
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        # Verify that the service methods were called
        mock_treinamento_service.processar_arquivo_upload.assert_called_once()
        mock_treinamento_service.processar_arquivo_documento.assert_called_once()

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.TreinamentoService')
    @patch('smart_core_assistant_painel.app.ui.treinamento.views.transaction')
    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_treinar_ia_post_exception_handling(self, mock_has_permission: MagicMock, mock_transaction: MagicMock, mock_treinamento_service: MagicMock) -> None:
        """Test treinar_ia POST exception handling."""
        # Arrange
        mock_has_permission.return_value = True
        mock_transaction.atomic.side_effect = Exception("Test exception")
        mock_treinamento_service.limpar_arquivo_temporario.return_value = None

        # Act
        response = self.client.post(reverse('treinamento:treinar_ia'), {
            'tag': 'test_tag',
            'grupo': 'test_grupo',
            'conteudo': 'test content'
        })

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'treinamento/treinar_ia.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Erro interno do servidor" in str(m) for m in messages))


class TestPreProcessamentoViews(TestCase):
    """Tests for the pre_processamento view."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.treinamento = Treinamento.objects.create(
            tag='test_tag',
            grupo='test_grupo',
            conteudo='test content'
        )

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_no_permission(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento view when user has no permission."""
        # Arrange
        mock_has_permission.return_value = False

        # Act
        response = self.client.get(reverse('treinamento:pre_processamento', args=[self.treinamento.id]))

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Você não tem permissão para acessar esta página.")

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_get_success(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento GET request success."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        with patch('smart_core_assistant_painel.app.ui.treinamento.views.FeaturesCompose.melhoria_ia_treinamento') as mock_melhoria:
            mock_melhoria.return_value = "improved content"
            response = self.client.get(reverse('treinamento:pre_processamento', args=[self.treinamento.id]))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'treinamento/pre_processamento.html')
        self.assertEqual(response.context['treinamento'], self.treinamento)

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_get_nonexistent_training(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento GET with nonexistent training."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.get(reverse('treinamento:pre_processamento', args=[999]))

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Treinamento não encontrado" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_get_empty_content(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento GET with empty content."""
        # Arrange
        mock_has_permission.return_value = True
        self.treinamento.conteudo = ""
        self.treinamento.save()

        # Act
        response = self.client.get(reverse('treinamento:pre_processamento', args=[self.treinamento.id]))

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Treinamento sem conteúdo" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_post_accept_action(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento POST with 'accept' action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        with patch('smart_core_assistant_painel.app.ui.treinamento.views.FeaturesCompose.melhoria_ia_treinamento') as mock_melhoria:
            mock_melhoria.return_value = "improved content"
            response = self.client.post(reverse('treinamento:pre_processamento', args=[self.treinamento.id]), {
                'acao': 'aceitar'
            })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        self.treinamento.refresh_from_db()
        self.assertTrue(self.treinamento.treinamento_finalizado)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Treinamento aceito e finalizado" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_post_keep_action(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento POST with 'keep' action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:pre_processamento', args=[self.treinamento.id]), {
            'acao': 'manter'
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        self.treinamento.refresh_from_db()
        self.assertTrue(self.treinamento.treinamento_finalizado)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Treinamento mantido e finalizado" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_post_discard_action(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento POST with 'discard' action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:pre_processamento', args=[self.treinamento.id]), {
            'acao': 'descartar'
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(Treinamento.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Treinamento descartado" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_post_invalid_action(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento POST with invalid action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:pre_processamento', args=[self.treinamento.id]), {
            'acao': 'invalid_action'
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Ação inválida" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_pre_processamento_post_missing_action(self, mock_has_permission: MagicMock) -> None:
        """Test pre_processamento POST with missing action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:pre_processamento', args=[self.treinamento.id]), {})

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Ação não especificada" in str(m) for m in messages))


class TestVerificarTreinamentosViews(TestCase):
    """Tests for the verificar_treinamentos_vetorizados view."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Evita execução dos tasks do django-q nos signals (mantém flags conforme criadas)
        self.async_task_patcher = patch(
            'smart_core_assistant_painel.app.ui.treinamento.signals.async_task',
            return_value=None
        )
        self.mock_async_task = self.async_task_patcher.start()
        
        # Create test trainings
        self.treinamento_vetorizado = Treinamento.objects.create(
            tag='test_tag1',
            grupo='test_grupo1',
            conteudo='test content 1',
            treinamento_finalizado=True,
            treinamento_vetorizado=True
        )
        
        self.treinamento_com_erro = Treinamento.objects.create(
            tag='test_tag2',
            grupo='test_grupo2',
            conteudo='test content 2',
            treinamento_finalizado=True,
            treinamento_vetorizado=False
        )

    def tearDown(self) -> None:
        """Tear down mocks started in setUp."""
        try:
            self.async_task_patcher.stop()
        except Exception:
            pass

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_verificar_treinamentos_no_permission(self, mock_has_permission: MagicMock) -> None:
        """Test verificar_treinamentos when user has no permission."""
        # Arrange
        mock_has_permission.return_value = False

        # Act
        response = self.client.get(reverse('treinamento:verificar_treinamentos_vetorizados'))

        # Assert
        self.assertEqual(response.status_code, 404)

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_verificar_treinamentos_get_success(self, mock_has_permission: MagicMock) -> None:
        """Test verificar_treinamentos GET request success."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.get(reverse('treinamento:verificar_treinamentos_vetorizados'))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'treinamento/verificar_treinamentos.html')
        self.assertIn(self.treinamento_vetorizado, response.context['treinamentos_vetorizados'])
        self.assertIn(self.treinamento_com_erro, response.context['treinamentos_com_erro'])

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_verificar_treinamentos_post_delete_action(self, mock_has_permission: MagicMock) -> None:
        """Test verificar_treinamentos POST with 'delete' action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:verificar_treinamentos_vetorizados'), {
            'acao': 'excluir',
            'treinamento_id': self.treinamento_vetorizado.id
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(Treinamento.objects.count(), 1)  # One should be deleted
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Treinamento excluído com sucesso" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_verificar_treinamentos_post_edit_action(self, mock_has_permission: MagicMock) -> None:
        """Test verificar_treinamentos POST with 'edit' action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:verificar_treinamentos_vetorizados'), {
            'acao': 'editar',
            'treinamento_id': self.treinamento_vetorizado.id
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        session = self.client.session
        self.assertIn('treinamento_edicao', session)
        self.assertEqual(session['treinamento_edicao']['id'], self.treinamento_vetorizado.id)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Editando treinamento ID" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_verificar_treinamentos_post_invalid_action(self, mock_has_permission: MagicMock) -> None:
        """Test verificar_treinamentos POST with invalid action."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:verificar_treinamentos_vetorizados'), {
            'acao': 'invalid_action',
            'treinamento_id': self.treinamento_vetorizado.id
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Ação inválida" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_verificar_treinamentos_post_missing_action_or_id(self, mock_has_permission: MagicMock) -> None:
        """Test verificar_treinamentos POST with missing action or ID."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:verificar_treinamentos_vetorizados'), {
            'acao': 'excluir'
            # Missing treinamento_id
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Ação ou ID do treinamento não especificado" in str(m) for m in messages))

    @patch('smart_core_assistant_painel.app.ui.treinamento.views.has_permission')
    def test_verificar_treinamentos_post_nonexistent_training(self, mock_has_permission: MagicMock) -> None:
        """Test verificar_treinamentos POST with nonexistent training."""
        # Arrange
        mock_has_permission.return_value = True
        # Act
        response = self.client.post(reverse('treinamento:verificar_treinamentos_vetorizados'), {
            'acao': 'excluir',
            'treinamento_id': 999
        })

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Treinamento não encontrado" in str(m) for m in messages))