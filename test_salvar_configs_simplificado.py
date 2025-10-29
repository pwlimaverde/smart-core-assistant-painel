"""
Script simplificado para testar apenas o salvamento das configurações de atendimentos.
"""

import os
import sys
import asyncio

# Adicionar o path do projeto (mesmo padrão do script original)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'smart_core_assistant_painel'))

# Configurar Django (mesmo padrão do script original)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.ui.core.settings')

import django
django.setup()

from asgiref.sync import sync_to_async
from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig


class MockDatabase:
    """Classe mock para simular database do Notion."""

    def __init__(self, db_id: str, data_source_id: str):
        self.id = db_id
        self.data_sources = [{"id": data_source_id}]


async def testar_salvamento_configuracoes():
    """Testa o salvamento das configurações com dados mock."""

    print("🧪 Iniciando teste de salvamento de configurações...")

    # Criar databases mock
    atendimento_db = MockDatabase("73752f54-f40a-4d9b-be41-b035812e9cfc", "2d9f278a-7cf6-4f7c-9212-46405537f11e")
    mensagem_db = MockDatabase("2f46b73e-d8f0-4785-b7ad-2ae966c9730a", "8a3c5b9e-d1f2-4e7c-9c3d-5f9e6a7b8c9d")

    print(f"🔍 Mock databases criadas:")
    print(f"   - Atendimento ID: {atendimento_db.id}")
    print(f"   - Atendimento Data Source: {atendimento_db.data_sources[0]['id']}")
    print(f"   - Mensagem ID: {mensagem_db.id}")
    print(f"   - Mensagem Data Source: {mensagem_db.data_sources[0]['id']}")

    try:
        print("💾 Salvando configurações no modelo NotionDatabaseConfig...")

        # Obter data_source_ids
        atendimento_data_source_id = (
            atendimento_db.data_sources[0]["id"]
            if atendimento_db.data_sources
            else None
        )
        mensagem_data_source_id = (
            mensagem_db.data_sources[0]["id"]
            if mensagem_db.data_sources
            else None
        )

        print(f"🔍 Data Source IDs obtidos: Atendimento={atendimento_data_source_id}, Mensagem={mensagem_data_source_id}")

        # Configuração para Atendimentos
        print("🔍 Criando configuração para Atendimentos...")
        atendimento_config = await sync_to_async(NotionDatabaseConfig.objects.update_or_create)(
            slug="ui_atendimentos_atendimento",
            defaults={
                "name": "🎯 Atendimentos CRM",
                "description": "Database para sincronização de atendimentos do sistema",
                "notion_database_id": atendimento_db.id,
                "data_source_id": atendimento_data_source_id,
                "django_model": "ui.atendimentos.Atendimento",
                "django_app_label": "ui",
                "notion_schema": {
                    "Protocolo": {"title": {}},
                    "Status": {"select": {"options": []}},
                    "Prioridade": {"select": {"options": []}},
                },
                "field_mappings": {
                    "protocolo": "Protocolo",
                    "status": "Status",
                    "prioridade": "Prioridade",
                },
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 7,
                "auto_sync": True,
            },

        )

        print(f"✅ Configuração Atendimento criada: {atendimento_config[0].id}")

        # Configuração para Mensagens
        print("🔍 Criando configuração para Mensagens...")
        mensagem_config = await sync_to_async(NotionDatabaseConfig.objects.update_or_create)(
            slug="ui_atendimentos_mensagem",
            defaults={
                "name": "💬 Mensagens CRM",
                "description": "Database para sincronização de mensagens do sistema",
                "notion_database_id": mensagem_db.id,
                "data_source_id": mensagem_data_source_id,
                "django_model": "ui.atendimentos.Mensagem",
                "django_app_label": "ui",
                "notion_schema": {
                    "Conteúdo": {"title": {}},
                    "Tipo": {"select": {"options": []}},
                    "Remetente": {"select": {"options": []}},
                },
                "field_mappings": {
                    "conteudo": "Conteúdo",
                    "tipo": "Tipo",
                    "remetente": "Remetente",
                },
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 8,
                "auto_sync": True,
            },
        )

        print(f"✅ Configuração Mensagem criada: {mensagem_config[0].id}")

        # Verificação
        print("🔍 Verificando se as configs foram realmente salvas...")

        try:
            check_atendimento = await sync_to_async(NotionDatabaseConfig.objects.get)(slug="ui_atendimentos_atendimento")
            print(f"✅ Verificação: Atendimento config encontrada com ID {check_atendimento.id}")
        except Exception as e:
            print(f"❌ Verificação: Atendimento config NÃO foi encontrada! Erro: {e}")

        try:
            check_mensagem = await sync_to_async(NotionDatabaseConfig.objects.get)(slug="ui_atendimentos_mensagem")
            print(f"✅ Verificação: Mensagem config encontrada com ID {check_mensagem.id}")
        except Exception as e:
            print(f"❌ Verificação: Mensagem config NÃO foi encontrada! Erro: {e}")

        print("🎉 Teste de salvamento concluído com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False


async def listar_configs_existentes():
    """Lista todas as configurações existentes."""
    print("\n📋 Configurações existentes no banco:")

    try:
        configs = await sync_to_async(list)(NotionDatabaseConfig.objects.all().values('slug', 'name', 'notion_database_id', 'data_source_id'))

        if not configs:
            print("   (Nenhuma configuração encontrada)")
        else:
            for config in configs:
                print(f"   - {config['slug']}: {config['name']}")
                print(f"     Database ID: {config['notion_database_id']}")
                print(f"     Data Source ID: {config['data_source_id']}")
                print()

    except Exception as e:
        print(f"❌ Erro ao listar configurações: {e}")


async def main():
    """Função principal."""
    print("🚀 Teste de salvamento de configurações de atendimentos/mensagens")
    print("=" * 60)

    # Listar configs existentes antes
    await listar_configs_existentes()

    # Executar teste
    success = await testar_salvamento_configuracoes()

    # Listar configs existentes depois
    await listar_configs_existentes()

    if success:
        print("\n🎉 SUCESSO: Configurações foram salvas corretamente!")
    else:
        print("\n💥 FALHA: Ocorreu um erro ao salvar as configurações.")


if __name__ == "__main__":
    asyncio.run(main())
