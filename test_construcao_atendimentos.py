"""
Script de teste para construção de databases de atendimentos no Notion.

Este script testa a implementação corrigida da construção de databases
de atendimentos e mensagens, seguindo o padrão existente.
"""

import asyncio
import os
import sys

# Adicionar o path do projeto (mesmo padrão do script original)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'smart_core_assistant_painel'))

# Configurar Django (mesmo padrão do script original)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.ui.core.settings')

import django
django.setup()

async def test_construcao_atendimentos():
    """Testa a construção de databases de atendimentos."""
    try:
        from app.notion_sync.scripts.script_constructor_notion import (
            NotionAtendimentosDatabaseConstructor
        )

        print("🧪 Iniciando teste de construção de atendimentos...")

        # Verificar se as variáveis de ambiente estão configuradas
        if not os.getenv("NOTION_TOKEN") or not os.getenv("NOTION_PAGE_ID"):
            print("❌ Configure NOTION_TOKEN e NOTION_PAGE_ID no .env")
            return False

        # Verificar se as databases necessárias existem
        from app.notion_sync.models import NotionDatabaseConfig

        configs_necessarias = [
            "ui_clientes_contato",
            "ui_operacional_departamento",
            "ui_operacional_atendente"
        ]

        for slug in configs_necessarias:
            try:
                NotionDatabaseConfig.objects.get(slug=slug)
                print(f"✅ Configuração {slug} encontrada")
            except NotionDatabaseConfig.DoesNotExist:
                print(f"❌ Configuração {slug} não encontrada")
                print("Execute primeiro a construção de clientes e operacional")
                return False

        # Executar a construção
        constructor = NotionAtendimentosDatabaseConstructor()
        await constructor.construct_atendimentos_databases()

        print("✅ Teste de construção de atendimentos concluído com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_construcao_atendimentos())
    if success:
        print("🎉 Todos os testes passaram!")
    else:
        print("💥 Alguns testes falharam!")
