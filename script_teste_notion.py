import os
import asyncio
from dotenv import load_dotenv
from notion_py_client import NotionAsyncClient

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

if not NOTION_TOKEN or not NOTION_PAGE_ID:
    raise SystemExit("Defina NOTION_TOKEN e NOTION_PAGE_ID no .env")

async def create_contato_db(notion_token: str, parent_page_id: str):
    async with NotionAsyncClient(auth=notion_token) as client:
        parameters = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "Contato"}}],
            # ← Aqui: propriedades dentro de initial_data_source (obrigatório na API 2025-09-03)
            "initial_data_source": {
                "name": "Contato",
                "properties": {
                    "nome": {"name": "nome", "type": "title", "title": {}},
                    "telefone": {"name": "telefone", "type": "phone_number", "phone_number": {}},
                    "endereço": {"name": "endereço", "type": "rich_text", "rich_text": {}}
                }
            }
        }

        created = await client.databases.create(parameters)  # a lib aceita o payload posicional
        print("✅ Criada:", created)
        print("id:", getattr(created, "id", None) or (created.get("id") if isinstance(created, dict) else None))
        return created

if __name__ == "__main__":
    asyncio.run(create_contato_db(NOTION_TOKEN, NOTION_PAGE_ID))
