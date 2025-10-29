"""
Script para testar apenas a construção de databases de atendimentos/mensagens.
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

async def main():
    """Executa apenas a construção de atendimentos/mensagens."""
    try:
        from app.notion_sync.scripts.script_constructor_notion import run_construction_atendimentos

        print("🚀 Iniciando construção de databases de atendimentos/mensagens...")
        print("⚠️  Pré-requisito: Execute run_construction_operacional() primeiro!")
        print()

        await run_construction_atendimentos()

        print("🎉 Construção de atendimentos/mensagens concluída com sucesso!")

        # Verificar se as configurações foram salvas
        from app.notion_sync.models import NotionDatabaseConfig

        print("\n📋 Verificando configurações salvas:")

        try:
            atendimento_config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_atendimento")
            print(f"✅ Atendimento: {atendimento_config.name} (ID: {atendimento_config.id})")
        except NotionDatabaseConfig.DoesNotExist:
            print("❌ Atendimento: Configuração não encontrada")

        try:
            mensagem_config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_mensagem")
            print(f"✅ Mensagem: {mensagem_config.name} (ID: {mensagem_config.id})")
        except NotionDatabaseConfig.DoesNotExist:
            print("❌ Mensagem: Configuração não encontrada")

    except Exception as e:
        print(f"❌ Erro durante a construção: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
