"""
Script utilitário para trocar o `code` por `access_token` (OAuth).

Este script facilita o fluxo OAuth do ClickUp em ambiente local,
permite colar o `code` recebido no redirect e obter o `access_token`
via `POST /api/v2/oauth/token`.

Requisitos:
- Definir `CLICKUP_CLIENT_ID` e `CLICKUP_CLIENT_SECRET` no `.env`.
- Obter o `code` após autorizar o app no ClickUp.

Comentários em português e tipagem completa.
Linhas com até 79 colunas.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from decouple import config


API_TOKEN_URL: str = "https://api.clickup.com/api/v2/oauth/token"


def exchange_code_for_token(code: str, client_id: str, client_secret: str) -> Dict[str, Any]:
    """Realiza a troca do `code` por `access_token`.

    Args:
        code: Código retornado no redirect da autorização.
        client_id: ID do cliente do app ClickUp.
        client_secret: Segredo do cliente do app ClickUp.

    Returns:
        Dict com o token e metadados retornados pela API.

    Raises:
        RuntimeError: Em casos de erro HTTP ou conexão.
    """
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    }
    data_bytes = json.dumps(payload).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    req = Request(url=API_TOKEN_URL, data=data_bytes, headers=headers, method="POST")

    try:
        with urlopen(req) as resp:
            status_code = resp.getcode()
            raw = resp.read().decode("utf-8")
            parsed: Dict[str, Any] = json.loads(raw) if raw else {}
            parsed["_status"] = status_code
            return parsed
    except HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTPError {e.code} em token: {err_body}") from e
    except URLError as e:
        raise RuntimeError(f"Erro de conexão em token: {e.reason}") from e


def main() -> None:
    """Ponto de entrada: lê `code` e devolve `access_token` na saída."""
    parser = argparse.ArgumentParser(
        description=(
            "Troca o code do OAuth por access_token do ClickUp."
        )
    )
    parser.add_argument(
        "--code",
        type=str,
        required=True,
        help=(
            "Código retornado no redirect (?code=...). Cole aqui para trocar."
        ),
    )
    args = parser.parse_args()

    client_id: str = config("CLICKUP_CLIENT_ID", default="")
    client_secret: str = config("CLICKUP_CLIENT_SECRET", default="")
    if not client_id or not client_secret:
        print(
            "CLICKUP_CLIENT_ID/CLICKUP_CLIENT_SECRET não definidos no .env."
        )
        raise SystemExit(1)

    try:
        res = exchange_code_for_token(args.code, client_id, client_secret)
        status = res.get("_status", "?")
        token = res.get("access_token", "")
        ttype = res.get("token_type", "")
        print(
            f"Troca concluída (status {status}). token_type={ttype}.\n"
            f"access_token={token}"
        )
        if not token:
            print(
                "Nenhum access_token retornado. Verifique se o code é válido."
            )
            raise SystemExit(2)
        print(
            "\nCopie o access_token para o .env em CLICKUP_OAUTH_ACCESS_TOKEN."
        )
    except RuntimeError as err:
        print(f"Falha na troca de token: {err}")
        raise SystemExit(3)


if __name__ == "__main__":
    main()