"""
Script para listar e deletar webhooks do Trello.

Uso:
    python list_webhooks.py          # Lista todos os webhooks
    python list_webhooks.py --delete # Delete todos os webhooks

Após deletar, você pode registrar novamente via painel de configuração.
"""

import sys

import requests
from decouple import config

# Configuração da API do Trello
API_KEY = config("TRELLO_API_KEY", default="")
TOKEN = config("TRELLO_TOKEN", default="")

if not API_KEY or not TOKEN:
    print("❌ Erro: TRELLO_API_KEY e TRELLO_TOKEN devem estar configurados!")
    print("   Configure no arquivo .env ou variáveis de ambiente.")
    sys.exit(1)

BASE_URL = "https://api.trello.com/1"


def list_webhooks() -> list[dict]:
    """Lista todos os webhooks registrados para o token atual."""
    url = f"{BASE_URL}/tokens/{TOKEN}/webhooks"
    params = {"key": API_KEY}

    response = requests.get(url, params=params, timeout=30)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Erro ao listar webhooks: {response.status_code}")
        print(f"   {response.text}")
        return []


def delete_webhook(webhook_id: str) -> bool:
    """Deleta um webhook específico."""
    url = f"{BASE_URL}/webhooks/{webhook_id}"
    params = {"key": API_KEY, "token": TOKEN}

    response = requests.delete(url, params=params, timeout=30)

    return response.status_code in (200, 404)


def main():
    delete_mode = "--delete" in sys.argv

    print("\n" + "=" * 60)
    print("🔍 TRELLO WEBHOOK MANAGER")
    print("=" * 60)

    webhooks = list_webhooks()

    if not webhooks:
        print("\n✅ Nenhum webhook encontrado para este token.")
        return

    print(f"\n📋 Encontrados {len(webhooks)} webhook(s):\n")

    for i, wh in enumerate(webhooks, 1):
        print(f"  {i}. ID: {wh.get('id')}")
        print(f"     Descrição: {wh.get('description', '(sem descrição)')}")
        print(f"     Callback URL: {wh.get('callbackURL', '(sem URL)')}")
        print(f"     Model ID: {wh.get('idModel', '(sem model)')}")
        print(f"     Ativo: {wh.get('active', False)}")
        print()

    if delete_mode:
        print("-" * 60)
        confirm = input("⚠️  Deseja deletar TODOS os webhooks acima? (s/N): ")

        if confirm.lower() in ("s", "sim", "y", "yes"):
            print("\n🗑️  Deletando webhooks...")

            for wh in webhooks:
                wh_id = wh.get("id")
                if delete_webhook(wh_id):
                    print(f"   ✅ Deletado: {wh_id}")
                else:
                    print(f"   ❌ Falha ao deletar: {wh_id}")

            print("\n✅ Limpeza concluída!")
            print("   Agora você pode registrar um novo webhook via painel.")
        else:
            print("\n❌ Operação cancelada.")
    else:
        print("-" * 60)
        print("💡 Para deletar todos os webhooks, execute:")
        print("   python list_webhooks.py --delete")

    print()


if __name__ == "__main__":
    main()
