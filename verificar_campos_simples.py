"""
Script simplificado para verificar os campos criados nas databases do Notion.
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
    print("CAMPOS CRIADOS NAS DATABASES DO NOTION")
    print("=" * 80)

    # Verificar database de Contatos
    try:
        print(f"\n📋 DATABASE DE CONTATOS")
        print(f"ID: {contato_db_id}")
        print("-" * 60)

        contato_db = await client.databases.retrieve(contato_db_id)

        # Obter título de forma segura
        title = contato_db.get('title', [])
        title_text = "Sem título"
        if title and len(title) > 0:
            title_text = title[0].get('text', {}).get('content', 'Sem título')
        print(f"Título: {title_text}")

        print("\n📝 CAMPOS DISPONÍVEIS:")
        print("-" * 40)

        for prop_name, prop_data in contato_db['properties'].items():
            prop_type = prop_data.get('type', 'unknown')
            print(f"  ✅ {prop_name:<35} [{prop_type}]")

            # Detalhes para relações
            if prop_type == 'relation':
                relation = prop_data.get('relation', {})
                database_id = relation.get('database_id', 'N/A')
                print(f"      → Relaciona com: {database_id}")
            # Detalhes para selects
            elif prop_type == 'select':
                options = prop_data.get('select', {}).get('options', [])
                if options:
                    opcoes = [opt.get('name') for opt in options]
                    print(f"      → Opções: {', '.join(opcoes)}")

    except Exception as e:
        print(f"❌ Erro ao verificar database de Contatos: {e}")

    # Verificar database de Clientes
    try:
        print(f"\n📋 DATABASE DE CLIENTES")
        print(f"ID: {cliente_db_id}")
        print("-" * 60)

        cliente_db = await client.databases.retrieve(cliente_db_id)

        # Obter título de forma segura
        title = cliente_db.get('title', [])
        title_text = "Sem título"
        if title and len(title) > 0:
            title_text = title[0].get('text', {}).get('content', 'Sem título')
        print(f"Título: {title_text}")

        print("\n📝 CAMPOS DISPONÍVEIS:")
        print("-" * 40)

        for prop_name, prop_data in cliente_db['properties'].items():
            prop_type = prop_data.get('type', 'unknown')
            print(f"  ✅ {prop_name:<35} [{prop_type}]")

            # Detalhes para relações
            if prop_type == 'relation':
                relation = prop_data.get('relation', {})
                database_id = relation.get('database_id', 'N/A')
                print(f"      → Relaciona com: {database_id}")
            # Detalhes para selects
            elif prop_type == 'select':
                options = prop_data.get('select', {}).get('options', [])
                if options:
                    opcoes = [opt.get('name') for opt in options]
                    print(f"      → Opções: {', '.join(opcoes)}")

    except Exception as e:
        print(f"❌ Erro ao verificar database de Clientes: {e}")

    print("\n" + "=" * 80)
    print("📋 INSTRUÇÕES PARA ADICIONAR RELACIONAMENTOS MANUALMENTE")
    print("=" * 80)

    print("""
⚠️  SE OS CAMPOS DE RELACIONAMENTO NÃO APARECEM:

1️⃣  NA DATABASE DE CONTATOS:
   • Clique em "Properties" (canto superior direito)
   • Clique em "New property"
   • Nome: Empresas Relacionadas
   • Tipo: Relation
   • Selecione: Database de Clientes (deve aparecer na lista)
   • Clique em "Done"

2️⃣  NA DATABASE DE CLIENTES:
   • Clique em "Properties" (canto superior direito)
   • Clique em "New property"
   • Nome: Contatos Relacionados
   • Tipo: Relation
   • Selecione: Database de Contatos (deve aparecer na lista)
   • Clique em "Done"

🔗 LINKS DIRETOS:
   • Contatos: https://www.notion.so/1b342e659f154daba19863a158d2a96a
   • Clientes: https://www.notion.so/4b5f7e64dc644a4daa53808dc98a303a

💡 DICA:
   Após adicionar os campos, você pode clicar nos relacionamentos
   para navegar entre os registros vinculados!
    """)

if __name__ == "__main__":
    asyncio.run(verificar_campos())
