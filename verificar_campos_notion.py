"""
Script para verificar os campos criados nas databases do Notion.
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

async def verificar_campos():
    """Verifica os campos criados nas databases do Notion."""

    token = os.getenv('NOTION_TOKEN')
    if not token:
        print("❌ NOTION_TOKEN não encontrado no .env")
        return

    client = NotionAsyncClient(auth=token)

    # IDs das databases criadas
    contato_db_id = '1b342e65-9f15-4dab-a198-63a158d2a96a'
    cliente_db_id = '4b5f7e64-dc64-4a4d-aa53-808dc98a303a'

    print("=" * 80)
    print("VERIFICAÇÃO DE CAMPOS CRIADOS NO NOTION")
    print("=" * 80)

    # Verificar database de Contatos
    try:
        print(f"\n📋 DATABASE DE CONTATOS: {contato_db_id}")
        print("-" * 60)

        contato_db = await client.databases.retrieve(contato_db_id)

        print("Título:", contato_db.get('title', [{}])[0].get('text', {}).get('content', 'Sem título'))
        print("\n📝 CAMPOS DISPONÍVEIS:")

        campos_contato = []
        for prop_name, prop_data in contato_db['properties'].items():
            prop_type = prop_data.get('type', 'unknown')
            campos_contato.append((prop_name, prop_type))
            print(f"  ✅ {prop_name:<30} [{prop_type}]")

            # Detalhes adicionais
            if prop_type == 'relation':
                relation = prop_data.get('relation', {})
                database_id = relation.get('database_id', 'N/A')
                print(f"      → Relaciona com database: {database_id}")
            elif prop_type == 'select':
                options = prop_data.get('select', {}).get('options', [])
                if options:
                    opcoes = [opt.get('name') for opt in options]
                    print(f"      → Opções: {opcoes}")

        # Verificar páginas criadas
        print(f"\n📄 VERIFICANDO PÁGINAS CRIADAS:")
        pages_query = await client.databases.query(
            database_id=contato_db_id,
            page_size=5
        )

        for i, page in enumerate(pages_query.get('results', [])):
            print(f"\n  Página {i+1}:")
            print(f"    ID: {page.get('id')}")

            # Mostrar propriedades da página
            props = page.get('properties', {})
            for prop_name, prop_value in props.items():
                if prop_name in campos_contato:
                    prop_type = next(t for n, t in campos_contato if n == prop_name)

                    if prop_type == 'title':
                        title = prop_value.get('title', [])
                        if title:
                            print(f"    {prop_name}: {title[0].get('text', {}).get('content', '')}")
                    elif prop_type == 'phone_number':
                        phone = prop_value.get('phone_number', '')
                        if phone:
                            print(f"    {prop_name}: {phone}")
                    elif prop_type == 'email':
                        email = prop_value.get('email', '')
                        if email:
                            print(f"    {prop_name}: {email}")
                    elif prop_type == 'relation':
                        relations = prop_value.get('relation', [])
                        if relations:
                            print(f"    {prop_name}: {len(relations)} relacionamento(s)")
                            for rel in relations[:2]:  # Limitar a 2 para não poluir
                                print(f"      → ID: {rel.get('id')}")

    except Exception as e:
        print(f"❌ Erro ao verificar database de Contatos: {e}")

    # Verificar database de Clientes
    try:
        print(f"\n📋 DATABASE DE CLIENTES: {cliente_db_id}")
        print("-" * 60)

        cliente_db = await client.databases.retrieve(cliente_db_id)

        print("Título:", cliente_db.get('title', [{}])[0].get('text', {}).get('content', 'Sem título'))
        print("\n📝 CAMPOS DISPONÍVEIS:")

        campos_cliente = []
        for prop_name, prop_data in cliente_db['properties'].items():
            prop_type = prop_data.get('type', 'unknown')
            campos_cliente.append((prop_name, prop_type))
            print(f"  ✅ {prop_name:<30} [{prop_type}]")

            # Detalhes adicionais
            if prop_type == 'relation':
                relation = prop_data.get('relation', {})
                database_id = relation.get('database_id', 'N/A')
                print(f"      → Relaciona com database: {database_id}")
            elif prop_type == 'select':
                options = prop_data.get('select', {}).get('options', [])
                if options:
                    opcoes = [opt.get('name') for opt in options]
                    print(f"      → Opções: {opcoes}")

        # Verificar páginas criadas
        print(f"\n📄 VERIFICANDO PÁGINAS CRIADAS:")
        pages_query = await client.databases.query(
            database_id=cliente_db_id,
            page_size=5
        )

        for i, page in enumerate(pages_query.get('results', [])):
            print(f"\n  Página {i+1}:")
            print(f"    ID: {page.get('id')}")

            # Mostrar propriedades da página
            props = page.get('properties', {})
            for prop_name, prop_value in props.items():
                if prop_name in campos_cliente:
                    prop_type = next(t for n, t in campos_cliente if n == prop_name)

                    if prop_type == 'title':
                        title = prop_value.get('title', [])
                        if title:
                            print(f"    {prop_name}: {title[0].get('text', {}).get('content', '')}")
                    elif prop_type == 'rich_text':
                        text = prop_value.get('rich_text', [])
                        if text:
                            print(f"    {prop_name}: {text[0].get('text', {}).get('content', '')}")
                    elif prop_type == 'select':
                        select = prop_value.get('select', {})
                        if select:
                            print(f"    {prop_name}: {select.get('name', '')}")
                    elif prop_type == 'relation':
                        relations = prop_value.get('relation', [])
                        if relations:
                            print(f"    {prop_name}: {len(relations)} relacionamento(s)")
                            for rel in relations[:2]:  # Limitar a 2 para não poluir
                                print(f"      → ID: {rel.get('id')}")

    except Exception as e:
        print(f"❌ Erro ao verificar database de Clientes: {e}")

    print("\n" + "=" * 80)
    print("📋 RESUMO")
    print("=" * 80)
    print("\n⚠️  IMPORTANTE:")
    print("Se os campos de relacionamento não aparecem, você precisará adicioná-los manualmente:")
    print()
    print("1. Na database de CONTATOS, adicione o campo:")
    print("   Nome: Empresas Relacionadas")
    print("   Tipo: Relation")
    print("   Database: Selecione a database de Clientes")
    print()
    print("2. Na database de CLIENTES, adicione o campo:")
    print("   Nome: Contatos Relacionados")
    print("   Tipo: Relation")
    print("   Database: Selecione a database de Contatos")
    print()
    print("🔗 Links diretos:")
    print(f"   Contatos: https://www.notion.so/{contato_db_id}")
    print(f"   Clientes: https://www.notion.so/{cliente_db_id}")

if __name__ == "__main__":
    asyncio.run(verificar_campos())
