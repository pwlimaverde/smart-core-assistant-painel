"""Testes para verificar o tratamento de erros nas views do oráculo."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from rolepermissions.roles import assign_role
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
        # Atribui a função de Gerente para ter a permissão "treinar_ia"
        assign_role(self.user, 'gerente')
        self.client.login(username='testuser', password='testpass123')

    def test_processar_pre_processamento_treinamento_inexistente(self) -> None:
        """Testa se o erro DoesNotExist é tratado corretamente."""
        # ID que não existe no banco
        inexistent_id = 99999
        
        # Faz uma requisição POST para o endpoint
        response = self.client.post(
            reverse('oraculo:pre_processamento', args=[inexistent_id]),
            data={'acao': 'process'}  # Corrigido de 'action' para 'acao'
        )
        
        # Verifica se houve redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verifica se a mensagem de erro foi adicionada
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(
            'não encontrado' in str(message) 
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
            'não encontrado' in str(message) 
            for message in messages
        ))
        
        # Verifica se redirecionou para a página correta
        self.assertRedirects(response, reverse('oraculo:treinar_ia'))

    def test_processar_pre_processamento_com_treinamento_valido(self) -> None:
        """Testa o comportamento normal com treinamento válido."""
        # Cria um treinamento válido
        treinamento = Treinamentos.objects.create(
            tag='teste_tag',
            grupo='teste_grupo'
        )
        
        # Faz uma requisição GET para verificar se não há erro
        response = self.client.get(
            reverse('oraculo:pre_processamento', args=[treinamento.id])
        )
        
        # Verifica se a página carregou normalmente (200 ou 302 dependendo da lógica)
        self.assertIn(response.status_code, [200, 302])
        
        # Se houve redirecionamento, não deve ser para a página de erro
        if response.status_code == 302:
            self.assertNotEqual(
                response.url, 
                reverse('oraculo:treinar_ia')
            )