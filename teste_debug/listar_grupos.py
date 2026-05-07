import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente baseadas no .env que está nesta mesma pasta
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Lê as credenciais
EVO_URL = os.getenv("EVO_URL", "")
EVO_API_KEY = os.getenv("EVO_API_KEY", "")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "")

if not EVO_URL or not EVO_API_KEY or not INSTANCE_NAME:
    print(
        "ERRO: Configure EVO_URL, EVO_API_KEY e INSTANCE_NAME no arquivo .env (veja o .env.example)."
    )
    exit(1)

headers = {"apikey": EVO_API_KEY, "Content-Type": "application/json"}


def listar_grupos():
    url = (
        f"{EVO_URL}/group/fetchAllGroups/{INSTANCE_NAME}?getParticipants=false"
    )
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        groups = response.json()

        print(
            "\n=== Selecione um ID abaixo e copie para a variável ID_GRUPO no .env ===\n"
        )

        for group in groups:
            # Em algumas versões da API, o nome do grupo vem em 'subject' ou 'name'
            name = group.get("subject", group.get("name", "Desconhecido"))
            group_id = group.get("id")
            print(f"- Nome: {name} | ID: {group_id}")

    except Exception as e:
        print(f"Erro ao buscar grupos: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Detalhes do erro: {e.response.text}")


if __name__ == "__main__":
    print(f"Conectando à Evolution API em: {EVO_URL}")
    print(f"Instância conectada: {INSTANCE_NAME}")
    listar_grupos()
