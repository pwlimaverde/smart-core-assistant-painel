"""Testes para verificar o tratamento de erros nas views do oráculo."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from rolepermissions.roles import assign_role
from unittest.mock import patch
from smart_core_assistant_painel.app.ui.oraculo.models import Treinamentos


class TestViewsErrorHandling(TestCase):
    """Testes para verificar o tratamento de erros nas views."""

    def setUp(self) -> None:
        """Configuração inicial dos testes."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Atribui a role de gerente para ter permissão treinar_ia
        assign_role(self.user, 'gerente')
        self.client.login(username='testuser', password='testpass123')

    def test_processar_pre_processamento_treinamento_inexistente(self) -> None:
        """Testa se o erro DoesNotExist é tratado corretamente."""
        # ID que não existe no banco
        inexistent_id = 99999
        
        # Faz uma requisição POST para o endpoint
        response = self.client.post(
            reverse('oraculo:pre_processamento', args=[inexistent_id]),
            data={'acao': 'aceitar'}
        )
        
        # Verifica se houve redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica se a mensagem de erro foi adicionada
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(
            'não foi encontrado' in str(message) 
            for message in messages
        ))
        
        # Verifica se redirecionou para a página correta
        self.assertRedirects(response, reverse('oraculo:treinar_ia'))

    def test_exibir_pre_processamento_treinamento_inexistente(self) -> None:
        """Testa se o erro DoesNotExist é tratado na exibição."""
        # ID que não existe no banco
        inexistent_id = 99999
        
        # Faz uma requisição GET para o endpoint
        response = self.client.get(
            reverse('oraculo:pre_processamento', args=[inexistent_id])
        )
        
        # Verifica se houve redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica se a mensagem de erro foi adicionada
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(
            'não foi encontrado' in str(message) 
            for message in messages
        ))
        
        # Verifica se redirecionou para a página correta
        self.assertRedirects(response, reverse('oraculo:treinar_ia'))

    @patch('smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose.melhoria_ia_treinamento')
    def test_processar_pre_processamento_com_treinamento_valido(self, mock_melhoria) -> None:
        """Testa o processamento de pré-processamento com treinamento válido."""
        # Mock do método que pode estar causando problemas
        mock_melhoria.return_value = "Texto melhorado de teste"
        
        # Criar um treinamento válido com documentos
        treinamento = Treinamentos.objects.create(
            tag="teste_valido",
            grupo="grupo_valido",
            _documentos=[{"page_content": "Conteúdo de teste", "metadata": {}}]
        )
        
        # Fazer uma requisição GET para a página de pré-processamento
        response = self.client.get(reverse("oraculo:pre_processamento", args=[treinamento.id]))
        
        # Verificar se a resposta é bem-sucedida
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sugestão de Melhoria")
        self.assertContains(response, "Texto melhorado de teste")
        
        # Verificar se o mock foi chamado
        mock_melhoria.assert_called_once()