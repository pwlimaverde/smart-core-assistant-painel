import os
import notion_client
from dotenv import load_dotenv
from notion_client.errors import APIResponseError

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Pega as credenciais do ambiente
notion_token = os.getenv("NOTION_TOKEN")
page_id = os.getenv("NOTION_PAGE_ID")

# Verifica se as variáveis foram carregadas corretamente
if not notion_token or not page_id:
    print(
        "Erro: As variáveis de ambiente NOTION_TOKEN e NOTION_PAGE_ID devem ser definidas."
    )
    exit()

# Inicializa o cliente do Notion
notion = notion_client.Client(auth=notion_token)

# Define o título e as propriedades do novo banco de dados
db_title = "Contato"

# --- CORREÇÃO APLICADA ---
# Removendo o caractere especial 'ç' do nome da propriedade para teste.
db_properties = {
    "Name": {"title": {}},
    "Telefone": {"phone_number": {}},
    "Endereco": {  # Alterado de "Endereço" para "Endereco"
        "rich_text": {}
    },
}
# -------------------------

print(f"Criando o banco de dados '{db_title}' na página com ID: {page_id}...")

try:
    # Cria o banco de dados usando a API
    new_database = notion.databases.create(
        parent={"type": "page_id", "page_id": page_id},
        title=[{"type": "text", "text": {"content": db_title}}],
        properties=db_properties,
    )

    # Imprime uma mensagem de sucesso com a URL do novo banco de dados
    print("\nBanco de dados criado com sucesso!")
    print(f"URL: {new_database['url']}")

except APIResponseError as error:
    # Imprime uma mensagem de erro caso algo dê errado
    print(f"\nOcorreu um erro ao criar o banco de dados: {error}")
