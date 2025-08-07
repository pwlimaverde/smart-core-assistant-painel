"""Testes para as views do app Oraculo."""

import json
from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from ..models import (
    Atendimento,
    Contato,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)
from ..views import nova_mensagem, webhook_whatsapp


class TestWebhookWhatsApp(TestCase):
    """Testes para a view webhook_whatsapp."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.client = Client()
        self.webhook_url = reverse('oraculo:webhook_whatsapp')
        
        # Dados de exemplo do WhatsApp
        self.whatsapp_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "id": "wamid.test123",
                            "from": "5511999999999",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {
                                "body": "Olá, preciso de ajuda"
                            }
                        }],
                        "contacts": [{
                            "profile": {
                                "name": "Cliente Teste"
                            },
                            "wa_id": "5511999999999"
                        }]
                    }
                }]
            }]
        }

    def test_webhook_get_verification(self) -> None:
        """Testa a verificação do webhook via GET."""
        # Simula verificação do Facebook
        response = self.client.get(self.webhook_url, {
            'hub.mode': 'subscribe',
            'hub.challenge': 'test_challenge',
            'hub.verify_token': 'your_verify_token'
        })
        
        # Deve retornar o challenge se o token estiver correto
        # (assumindo que a view implementa essa verificação)
        self.assertEqual(response.status_code, 200)

    @patch('smart_core_assistant_painel.app.ui.oraculo.views.nova_mensagem')
    def test_webhook_post_nova_mensagem(self, mock_nova_mensagem: Mock) -> None:
        """Testa o processamento de nova mensagem via POST."""
        mock_nova_mensagem.return_value = None
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(self.whatsapp_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        mock_nova_mensagem.assert_called_once()

    def test_webhook_post_dados_invalidos(self) -> None:
        """Testa o webhook com dados inválidos."""
        dados_invalidos = {"invalid": "data"}
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(dados_invalidos),
            content_type='application/json'
        )
        
        # Deve retornar 200 mesmo com dados inválidos (padrão WhatsApp)
        self.assertEqual(response.status_code, 200)

    def test_webhook_post_sem_mensagens(self) -> None:
        """Testa o webhook sem mensagens no payload."""
        dados_sem_mensagens = {
            "entry": [{
                "changes": [{
                    "value": {
                        "contacts": [{
                            "profile": {"name": "Cliente Teste"},
                            "wa_id": "5511999999999"
                        }]
                    }
                }]
            }]
        }
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(dados_sem_mensagens),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)

    def test_webhook_post_multiplas_mensagens(self) -> None:
        """Testa o webhook com múltiplas mensagens."""
        dados_multiplas = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [
                            {
                                "id": "wamid.test123",
                                "from": "5511999999999",
                                "timestamp": "1234567890",
                                "type": "text",
                                "text": {"body": "Primeira mensagem"}
                            },
                            {
                                "id": "wamid.test456",
                                "from": "5511999999999",
                                "timestamp": "1234567891",
                                "type": "text",
                                "text": {"body": "Segunda mensagem"}
                            }
                        ],
                        "contacts": [{
                            "profile": {"name": "Cliente Teste"},
                            "wa_id": "5511999999999"
                        }]
                    }
                }]
            }]
        }
        
        with patch('smart_core_assistant_painel.app.ui.oraculo.views.nova_mensagem') as mock_nova_mensagem:
            response = self.client.post(
                self.webhook_url,
                data=json.dumps(dados_multiplas),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            # Deve processar ambas as mensagens
            self.assertEqual(mock_nova_mensagem.call_count, 2)


class TestNovaMensagem(TestCase):
    """Testes para a função nova_mensagem."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999",
            nome="Cliente Teste"
        )
        
        self.atendimento = Atendimento.objects.create(
            contato=self.contato,
            status=StatusAtendimento.ATIVO
        )
        
        # Dados de mensagem de exemplo
        self.dados_mensagem = {
            "id": "wamid.test123",
            "from": "5511999999999",
            "timestamp": "1234567890",
            "type": "text",
            "text": {
                "body": "Olá, preciso de ajuda"
            }
        }
        
        self.dados_contato = {
            "profile": {
                "name": "Cliente Teste"
            },
            "wa_id": "5511999999999"
        }

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    @patch('smart_core_assistant_painel.modules.ai.processar_mensagem_ai')
    def test_nova_mensagem_contato_existente(self, mock_ai: Mock, mock_whatsapp: Mock) -> None:
        """Testa o processamento de nova mensagem de contato existente."""
        mock_ai.return_value = "Resposta do bot"
        mock_whatsapp.return_value = True
        
        nova_mensagem(self.dados_mensagem, self.dados_contato)
        
        # Verifica se a mensagem foi salva
        mensagem = Mensagem.objects.filter(
            message_id_whatsapp="wamid.test123"
        ).first()
        
        self.assertIsNotNone(mensagem)
        self.assertEqual(mensagem.conteudo, "Olá, preciso de ajuda")
        self.assertEqual(mensagem.remetente, TipoRemetente.CONTATO)
        self.assertEqual(mensagem.atendimento, self.atendimento)
        
        # Verifica se o AI foi chamado
        mock_ai.assert_called_once()
        
        # Verifica se a resposta foi enviada
        mock_whatsapp.assert_called_once()

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    @patch('smart_core_assistant_painel.modules.ai.processar_mensagem_ai')
    def test_nova_mensagem_contato_novo(self, mock_ai: Mock, mock_whatsapp: Mock) -> None:
        """Testa o processamento de nova mensagem de contato novo."""
        mock_ai.return_value = "Bem-vindo!"
        mock_whatsapp.return_value = True
        
        dados_novo_contato = {
            "profile": {"name": "Novo Cliente"},
            "wa_id": "5511888888888"
        }
        
        dados_nova_mensagem = {
            "id": "wamid.novo123",
            "from": "5511888888888",
            "timestamp": "1234567890",
            "type": "text",
            "text": {"body": "Primeira mensagem"}
        }
        
        nova_mensagem(dados_nova_mensagem, dados_novo_contato)
        
        # Verifica se o novo contato foi criado
        novo_contato = Contato.objects.filter(
            telefone="5511888888888"
        ).first()
        
        self.assertIsNotNone(novo_contato)
        self.assertEqual(novo_contato.nome, "Novo Cliente")
        
        # Verifica se o novo atendimento foi criado
        novo_atendimento = Atendimento.objects.filter(
            contato=novo_contato,
            status=StatusAtendimento.ATIVO
        ).first()
        
        self.assertIsNotNone(novo_atendimento)
        
        # Verifica se a mensagem foi salva
        mensagem = Mensagem.objects.filter(
            message_id_whatsapp="wamid.novo123"
        ).first()
        
        self.assertIsNotNone(mensagem)
        self.assertEqual(mensagem.atendimento, novo_atendimento)

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    def test_nova_mensagem_tipo_imagem(self, mock_whatsapp: Mock) -> None:
        """Testa o processamento de mensagem do tipo imagem."""
        mock_whatsapp.return_value = True
        
        dados_imagem = {
            "id": "wamid.img123",
            "from": "5511999999999",
            "timestamp": "1234567890",
            "type": "image",
            "image": {
                "id": "image_id_123",
                "mime_type": "image/jpeg",
                "caption": "Foto do problema"
            }
        }
        
        nova_mensagem(dados_imagem, self.dados_contato)
        
        # Verifica se a mensagem foi salva com tipo correto
        mensagem = Mensagem.objects.filter(
            message_id_whatsapp="wamid.img123"
        ).first()
        
        self.assertIsNotNone(mensagem)
        self.assertEqual(mensagem.tipo, TipoMensagem.IMAGEM)
        self.assertIn("image_id_123", mensagem.conteudo)

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    def test_nova_mensagem_tipo_audio(self, mock_whatsapp: Mock) -> None:
        """Testa o processamento de mensagem do tipo áudio."""
        mock_whatsapp.return_value = True
        
        dados_audio = {
            "id": "wamid.audio123",
            "from": "5511999999999",
            "timestamp": "1234567890",
            "type": "audio",
            "audio": {
                "id": "audio_id_123",
                "mime_type": "audio/ogg"
            }
        }
        
        nova_mensagem(dados_audio, self.dados_contato)
        
        # Verifica se a mensagem foi salva com tipo correto
        mensagem = Mensagem.objects.filter(
            message_id_whatsapp="wamid.audio123"
        ).first()
        
        self.assertIsNotNone(mensagem)
        self.assertEqual(mensagem.tipo, TipoMensagem.AUDIO)
        self.assertIn("audio_id_123", mensagem.conteudo)

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    def test_nova_mensagem_tipo_documento(self, mock_whatsapp: Mock) -> None:
        """Testa o processamento de mensagem do tipo documento."""
        mock_whatsapp.return_value = True
        
        dados_documento = {
            "id": "wamid.doc123",
            "from": "5511999999999",
            "timestamp": "1234567890",
            "type": "document",
            "document": {
                "id": "doc_id_123",
                "filename": "documento.pdf",
                "mime_type": "application/pdf"
            }
        }
        
        nova_mensagem(dados_documento, self.dados_contato)
        
        # Verifica se a mensagem foi salva com tipo correto
        mensagem = Mensagem.objects.filter(
            message_id_whatsapp="wamid.doc123"
        ).first()
        
        self.assertIsNotNone(mensagem)
        self.assertEqual(mensagem.tipo, TipoMensagem.DOCUMENTO)
        self.assertIn("doc_id_123", mensagem.conteudo)
        self.assertIn("documento.pdf", mensagem.conteudo)

    def test_nova_mensagem_duplicada(self) -> None:
        """Testa o tratamento de mensagem duplicada."""
        # Cria uma mensagem existente
        Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Mensagem original",
            message_id_whatsapp="wamid.test123"
        )
        
        # Tenta processar a mesma mensagem novamente
        with patch('smart_core_assistant_painel.modules.ai.processar_mensagem_ai') as mock_ai:
            nova_mensagem(self.dados_mensagem, self.dados_contato)
            
            # O AI não deve ser chamado para mensagem duplicada
            mock_ai.assert_not_called()
        
        # Deve existir apenas uma mensagem com esse ID
        count = Mensagem.objects.filter(
            message_id_whatsapp="wamid.test123"
        ).count()
        
        self.assertEqual(count, 1)

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    @patch('smart_core_assistant_painel.modules.ai.processar_mensagem_ai')
    def test_nova_mensagem_erro_ai(self, mock_ai: Mock, mock_whatsapp: Mock) -> None:
        """Testa o tratamento de erro no processamento de AI."""
        mock_ai.side_effect = Exception("Erro no AI")
        mock_whatsapp.return_value = True
        
        # Não deve gerar exceção
        nova_mensagem(self.dados_mensagem, self.dados_contato)
        
        # A mensagem do usuário deve ser salva mesmo com erro no AI
        mensagem = Mensagem.objects.filter(
            message_id_whatsapp="wamid.test123"
        ).first()
        
        self.assertIsNotNone(mensagem)
        self.assertEqual(mensagem.conteudo, "Olá, preciso de ajuda")

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    @patch('smart_core_assistant_painel.modules.ai.processar_mensagem_ai')
    def test_nova_mensagem_erro_whatsapp(self, mock_ai: Mock, mock_whatsapp: Mock) -> None:
        """Testa o tratamento de erro no envio via WhatsApp."""
        mock_ai.return_value = "Resposta do bot"
        mock_whatsapp.side_effect = Exception("Erro no WhatsApp")
        
        # Não deve gerar exceção
        nova_mensagem(self.dados_mensagem, self.dados_contato)
        
        # A mensagem do usuário deve ser salva
        mensagem_usuario = Mensagem.objects.filter(
            message_id_whatsapp="wamid.test123"
        ).first()
        
        self.assertIsNotNone(mensagem_usuario)
        
        # A resposta do bot deve ser salva mesmo com erro no envio
        mensagem_bot = Mensagem.objects.filter(
            remetente=TipoRemetente.BOT,
            atendimento=self.atendimento
        ).first()
        
        self.assertIsNotNone(mensagem_bot)
        self.assertEqual(mensagem_bot.conteudo, "Resposta do bot")


class TestViewsIntegration(TestCase):
    """Testes de integração para as views."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.client = Client()
        self.webhook_url = reverse('oraculo:webhook_whatsapp')

    @patch('smart_core_assistant_painel.modules.whatsapp.enviar_mensagem_whatsapp')
    @patch('smart_core_assistant_painel.modules.ai.processar_mensagem_ai')
    def test_fluxo_completo_nova_conversa(self, mock_ai: Mock, mock_whatsapp: Mock) -> None:
        """Testa o fluxo completo de uma nova conversa."""
        mock_ai.return_value = "Olá! Como posso ajudá-lo?"
        mock_whatsapp.return_value = True
        
        dados_webhook = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "id": "wamid.integration123",
                            "from": "5511777777777",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {"body": "Olá, preciso de suporte"}
                        }],
                        "contacts": [{
                            "profile": {"name": "Cliente Integração"},
                            "wa_id": "5511777777777"
                        }]
                    }
                }]
            }]
        }
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(dados_webhook),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica se o contato foi criado
        contato = Contato.objects.filter(
            telefone="5511777777777"
        ).first()
        
        self.assertIsNotNone(contato)
        self.assertEqual(contato.nome, "Cliente Integração")
        
        # Verifica se o atendimento foi criado
        atendimento = Atendimento.objects.filter(
            contato=contato,
            status=StatusAtendimento.ATIVO
        ).first()
        
        self.assertIsNotNone(atendimento)
        
        # Verifica se as mensagens foram criadas
        mensagens = Mensagem.objects.filter(atendimento=atendimento)
        self.assertEqual(mensagens.count(), 2)  # Usuário + Bot
        
        mensagem_usuario = mensagens.filter(
            remetente=TipoRemetente.CONTATO
        ).first()
        
        mensagem_bot = mensagens.filter(
            remetente=TipoRemetente.BOT
        ).first()
        
        self.assertEqual(mensagem_usuario.conteudo, "Olá, preciso de suporte")
        self.assertEqual(mensagem_bot.conteudo, "Olá! Como posso ajudá-lo?")
        
        # Verifica se o AI e WhatsApp foram chamados
        mock_ai.assert_called_once()
        mock_whatsapp.assert_called_once()

    def test_webhook_csrf_exempt(self) -> None:
        """Testa se o webhook está isento de CSRF."""
        # O webhook deve aceitar POST sem token CSRF
        response = self.client.post(
            self.webhook_url,
            data=json.dumps({"test": "data"}),
            content_type='application/json'
        )
        
        # Não deve retornar erro 403 (CSRF)
        self.assertNotEqual(response.status_code, 403)