#!/usr/bin/env python3
"""
Teste do processamento de mensagens WhatsApp com o formato JSON correto
"""

# JSON correto conforme fornecido pelo usuário
test_payload = {
    "event": "messages.upsert",
    "instance": "arcane",
    "data": {
        "key": {
            "remoteJid": "5516992805443@s.whatsapp.net",
            "fromMe": False,
            "id": "5F2AAA4BD98BB388BBCD6FCB9B4ED676"
        },
        "pushName": "xpto",
        "message": {
            "extendedTextMessage": {
                "text": "Meu nome é Paulo Weslley"
            }
        },
        "messageType": "conversation",
        "messageTimestamp": 1748739583
    },
    "owner": "arcane",
    "source": "android",
    "destination": "localhost",
    "date_time": "2025-05-31T21:59:43.640Z",
    "sender": "55999999999@s.whatsapp.net",
    "server_url": "http://localhost:8080",
    "apikey": "",
    "webhookUrl": "localhost",
    "executionMode": "production"
}

print("JSON de teste criado:")
print("=" * 50)

print("Estrutura da mensagem:")
print(f"- event: {test_payload['event']}")
print(f"- data.key.remoteJid: {test_payload['data']['key']['remoteJid']}")
print(f"- data.pushName: {test_payload['data']['pushName']}")
print(f"- data.messageType: {test_payload['data']['messageType']}")
print(
    f"- Primeira chave em data.message: {list(test_payload['data']['message'].keys())[0]}")
print(
    f"- Conteúdo real: {test_payload['data']['message']['extendedTextMessage']['text']}")

print("\nAnálise:")
print("- O messageType diz 'conversation' mas a estrutura real é 'extendedTextMessage'")
print("- Com as correções, deve priorizar 'extendedTextMessage' sobre 'conversation'")
print("- O conteúdo deve ser extraído de data.message.extendedTextMessage.text")
print("- PushName 'xpto' deve ser armazenado como nome_perfil_whatsapp")
print("- Texto 'Meu nome é Paulo Weslley' deve ser processado para extração de entidades")

print("\n✓ Teste preparado - usar este payload para testar o webhook")
