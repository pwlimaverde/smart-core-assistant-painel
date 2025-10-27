import os
import sys
import django

sys.path.append('src/smart_core_assistant_painel')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import DepartamentoSync, AtendenteHumanoSync
from smart_core_assistant_painel.app.notion_sync.signals import schedule_sync_operation

print('Testando sincronização...')

# Testar Departamento
print('\n=== Testando Departamento ===')
for sync in DepartamentoSync.objects.all():
    print(f'Testando sincronização do departamento: {sync.departamento.nome}')

    try:
        # Preparar dados
        sync.prepare_notion_data()
        sync.save()
        print(f'✅ Dados preparados com sucesso')

        # Agendar sincronização
        schedule_sync_operation(
            model_name="Departamento",
            instance_id=sync.departamento.id,
            operation="update"
        )
        print(f'✅ Sincronização agendada com sucesso')

    except Exception as e:
        print(f'❌ Erro: {e}')

# Testar Atendente
print('\n=== Testando Atendente ===')
for sync in AtendenteHumanoSync.objects.all():
    print(f'Testando sincronização do atendente: {sync.atendente.nome}')

    try:
        # Preparar dados
        sync.prepare_notion_data()
        sync.save()
        print(f'✅ Dados preparados com sucesso')

        # Agendar sincronização
        schedule_sync_operation(
            model_name="AtendenteHumano",
            instance_id=sync.atendente.id,
            operation="update"
        )
        print(f'✅ Sincronização agendada com sucesso')

    except Exception as e:
        print(f'❌ Erro: {e}')

print('\n=== Verificando resultado ===')
print('Departamentos:')
for sync in DepartamentoSync.objects.all():
    print(f'  - {sync.departamento.nome} | Status: {sync.sync_status} | External ID: {sync.external_id or "NÃO SINCRONIZADO"}')
    if sync.sync_error:
        print(f'    Erro: {sync.sync_error}')

print('\nAtendentes:')
for sync in AtendenteHumanoSync.objects.all():
    print(f'  - {sync.atendente.nome} | Status: {sync.sync_status} | External ID: {sync.external_id or "NÃO SINCRONIZADO"}')
    if sync.sync_error:
        print(f'    Erro: {sync.sync_error}')

print('\nTeste concluído!')
