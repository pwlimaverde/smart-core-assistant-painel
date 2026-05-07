import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis de ambiente baseadas no .env que está nesta mesma pasta
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Lê as credenciais
EVO_URL = os.getenv("EVO_URL", "")
EVO_API_KEY = os.getenv("EVO_API_KEY", "")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "")
ID_GRUPO = os.getenv("ID_GRUPO", "")

if not EVO_URL or not EVO_API_KEY or not INSTANCE_NAME or not ID_GRUPO:
    print(
        "ERRO: Verifique se EVO_URL, EVO_API_KEY, INSTANCE_NAME e ID_GRUPO estão no .env!"
    )
    exit(1)

headers = {"apikey": EVO_API_KEY, "Content-Type": "application/json"}


def enviar_mensagem_grupo(mensagem):
    url = f"{EVO_URL}/message/sendText/{INSTANCE_NAME}"
    payload = {"number": ID_GRUPO, "text": mensagem, "delay": 1200}
    try:
        print(f"\nEnviando mensagem para {ID_GRUPO}...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("Mensagem enviada com sucesso!")
        print("Retorno da API:")
        print(response.json())
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Detalhes do erro: {e.response.text}")


if __name__ == "__main__":
    print(f"Preparando envio pela instância: {INSTANCE_NAME}")

    texto_mensagem = "✅ Olá! Teste de integração do sistema Smart Core Assistant passando com sucesso."
    enviar_mensagem_grupo(texto_mensagem)
