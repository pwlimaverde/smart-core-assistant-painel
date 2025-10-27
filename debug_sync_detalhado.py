"""
Script para debugar sincronização em tempo real e identificar problemas de cache.

Este script vai:
1. Limpar completamente o cache do Django
2. Forçar sincronização passo a passo
3. Monitorar cada operação em detalhes
4. Identificar onde está o problema de atualização
"""

import os
import sys
import django
import time

sys.path.append('src/smart_core_assistant_painel')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
django.setup()

from django.db import connection
from django.core.cache import cache
from smart_core_assistant_painel.app.notion_sync.models import DepartamentoSync, AtendenteHumanoSync
from smart_core_assistant_painel.app.ui.operacional.models import Departamento, AtendenteHumano
from smart_core_assistant_painel.app.notion_sync.signals import schedule_sync_operation

def limpar_cache():
    """Limpa todo o cache do Django e do banco."""
    print("🧹 Limpando caches...")

    # Limpa cache do Django
    cache.clear()

    # Força reset da conexão para limpar cache de queries
    connection.close()
    connection.connect()

    print("✅ Cache limpo")

def verificar_estado_atual():
    """Verifica o estado atual dos dados."""
    print("\n🔍 ESTADO ATUAL:")

    # Dados Django
    print("\n📋 DADOS DJANGO:")
    for depto in Departamento.objects.all():
        atendentes = depto.atendentes.filter(ativo=True)
        print(f"🏛️ {depto.nome}: {list(atendentes.values_list('nome', flat=True))}")

    # Sync Records
    print("\n📝 SYNC RECORDS:")
    for depto_sync in DepartamentoSync.objects.all():
        print(f"🏛️ {depto_sync.departamento.nome}: external_id={depto_sync.external_id}, status={depto_sync.sync_status}")

    for atendente_sync in AtendenteHumanoSync.objects.all():
        depto_nome = atendente_sync.atendente.departamento.nome if atendente_sync.atendente.departamento else "Nenhum"
        print(f"👤 {atendente_sync.atendente.nome}: depto='{depto_nome}', external_id={atendente_sync.external_id}, status={atendente_sync.sync_status}")

def debug_mudanca_atendente():
    """Debug detalhado da mudança de atendente."""
    print("\n🔧 DEBUG MUDANÇA DE ATENDENTE:")

    # Pegar um atendente para teste
    atendente = AtendenteHumano.objects.filter(departamento__isnull=False).first()
    if not atendente:
        print("❌ Nenhum atendente com departamento encontrado")
        return

    depto_original = atendente.departamento
    depto_novo = Departamento.objects.exclude(id=depto_original.id).first()

    if not depto_novo:
        print("❌ Apenas um departamento encontrado")
        return

    print(f"👤 Movendo {atendente.nome} de '{depto_original.nome}' para '{depto_novo.nome}'")

    # Verificar sync records antes
    print("\n📊 ANTES DA MUDANÇA:")
    atendente_sync = AtendenteHumanoSync.objects.get(atendente=atendente)
    depto_sync_original = DepartamentoSync.objects.get(departamento=depto_original)
    depto_sync_novo = DepartamentoSync.objects.get(departamento=depto_novo)


    print(f"  Depto Original: {depto_sync_original.departamento.nome}, sync_status={depto_sync_original.sync_status}")
    print(f"  Depto Novo: {depto_sync_novo.departamento.nome}, sync_status={depto_sync_novo.sync_status}")

    # FORÇAR PREPARAÇÃO DE DADOS
    print("\n🔄 PREPARANDO DADOS FORÇADAMENTE:")

    # Preparar sync do atendente
    atendente_sync.prepare_notion_data()
    atendente_sync.save()
    print(f"  ✅ AtendenteSync preparado: depto_id={atendente.departamento_id if atendente.departamento_id else 'Nenhum'}")

    # Preparar sync do departamento original
    depto_sync_original.prepare_notion_data()
    depto_sync_original.save()
    print(f"  ✅ DeptoOriginalSync preparado")

    # Preparar sync do departamento novo (ainda sem o atendente)
    depto_sync_novo.prepare_notion_data()
    depto_sync_novo.save()
    print(f"  ✅ DeptoNovoSync preparado (antes de adicionar atendente)")

    # Mudar atendente de departamento (ESTE É O PASSO CRÍTICO)
    print(f"\n🔄 EXECUTANDO MUDANÇA:")
    print(f"  Antes: atendente.departamento_id = {atendente.departamento_id}")

    # Salvar original_department_id para o signal
    atendente._original_departamento_id = atendente.departamento_id
    atendente.departamento = depto_novo
    atendente.save()

    print(f"  Depois: atendente.departamento_id = {atendente.departamento_id}")

    # Esperar um pouco para o signal processar
    print("\n⏳ AGUARDANDO PROCESSAMENTO DOS SIGNALS (5 segundos)...")
    time.sleep(5)

    # Verificar estado após a mudança
    print("\n📊 APÓS A MUDANÇA:")

    # Recarregar do banco para garantir dados frescos
    atendente.refresh_from_db()
    depto_sync_original.refresh_from_db()
    depto_sync_novo.refresh_from_db()
    atendente_sync.refresh_from_db()

    print(f"  Atendente: depto_id={atendente.departamento_id}, sync_status={atendente_sync.sync_status}")
    print(f"  Depto Original: sync_status={depto_sync_original.sync_status}")
    print(f"  Depto Novo: sync_status={depto_sync_novo.sync_status}")

    # Verificar se os relacionamentos foram atualizados nos dados do Notion
    print("\n🔍 VERIFICANDO PROPERTIES DO NOTION:")

    # Verificar properties do atendente
    print(f"  AtendenteSync.notion_properties keys: {list(atendente_sync.notion_properties.keys())}")
    if 'Departamentos Relacionados' in atendente_sync.notion_properties:
        rel_data = atendente_sync.notion_properties['Departamentos Relacionados']
        print(f"    Departamentos Relacionados: {rel_data}")
    else:
        print("    ❌ 'Departamentos Relacionados' não encontrado nas properties!")

    # Verificar properties do depto original
    print(f"  DeptoOriginalSync.notion_properties keys: {list(depto_sync_original.notion_properties.keys())}")
    if 'Atendentes Relacionados' in depto_sync_original.notion_properties:
        rel_data = depto_sync_original.notion_properties['Atendentes Relacionados']
        print(f"    Atendentes Relacionados: {rel_data}")
    else:
        print("    ❌ 'Atendentes Relacionados' não encontrado nas properties!")

    # Verificar properties do depto novo
    print(f"  DeptoNovoSync.notion_properties keys: {list(depto_sync_novo.notion_properties.keys())}")
    if 'Atendentes Relacionados' in depto_sync_novo.notion_properties:
        rel_data = depto_sync_novo.notion_properties['Atendentes Relacionados']
        print(f"    Atendentes Relacionados: {rel_data}")
    else:
        print("    ❌ 'Atendentes Relacionados' não encontrado nas properties!")

    # Forçar sincronização manual se necessário
    if depto_sync_novo.sync_status == 'pending':
        print(f"\n🚀 FORÇANDO SINCRONIZAÇÃO DO DEPARTAMENTO NOVO...")
        try:
            schedule_sync_operation(
                model_name="Departamento",
                instance_id=depto_novo.id,
                operation="update"
            )
            print("✅ Sincronização forçada!")
        except Exception as e:
            print(f"❌ Erro ao forçar sincronização: {e}")

    print("\n⏳ AGUARDANDO 10 SEGUNDOS PARA VERIFICAR NO NOTION...")
    time.sleep(10)

    # Verificação final
    print("\n📊 VERIFICAÇÃO FINAL:")

    # Recarregar todos do banco
    for sync in [atendente_sync, depto_sync_original, depto_sync_novo]:
        sync.refresh_from_db()

    print(f"  Atendente: depto={atendente.departamento.nome if atendente.departamento else 'Nenhum'}, status={atendente_sync.sync_status}")
    print(f"  Depto Original: status={depto_sync_original.sync_status}")
    print(f"  Depto Novo: status={depto_sync_novo.sync_status}")

def main():
    """Função principal do debug."""
    print("🐛 DEBUG DE SINCRONIZAÇÃO DETALHADO")
    print("=" * 60)

    # Limpar cache
    limpar_cache()

    # Verificar estado atual
    verificar_estado_atual()

    # Debug da mudança
    debug_mudanca_atendente()

    print("\n✅ DEBUG CONCLUÍDO!")
    print("\n📋 RESUMO:")
    print("1. Verifique se os properties foram atualizados corretamente")
    print("2. Verifique no Notion se os relacionamentos mudaram")
    print("3. Se ainda não funcionar, pode ser cache do browser Notion")
    print("4. Tente limpar cache do Notion (Ctrl+Shift+R)")

if __name__ == '__main__':
    main()
