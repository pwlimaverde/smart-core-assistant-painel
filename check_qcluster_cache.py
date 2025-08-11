#!/usr/bin/env python
import os
import sys

# Adicionar o caminho do Django ao PYTHONPATH
sys.path.insert(0, '/app/src/smart_core_assistant_painel/app/ui')
sys.path.insert(0, '/app/src')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.core.cache import cache
from django.conf import settings

print('=== CONFIGURAÇÃO DO CACHE ===')
print(f'Cache backend: {type(cache).__name__}')
print(f'Cache location: {settings.CACHES["default"]["LOCATION"]}')
print(f'Cache timeout: {settings.CACHES["default"].get("TIMEOUT", "Not set")}')

print('\n=== CONFIGURAÇÃO DO Q_CLUSTER ===')
for key, value in settings.Q_CLUSTER.items():
    print(f'{key}: {value}')

print('\n=== TESTE DE CONECTIVIDADE DO CACHE ===')
try:
    cache.set('test_qcluster', 'working', 30)
    result = cache.get('test_qcluster')
    print(f'Cache test result: {result}')
    cache.delete('test_qcluster')
except Exception as e:
    print(f'Cache error: {e}')

print('\n=== VERIFICAÇÃO DE CHAVES EXISTENTES ===')
try:
    # Verificar se há chaves do WhatsApp no cache
    buffer_key = 'wa_buffer_558897141275'
    timer_key = 'wa_timer_558897141275'
    
    buffer_exists = cache.has_key(buffer_key)
    timer_exists = cache.has_key(timer_key)
    
    print(f'Buffer key exists: {buffer_exists}')
    print(f'Timer key exists: {timer_exists}')
    
    if buffer_exists:
        buffer_content = cache.get(buffer_key, [])
        print(f'Buffer content: {len(buffer_content) if buffer_content else 0} messages')
        
except Exception as e:
    print(f'Key check error: {e}')