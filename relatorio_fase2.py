"""
Script para gerar relatório da Fase 2 da integração com Notion.

Este script exibe um resumo completo da implementação dos models
Departamento e AtendenteHumano com sincronização Notion.
"""

import os
import sys

# Adicionar o path do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.settings')

import django
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig, DepartamentoSync, AtendenteHumanoSync
from smart_core_assistant_painel.app.ui.operacional.models import Departamento, AtendenteHumano


def main():
    """Função principal do relatório."""
    print('=== RELATÓRIO DA FASE 2 - INTEGRAÇÃO NOTION ===\n')

    # Configurações das databases
    print('CONFIGURAÇÕES DAS DATABASES:')
    for config in NotionDatabaseConfig.objects.all():
        print(f'  - {config.name} ({config.slug})')
        print(f'    Modelo: {config.django_model}')
        print(f'    App: {config.django_app_label}')
        print(f'    Sync: {"Habilitado" if config.sync_enabled else "Desabilitado"}')
        print(f'    Campos: {len(config.notion_schema)}')
        print(f'    Database ID: {config.notion_database_id}')
        print()

    # Departamentos
    print('DEPARTAMENTOS:')
    for sync in DepartamentoSync.objects.all():
        depto = sync.departamento
        print(f'  - {depto.nome}')
        print(f'    Status Sync: {sync.sync_status}')
        print(f'    External ID: {sync.external_id or "Não sincronizado"}')
        print(f'    Atendentes: {depto.atendentes.count()}')
        print(f'    Último Sync: {sync.last_sync_at or "Nunca"}')
        print()

    # Atendentes Humanos
    print('ATENDENTES HUMANOS:')
    for sync in AtendenteHumanoSync.objects.all():
        atendente = sync.atendente
        print(f'  - {atendente.nome} - {atendente.cargo}')
        print(f'    Departamento: {atendente.departamento.nome if atendente.departamento else "Nenhum"}')
        print(f'    Status Sync: {sync.sync_status}')
        print(f'    External ID: {sync.external_id or "Não sincronizado"}')
        print(f'    Carga: {sync.carga_atual}/{sync.capacidade_maxima}')
        print(f'    Último Sync: {sync.last_sync_at or "Nunca"}')
        print()

    # Resumo
    print('=== RESUMO ===')
    print(f'Departamentos: {Departamento.objects.count()} criados, {DepartamentoSync.objects.count()} com sync')
    print(f'Atendentes: {AtendenteHumano.objects.count()} criados, {AtendenteHumanoSync.objects.count()} com sync')
    print(f'Databases Configuradas: {NotionDatabaseConfig.objects.count()}')

    # Status de sincronização
    dept_pending = DepartamentoSync.objects.filter(sync_status='pending').count()
    aten_pending = AtendenteHumanoSync.objects.filter(sync_status='pending').count()
    dept_error = DepartamentoSync.objects.filter(sync_status='error').count()
    aten_error = AtendenteHumanoSync.objects.filter(sync_status='error').count()

    print(f'\nSTATUS DA SINCRONIZAÇÃO:')
    print(f'  Pendentes: {dept_pending} departamentos, {aten_pending} atendentes')
    print(f'  Com Erro: {dept_error} departamentos, {aten_error} atendentes')


if __name__ == '__main__':
    main()
