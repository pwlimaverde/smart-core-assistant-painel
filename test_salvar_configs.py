"""
Script para testar o salvamento das configurações de atendimentos.
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

async def test_salvar_configs():
    """Testa apenas o salvamento das configurações."""
    try:
        from app.notion_sync.models import NotionDatabaseConfig

        # Verificar se as databases foram criadas
        try:
            atendimento_config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_atendimento")
            print(f"✅ Configuração Atendimento encontrada: {atendimento_config.id}")
            print(f"   Database ID: {atendimento_config.notion_database_id}")
            print(f"   Data Source ID: {atendimento_config.data_source_id}")
            print(f"   Pronta para sync: {atendimento_config.is_ready_for_sync()}")
        except NotionDatabaseConfig.DoesNotExist:
            print("❌ Configuração de Atendimento não encontrada")

        try:
            mensagem_config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_mensagem")
            print(f"✅ Configuração Mensagem encontrada: {mensagem_config.id}")
            print(f"   Database ID: {mensagem_config.notion_database_id}")
            print(f"   Data Source ID: {mensagem_config.data_source_id}")
            print(f"   Pronta para sync: {mensagem_config.is_ready_for_sync()}")
        except NotionDatabaseConfig.DoesNotExist:
            print("❌ Configuração de Mensagem não encontrada")

        # Listar todas as configs
        print("\n📋 Todas as configurações disponíveis:")
        for config in NotionDatabaseConfig.objects.all():
            print(f"   - {config.slug}: {config.name}")

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_salvar_configs())
