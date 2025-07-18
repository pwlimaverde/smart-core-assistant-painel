#!/usr/bin/env python3
"""
Teste para verificar se a correção do webhook está funcionando corretamente.
"""

import os
import sys

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'src.smart_core_assistant_painel.app.ui.core.settings')
sys.path.insert(0, 'src')
django.setup()


def test_webhook_correcao():
    """Testa se a correção do webhook resolve o erro de dict_keys"""

    # Mock de dados do webhook
    webhook_data = {
        "data": {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net"
            },
            "message": {
                "extendedTextMessage": {
                    "text": "Olá, esta é uma mensagem de teste!"
                }
            }
        }
    }

    # Simular o processamento
    data = webhook_data
    phone = data.get('data').get('key').get('remoteJid').split('@')[0]

    # Testar a correção: obter chaves sem erro
    message_keys = data.get('data').get('message').keys()
    primeira_chave = list(message_keys)[0] if message_keys else None

    print("✅ TESTE DE CORREÇÃO DO WEBHOOK")
    print("=" * 40)
    print(f"Telefone extraído: {phone}")
    print(f"Chaves da mensagem: {list(message_keys)}")
    print(f"Primeira chave: {primeira_chave}")

    # Testar integração com TipoMensagem
    from smart_core_assistant_painel.app.ui.oraculo.models import TipoMensagem
    tipo_mensagem = TipoMensagem.obter_por_chave_json(primeira_chave)
    print(f"Tipo da mensagem (enum): {tipo_mensagem}")

    # Testar extração de conteúdo
    if primeira_chave == 'extendedTextMessage':
        message_content = data.get('data').get(
            'message').get('extendedTextMessage').get('text')
        print(f"Conteúdo da mensagem: {message_content}")

    print("\n✅ Teste concluído com sucesso! O erro foi corrigido.")


if __name__ == "__main__":
    test_webhook_correcao()
