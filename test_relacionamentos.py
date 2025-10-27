"""
Script para testar relacionamentos entre Departamento e AtendenteHumano no Notion.

Este script verifica se os vínculos estão sendo estabelecidos corretamente
nas databases do Notion após a sincronização.
"""

import os
import sys
import django

sys.path.append('src/smart_core_assistant_painel')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import DepartamentoSync, AtendenteHumanoSync
from smart_core_assistant_painel.app.ui.operacional.models import Departamento, AtendenteHumano


def main():
    print('🔍 Testando Relacionamentos no Notion')
    print('=' * 50)

    # Verificar relacionamentos no Django
    print('\n📋 RELACIONAMENTOS NO DJANGO:')
    for depto in Departamento.objects.all():
        print(f'\n🏛️ Departamento: {depto.nome}')
        atendentes = depto.atendentes.filter(ativo=True)
        if atendentes.exists():
            for atendente in atendentes:
                print(f'  👤 {atendente.nome} ({atendente.cargo})')
        else:
            print('  (Sem atendentes ativos)')

    # Verificar sync records e seus metadados
    print('\n🔄 METADADOS DOS SYNC RECORDS:')

    for depto_sync in DepartamentoSync.objects.all():
        print(f'\n🏛️ DepartamentoSync: {depto_sync.departamento.nome}')
        if depto_sync.metadados:
            if 'atendentes_vinculados' in depto_sync.metadados:
                atendentes_info = depto_sync.metadados['atendentes_vinculados']
                print(f'  📝 Atendentes nos metadados: {atendentes_info}')
            else:
                print('  📝 (Sem atendentes_vinculados nos metadados)')
        else:
            print('  📝 (Sem metadados)')

    for atendente_sync in AtendenteHumanoSync.objects.all():
        print(f'\n👤 AtendenteHumanoSync: {atendente_sync.atendente.nome}')
        if atendente_sync.atendente.departamento:
            print(f'  🏢 Departamento: {atendente_sync.atendente.departamento.nome}')
        else:
            print('  🏢 (Sem departamento)')

        if atendente_sync.metadados:
            if 'departamento_vinculado' in atendente_sync.metadados:
                depto_info = atendente_sync.metadados['departamento_vinculado']
                print(f'  📝 Departamento nos metadados: {depto_info}')
            else:
                print('  📝 (Sem departamento_vinculado nos metadados)')
        else:
            print('  📝 (Sem metadados)')

    # Testar trigger de sincronização alterando um relacionamento
    print('\n🧪 TESTE DE SINCRONIZAÇÃO:')
    print('Alterando departamento de um atendente para testar o trigger...')

    try:
        # Pegar um atendente e mudar de departamento
        atendente = AtendenteHumano.objects.first()
        if not atendente:
            print('Nenhum atendente encontrado para teste')
            return

        depto_original = atendente.departamento
        novo_depto = Departamento.objects.exclude(id=depto_original.id).first()

        if not novo_depto:
            print('Apenas um departamento encontrado, não é possível testar mudança')
            return

        print(f'Movendo {atendente.nome} de "{depto_original.nome}" para "{novo_depto.nome}"')

        # Salvar para disparar signals
        atendente.departamento = novo_depto
        atendente.save()

        print('✅ Atendente movido! Verificando se sync foi agendado...')

        # Verificar status após um momento
        import time
        time.sleep(2)  # Dar tempo para o signal executar

        # Verificar sync records
        atendente_sync = AtendenteHumanoSync.objects.get(atendente=atendente)
        depto_sync_antigo = DepartamentoSync.objects.get(departamento=depto_original)
        depto_sync_novo = DepartamentoSync.objects.get(departamento=novo_depto)

        print(f'📊 Status após mudança:')
        print(f'  Atendente: {atendente_sync.sync_status}')
        print(f'  Departamento Antigo: {depto_sync_antigo.sync_status}')
        print(f'  Departamento Novo: {depto_sync_novo.sync_status}')

        # Voltar ao original
        print('\n🔄 Restaurando relacionamento original...')
        atendente.departamento = depto_original
        atendente.save()

        print('✅ Teste concluído!')

    except Exception as e:
        print(f'❌ Erro no teste: {e}')


if __name__ == '__main__':
    main()
