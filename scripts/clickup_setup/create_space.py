"""
Script simples para criar um Space no ClickUp.

Este script lê variáveis de ambiente e faz uma chamada à API
`POST /api/v2/team/{team_id}/space` para criar um Space com o nome
informado (padrão: "smart-core-assistant").

Requisitos:
- Definir `CLICKUP_PERSONAL_TOKEN` no `.env` (token começa com `pk_`).
- Opcional: definir `CLICKUP_TEAM_ID`. Se vazio, o script obtém o
  primeiro Workspace acessível via `GET /api/v2/team`.

Comentários em português, tipagem completa e linhas ≤79 colunas.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from decouple import config


API_BASE_V2: str = "https://api.clickup.com/api/v2"


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Obtém valor de configuração do `.env`/ambiente.

    Usa `python-decouple` para ler primeiro do `.env` e, na ausência,
    do ambiente do sistema.

    Args:
        key: Nome da variável.
        default: Valor padrão se não existir.

    Returns:
        Valor da variável ou default.
    """
    value: str = config(key, default=default or "")
    return value if value != "" else default


def build_auth_value(token: str) -> str:
    """Constrói valor de Authorization conforme tipo de token.

    Se o token for pessoal (prefixo `pk_`), usa-o diretamente.
    Caso contrário, assume OAuth e prefixa com `Bearer`.

    Args:
        token: Token do ClickUp.

    Returns:
        Valor para cabeçalho Authorization.
    """
    if token.startswith("pk_"):
        return token
    return f"Bearer {token}"


def http_request(
    method: str,
    url: str,
    token: str,
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Executa requisição HTTP simples com `urllib`.

    Args:
        method: Método HTTP (GET, POST, PUT).
        url: URL da API.
        token: Token do ClickUp.
        body: Corpo JSON opcional.

    Returns:
        Resposta decodificada em dict.

    Raises:
        RuntimeError: Em erros HTTP/Conexão.
    """
    data_bytes: Optional[bytes] = None
    if body is not None:
        data_bytes = json.dumps(body).encode("utf-8")

    headers = {
        "Authorization": build_auth_value(token),
        "Content-Type": "application/json",
    }

    req = Request(url=url, data=data_bytes, headers=headers, method=method)

    try:
        with urlopen(req) as resp:
            status_code = resp.getcode()
            raw = resp.read().decode("utf-8")
            parsed: Dict[str, Any] = json.loads(raw) if raw else {}
            parsed["_status"] = status_code
            return parsed
    except HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(
            f"HTTPError {e.code} em {url}: {err_body}"
        ) from e
    except URLError as e:
        raise RuntimeError(f"Erro de conexão em {url}: {e.reason}") from e


def get_team_id(token: str, env_team_id: Optional[str]) -> str:
    """Obtém `team_id` via env ou API.

    Args:
        token: Token do ClickUp.
        env_team_id: Valor vindo da variável `CLICKUP_TEAM_ID`.

    Returns:
        ID do Workspace (team).

    Raises:
        RuntimeError: Se nenhum Workspace for encontrado.
    """
    if env_team_id and env_team_id.strip():
        return env_team_id.strip()

    url = f"{API_BASE_V2}/team"
    resp = http_request("GET", url, token)
    teams = resp.get("teams", [])
    if not teams:
        raise RuntimeError("Nenhum Workspace disponível para o token." )

    first = teams[0]
    team_id = str(first.get("id"))
    if not team_id:
        raise RuntimeError("Workspace sem ID válido retornado pela API.")
    return team_id


def create_space(team_id: str, name: str, token: str) -> Dict[str, Any]:
    """Cria um Space no Workspace informado.

    Args:
        team_id: ID do Workspace (team).
        name: Nome do Space a ser criado.
        token: Token do ClickUp.

    Returns:
        Dict com dados do Space criado.
    """
    url = f"{API_BASE_V2}/team/{team_id}/space"
    payload = {"name": name}
    return http_request("POST", url, token, payload)


def main() -> None:
    """Ponto de entrada do script.

    Lê variáveis de ambiente e cria um Space no ClickUp.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Cria um Space no ClickUp (padrão: smart-core-assistant)."
        )
    )
    parser.add_argument(
        "--name",
        type=str,
        default="smart-core-assistant",
        help="Nome do Space a ser criado.",
    )
    args = parser.parse_args()

    # Aceita token pessoal (pk_...) ou token OAuth (Bearer).
    token = get_env("CLICKUP_PERSONAL_TOKEN") or get_env(
        "CLICKUP_OAUTH_ACCESS_TOKEN"
    )
    if not token:
        msg = (
            "Token do ClickUp não encontrado. Defina "
            "CLICKUP_PERSONAL_TOKEN (pk_...) ou CLICKUP_OAUTH_ACCESS_TOKEN."
        )
        print(msg)
        sys.exit(1)

    env_team_id = get_env("CLICKUP_TEAM_ID")
    try:
        team_id = get_team_id(token, env_team_id)
        created = create_space(team_id, args.name, token)
        space_name = created.get("name", args.name)
        space_id = created.get("id", "")
        status = created.get("_status", "?")
        print(
            (
                f"Space criado com sucesso (status {status}): "
                f"id={space_id}, name={space_name}"
            )
        )
    except RuntimeError as err:
        print(f"Falha ao criar Space: {err}")
        sys.exit(2)


if __name__ == "__main__":
    main()