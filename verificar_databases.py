"""
Script para verificar as propriedades das databases no Notion.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from notion_py_client import NotionAsyncClient

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
import django
django.setup()

load_dotenv()

async def check_databases():
    """Verifica as propriedades das databases no Notion."""

    token = os.getenv('NOTION_TOKEN')
    if not token:
        print("❌ NOTION_TOKEN não encontrado no .env")
        return

    client = NotionAsyncClient(auth=token)

    # IDs das databases criadas
    contato_db_id = '186744b1-51d6-4a9b-9c31-16565d16985c'
    cliente_db_id = 'f475ecfc-18d8-4d42-bd8e-9eea44e5434d'

    print("=" * 60)
    print("PROPRIEDADES DAS DATABASES NO NOTION")
    print("=" * 60)

    # Verificar database de Contatos
    try:
        print(f"\n📋 Database de Contatos: {contato_db_id}")
        print("-" * 40)

        contato_db = await client.databases.retrieve(contato_db_id)

        # Print completo para debug
        print("Resposta completa da API:")
        print(contato_db)

        # Tentar mostrar propriedades se existirem
        if 'properties' in contato_db:
            print("Propriedades:")
            for prop_name, prop_data in contato_db['properties'].items():
                prop_type = prop_data.get('type', 'unknown')
                print(f"  • {prop_name}: {prop_type}")

                # Mostrar detalhes para relações
                if prop_type == 'relation':
                    relation_info = prop_data.get('relation', {})
                    database_id = relation_info.get('database_id', 'N/A')
                    print(f"    → Relaciona com database: {database_id}")
                # Mostrar opções para selects
                elif prop_type == 'select':
                    options = prop_data.get('select', {}).get('options', [])
                    if options:
                        print(f"    → Opções: {[opt.get('name') for opt in options]}")

    except Exception as e:
        print(f"❌ Erro ao verificar database de Contatos: {e}")

    # Verificar database de Clientes
    try:
        print(f"\n📋 Database de Clientes: {cliente_db_id}")
        print("-" * 40)

        cliente_db = await client.databases.retrieve(cliente_db_id)

        # Print completo para debug
        print("Resposta completa da API:")
        print(cliente_db)

        # Tentar mostrar propriedades se existirem
        if 'properties' in cliente_db:
            print("Propriedades:")
            for prop_name, prop_data in cliente_db['properties'].items():
                prop_type = prop_data.get('type', 'unknown')
                print(f"  • {prop_name}: {prop_type}")

                # Mostrar detalhes para relações
                if prop_type == 'relation':
                    relation_info = prop_data.get('relation', {})
                    database_id = relation_info.get('database_id', 'N/A')
                    print(f"    → Relaciona com database: {database_id}")
                # Mostrar opções para selects
                elif prop_type == 'select':
                    options = prop_data.get('select', {}).get('options', [])
                    if options:
                        print(f"    → Opções: {[opt.get('name') for opt in options]}")

    except Exception as e:
        print(f"❌ Erro ao verificar database de Clientes: {e}")

    print("\n" + "=" * 60)
    print("VERIFICAÇÃO CONCLUÍDA")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_databases())
