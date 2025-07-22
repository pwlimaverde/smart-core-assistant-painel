#!/usr/bin/env python3
"""
Teste para verificar se o processamento de mensagens do tipo 'conversation' está funcionando
"""

# Simular dados do webhook com tipo 'conversation'
from smart_core_assistant_painel.app.ui.oraculo.models import TipoMensagem
test_data = {
    "event": "messages.upsert",
    "instance": "arcane",
    "data": {
        "key": {
            "remoteJid": "5516992805443@s.whatsapp.net",
            "fromMe": False,
            "id": "TEST_MESSAGE_123"
        },
        "pushName": "Teste Usuario",
        "message": {
            "conversation": "Olá, esta é uma mensagem de teste"
        },
        "messageType": "conversation",
        "messageTimestamp": 1674739583
    }
}

print("Dados de teste preparados:")
print(f"Tipo da mensagem: {test_data['data']['messageType']}")
print(f"Conteúdo: {test_data['data']['message']['conversation']}")
print(f"PushName: {test_data['data']['pushName']}")
print(f"RemoteJid: {test_data['data']['key']['remoteJid']}")

print("\nTeste de mapeamento de tipo 'conversation':")

# Teste manual do mapeamento

tipo_mensagem = TipoMensagem.obter_por_chave_json('conversation')
print(f"Tipo mapeado: {tipo_mensagem}")
print(f"É TEXTO_FORMATADO? {tipo_mensagem == TipoMensagem.TEXTO_FORMATADO}")

print("\n✓ Testes básicos concluídos!")
