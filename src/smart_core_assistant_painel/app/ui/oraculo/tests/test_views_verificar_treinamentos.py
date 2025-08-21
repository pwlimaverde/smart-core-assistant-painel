"""Testes para a view de verificação de treinamentos vetorizados."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Treinamentos


class TestVerificarTreinamentosView(TestCase):
    """Testes para a view verificar_treinamentos_vetorizados."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Cria treinamentos de teste
        self.treinamento_vetorizado = Treinamentos.objects.create(
            tag="teste_vetorizado",
            grupo="grupo_teste",
            treinamento_finalizado=True,
            treinamento_vetorizado=True,
            _documentos=[{"content": "Documento vetorizado"}]
        )
        
        self.treinamento_erro = Treinamentos.objects.create(
            tag="teste_erro",
            grupo="grupo_teste",
            treinamento_finalizado=True,
            treinamento_vetorizado=False,
            _documentos=[{"content": "Documento com erro"}]
        )
        
        self.url = reverse('oraculo:verificar_treinamentos_vetorizados')

    def test_verificar_treinamentos_get(self):
        """Testa o acesso à página de verificação de treinamentos via GET."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Treinamentos Vetorizados")
        self.assertContains(response, "Treinamentos com Erro")
        
        # Verifica se os treinamentos aparecem na página
        self.assertContains(response, "teste_vetorizado")
        self.assertContains(response, "teste_erro")

    def test_verificar_treinamentos_excluir(self):
        """Testa a exclusão de um treinamento."""
        treinamento_id = self.treinamento_vetorizado.id
        
        response = self.client.post(self.url, {
            'acao': 'excluir',
            'treinamento_id': treinamento_id
        })
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica se o treinamento foi excluído
        with self.assertRaises(Treinamentos.DoesNotExist):
            Treinamentos.objects.get(id=treinamento_id)

    def test_verificar_treinamentos_vetorizar(self):
        """Testa a tentativa de vetorizar novamente um treinamento."""
        treinamento_id = self.treinamento_erro.id
        
        with patch('smart_core_assistant_painel.app.ui.oraculo.views.async_task') as mock_async_task:
            response = self.client.post(self.url, {
                'acao': 'vetorizar',
                'treinamento_id': treinamento_id
            })
            
            # Verifica redirecionamento
            self.assertEqual(response.status_code, 302)
            
            # Verifica se a task assíncrona foi chamada
            mock_async_task.assert_called_once()

    def test_verificar_treinamentos_acao_invalida(self):
        """Testa uma ação inválida."""
        response = self.client.post(self.url, {
            'acao': 'acao_invalida',
            'treinamento_id': self.treinamento_erro.id
        })
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica se a mensagem de erro está na sessão
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ação inválida.")

    def test_verificar_treinamentos_sem_permissao(self):
        """Testa o acesso à página sem permissão."""
        # Desloga o usuário
        self.client.logout()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_verificar_treinamentos_post_sem_acao(self):
        """Testa POST sem especificar ação."""
        response = self.client.post(self.url, {
            'treinamento_id': self.treinamento_erro.id
        })
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica se a mensagem de erro está na sessão
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ação ou ID do treinamento não especificado.")