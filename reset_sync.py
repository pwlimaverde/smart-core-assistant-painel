import os
import sys
import django

sys.path.append('src/smart_core_assistant_painel')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import DepartamentoSync, AtendenteHumanoSync

print('Resetando status de sincronização...')

# Resetar Departamentos
for sync in DepartamentoSync.objects.all():
    sync.sync_status = 'pending'
    sync.sync_error = None
    sync.retry_count = 0
    sync.save()
    print(f'Resetado Departamento: {sync.departamento.nome}')

# Resetar Atendentes
for sync in AtendenteHumanoSync.objects.all():
    sync.sync_status = 'pending'
    sync.sync_error = None
    sync.retry_count = 0
    sync.save()
    print(f'Resetado Atendente: {sync.atendente.nome}')

print('Status resetados com sucesso!')
