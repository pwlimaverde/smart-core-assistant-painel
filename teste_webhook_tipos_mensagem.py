#!/usr/bin/env python3
"""
Teste para verificar se o webhook_whatsapp processa corretamente diferentes tipos de mensagens.
"""

import os
import sys
import json
import logging
from unittest.mock import MagicMock, patch

import django

# Configurar logging para debug
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurar Django com configurações mínimas para teste
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
sys.path.insert(0, os.path.abspath('src'))

# Desativar verificação de aplicações instaladas para teste standalone
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'

print("Configurando Django...")
try:
    django.setup()
    print("Django configurado com sucesso!")
except Exception as e:
    print(f"Erro ao configurar Django: {e}")
    sys.exit(1)


def test_webhook_tipos_mensagem():
    """Testa se o webhook_whatsapp processa corretamente diferentes tipos de mensagens."""
    from smart_core_assistant_painel.app.ui.oraculo.views import webhook_whatsapp
    from smart_core_assistant_painel.app.ui.oraculo.models import TipoMensagem, Mensagem
    from django.http import HttpRequest

    # Função para criar um mock de request com dados de mensagem
    def create_mock_request(message_type, message_content):
        request = MagicMock(spec=HttpRequest)
        
        # Estrutura base do webhook
        data = {
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "id": f"test-message-id-{message_type}"
                },
                "message": {}
            }
        }
        
        # Adicionar o tipo específico de mensagem
        if message_type == "extendedTextMessage":
            data["data"]["message"][message_type] = {"text": message_content}
        elif message_type == "imageMessage":
            data["data"]["message"][message_type] = {
                "caption": message_content,
                "mimetype": "image/jpeg",
                "url": "https://example.com/image.jpg",
                "fileLength": 12345
            }
        elif message_type == "videoMessage":
            data["data"]["message"][message_type] = {
                "caption": message_content,
                "mimetype": "video/mp4",
                "url": "https://example.com/video.mp4",
                "seconds": 30,
                "fileLength": 123456
            }
        elif message_type == "audioMessage":
            data["data"]["message"][message_type] = {
                "mimetype": "audio/ogg",
                "url": "https://example.com/audio.ogg",
                "seconds": 15,
                "ptt": True
            }
        elif message_type == "documentMessage":
            data["data"]["message"][message_type] = {
                "fileName": message_content,
                "mimetype": "application/pdf",
                "url": "https://example.com/document.pdf",
                "fileLength": 54321
            }
        
        request.body = json.dumps(data).encode('utf-8')
        return request

    # Patch para processar_mensagem_whatsapp para evitar acesso ao banco de dados
    with patch('smart_core_assistant_painel.app.ui.oraculo.models.processar_mensagem_whatsapp') as mock_processar:
        # Configurar o mock para retornar um objeto mensagem simulado
        mock_mensagem = MagicMock(spec=Mensagem)
        mock_mensagem.id = 1
        mock_processar.return_value = mock_mensagem
        
        # Testar mensagem de texto
        print("\n✅ TESTE DE MENSAGEM DE TEXTO")
        request = create_mock_request("extendedTextMessage", "Olá, esta é uma mensagem de teste!")
        response = webhook_whatsapp(request)
        assert response.status_code == 200
        mock_processar.assert_called_with(
            numero_telefone="5511999999999",
            conteudo="Olá, esta é uma mensagem de teste!",
            tipo_mensagem=TipoMensagem.TEXTO_FORMATADO,
            message_id="test-message-id-extendedTextMessage",
            metadados={},
            remetente="cliente"
        )
        print("   ✓ Mensagem de texto processada corretamente")
        
        # Testar mensagem de imagem
        print("\n✅ TESTE DE MENSAGEM DE IMAGEM")
        mock_processar.reset_mock()
        request = create_mock_request("imageMessage", "Foto do produto")
        response = webhook_whatsapp(request)
        assert response.status_code == 200
        mock_processar.assert_called_with(
            numero_telefone="5511999999999",
            conteudo="Foto do produto",
            tipo_mensagem=TipoMensagem.IMAGEM,
            message_id="test-message-id-imageMessage",
            metadados={
                'mimetype': 'image/jpeg',
                'url': 'https://example.com/image.jpg',
                'fileLength': 12345
            },
            remetente="cliente"
        )
        print("   ✓ Mensagem de imagem processada corretamente")
        
        # Testar mensagem de vídeo
        print("\n✅ TESTE DE MENSAGEM DE VÍDEO")
        mock_processar.reset_mock()
        request = create_mock_request("videoMessage", "Vídeo demonstrativo")
        response = webhook_whatsapp(request)
        assert response.status_code == 200
        mock_processar.assert_called_with(
            numero_telefone="5511999999999",
            conteudo="Vídeo demonstrativo",
            tipo_mensagem=TipoMensagem.VIDEO,
            message_id="test-message-id-videoMessage",
            metadados={
                'mimetype': 'video/mp4',
                'url': 'https://example.com/video.mp4',
                'seconds': 30,
                'fileLength': 123456
            },
            remetente="cliente"
        )
        print("   ✓ Mensagem de vídeo processada corretamente")
        
        # Testar mensagem de áudio
        print("\n✅ TESTE DE MENSAGEM DE ÁUDIO")
        mock_processar.reset_mock()
        request = create_mock_request("audioMessage", "")
        response = webhook_whatsapp(request)
        assert response.status_code == 200
        mock_processar.assert_called_with(
            numero_telefone="5511999999999",
            conteudo="Áudio recebido",
            tipo_mensagem=TipoMensagem.AUDIO,
            message_id="test-message-id-audioMessage",
            metadados={
                'mimetype': 'audio/ogg',
                'url': 'https://example.com/audio.ogg',
                'seconds': 15,
                'ptt': True
            },
            remetente="cliente"
        )
        print("   ✓ Mensagem de áudio processada corretamente")
        
        # Testar mensagem de documento
        print("\n✅ TESTE DE MENSAGEM DE DOCUMENTO")
        mock_processar.reset_mock()
        request = create_mock_request("documentMessage", "relatorio.pdf")
        response = webhook_whatsapp(request)
        assert response.status_code == 200
        mock_processar.assert_called_with(
            numero_telefone="5511999999999",
            conteudo="relatorio.pdf",
            tipo_mensagem=TipoMensagem.DOCUMENTO,
            message_id="test-message-id-documentMessage",
            metadados={
                'mimetype': 'application/pdf',
                'url': 'https://example.com/document.pdf',
                'fileLength': 54321
            },
            remetente="cliente"
        )
        print("   ✓ Mensagem de documento processada corretamente")

    print("\n✅ TODOS OS TESTES PASSARAM!")
    print("O webhook_whatsapp está processando corretamente diferentes tipos de mensagens.")


if __name__ == "__main__":
    test_webhook_tipos_mensagem()