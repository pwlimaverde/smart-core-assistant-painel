import requests
import json
import time
from datetime import datetime

# Teste simples do webhook
payload = {
    'data': {
        'key': {
            'remoteJid': '558897141275@c.us',
            'fromMe': False,
            'id': f'test_msg_{int(time.time())}'
        },
        'pushName': 'Teste Debug',
        'messageType': 'conversation',
        'message': {
            'conversation': 'Teste de debug do cache'
        },
        'messageTimestamp': int(time.time())
    }
}

print(f'[{datetime.now()}] Enviando webhook...')
response = requests.post('http://localhost:8000/oraculo/webhook_whatsapp/', json=payload)
print(f'[{datetime.now()}] Response: {response.status_code} - {response.text}')