"""Ferramenta de diagnóstico de webhooks do Trello.

Objetivo:
- Listar webhooks cadastrados no token.
- Listar boards do Workspace (Organization).
- Garantir webhook POR BOARD apontando para o endpoint do tenant.

Por que isso é necessário:
- Movimentações de cards/listas (ex.: updateCard) chegam via webhooks do *Board*.
- Um webhook no Workspace/Organization geralmente não recebe eventos de cards/listas.

Uso (no root do repo):
  uv run python scripts/trello/trello_webhook_diagnose.py list-webhooks
  uv run python scripts/trello/trello_webhook_diagnose.py list-boards --workspace-id <ID>
  uv run python scripts/trello/trello_webhook_diagnose.py ensure-board-webhook --board-id <ID> --tenant-slug paulo-ecoprint --callback-base https://paulo-ecoprint.smartcoreassistant.com.br
  uv run python scripts/trello/trello_webhook_diagnose.py ensure-workspace-boards --workspace-id <ID> --tenant-slug paulo-ecoprint --callback-base https://paulo-ecoprint.smartcoreassistant.com.br

Credenciais:
- Por segurança, NUNCA hardcode. Este script lê do ambiente (.env) via python-decouple:
  TRELLO_API_KEY, TRELLO_TOKEN
Opcional:
  TRELLO_WORKSPACE_ID (para comandos que listam/garantem por workspace)
  TRELLO_WEBHOOK_CALLBACK_URL (base URL, ex.: https://paulo-ecoprint.smartcoreassistant.com.br)
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
from dataclasses import dataclass
from typing import Any, Iterable

import requests
from decouple import config

API_BASE = "https://api.trello.com/1"


def _require_env(name: str) -> str:
    value = config(name, default="").strip()
    if not value:
        raise SystemExit(f"Variável obrigatória ausente: {name}")
    return value


def _redact(value: str, keep: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}...{value[-keep:]}"


def _callback_url(callback_base: str, tenant_slug: str) -> str:
    base = callback_base.rstrip("/")
    return f"{base}/api/trello_sync/webhook/{tenant_slug}/"


def _http(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout_s: int = 20,
) -> Any:
    resp = requests.request(
        method,
        url,
        params=params,
        json=json_body,
        timeout=timeout_s,
    )
    if not resp.ok:
        text = resp.text or ""
        raise RuntimeError(
            f"{method} {url} -> {resp.status_code}: {text[:400]}"
        )
    if not resp.text:
        return None
    try:
        return resp.json()
    except Exception:
        return resp.text


def trello_get(
    path: str, *, api_key: str, token: str, params: dict[str, Any] | None = None
) -> Any:
    qp = dict(params or {})
    qp["key"] = api_key
    qp["token"] = token
    return _http("GET", f"{API_BASE}{path}", params=qp)


def trello_post_token_webhook(
    *,
    api_key: str,
    token: str,
    callback_url: str,
    model_id: str,
    description: str,
) -> dict[str, Any]:
    url = f"{API_BASE}/tokens/{token}/webhooks/"
    payload = {
        "key": api_key,
        "callbackURL": callback_url,
        "idModel": model_id,
        "description": description,
    }
    data = _http("POST", url, json_body=payload)
    if not isinstance(data, dict):
        raise RuntimeError("Resposta inesperada ao criar webhook no Trello.")
    return data


@dataclass(frozen=True)
class TrelloWebhook:
    webhook_id: str
    active: bool
    callback_url: str
    id_model: str
    description: str


def list_webhooks(*, api_key: str, token: str) -> list[TrelloWebhook]:
    items = trello_get(f"/tokens/{token}/webhooks", api_key=api_key, token=token)
    if not isinstance(items, list):
        return []
    out: list[TrelloWebhook] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        out.append(
            TrelloWebhook(
                webhook_id=str(it.get("id", "")),
                active=bool(it.get("active", False)),
                callback_url=str(it.get("callbackURL", "")),
                id_model=str(it.get("idModel", "")),
                description=str(it.get("description", "")),
            )
        )
    return out


def list_workspace_boards(
    *, api_key: str, token: str, workspace_id: str
) -> list[dict[str, Any]]:
    boards = trello_get(
        f"/organizations/{workspace_id}/boards",
        api_key=api_key,
        token=token,
        params={"fields": "name,url,closed,idOrganization"},
    )
    if not isinstance(boards, list):
        return []
    # Normaliza apenas dicts
    return [b for b in boards if isinstance(b, dict)]


def list_my_boards(*, api_key: str, token: str) -> list[dict[str, Any]]:
    boards = trello_get(
        "/members/me/boards",
        api_key=api_key,
        token=token,
        params={"fields": "name,url,closed,idOrganization"},
    )
    if not isinstance(boards, list):
        return []
    return [b for b in boards if isinstance(b, dict)]


def resolve_board(
    *, api_key: str, token: str, board_identifier: str
) -> dict[str, Any]:
    """Resolve um board por ID ou shortLink e retorna dados básicos."""
    data = trello_get(
        f"/boards/{board_identifier}",
        api_key=api_key,
        token=token,
        params={"fields": "name,url,closed,idOrganization"},
    )
    if not isinstance(data, dict):
        raise RuntimeError("Resposta inesperada ao resolver board.")
    return data


def _extract_board_identifier(value: str) -> str:
    """Aceita:
    - ID do board (24 chars) ou shortLink (8 chars)
    - URL do Trello (https://trello.com/b/<shortLink>/...)
    """
    raw = value.strip()
    if not raw:
        return ""

    # Se parece URL, tenta extrair /b/<shortLink>/
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urllib.parse.urlparse(raw)
        path = parsed.path or ""
        parts = [p for p in path.split("/") if p]
        # Ex.: ["b", "<shortLink>", "nome-do-board"]
        if len(parts) >= 2 and parts[0] == "b":
            return parts[1]
        return ""

    # Caso contrário, assume que já é identificador (id ou shortLink)
    return raw


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_list_webhooks(args: argparse.Namespace) -> int:
    api_key = _require_env("TRELLO_API_KEY")
    token = _require_env("TRELLO_TOKEN")
    workspace_id = config("TRELLO_WORKSPACE_ID", default="").strip()

    print("Trello credentials:")
    print(f"- TRELLO_API_KEY={_redact(api_key)}")
    print(f"- TRELLO_TOKEN={_redact(token)}")
    if workspace_id:
        print(f"- TRELLO_WORKSPACE_ID={workspace_id}")
    print()

    hooks = list_webhooks(api_key=api_key, token=token)
    print(f"Webhooks encontrados: {len(hooks)}")
    for h in hooks:
        print(
            f"- id={h.webhook_id} active={h.active} idModel={h.id_model} "
            f"callbackURL={h.callback_url} desc={h.description}"
        )
        if workspace_id and h.id_model == workspace_id:
            print(
                "  AVISO: este webhook está no Workspace/Organization (idModel=workspace). "
                "Movimentação de cards/listas pode NÃO chegar por aqui; use webhook por Board."
            )
        if "ngrok" in (h.callback_url or ""):
            print(
                "  AVISO: callbackURL parece ser ngrok. Se você migrou para produção, "
                "provavelmente precisa remover e recriar apontando para o domínio final."
            )
    return 0


def cmd_list_boards(args: argparse.Namespace) -> int:
    api_key = _require_env("TRELLO_API_KEY")
    token = _require_env("TRELLO_TOKEN")
    workspace_id = (args.workspace_id or config("TRELLO_WORKSPACE_ID", default="")).strip()
    if not workspace_id:
        raise SystemExit("Informe --workspace-id ou defina TRELLO_WORKSPACE_ID.")

    boards = list_workspace_boards(
        api_key=api_key, token=token, workspace_id=workspace_id
    )
    if args.json:
        _print_json(boards)
        return 0

    print(f"Boards no workspace {workspace_id}: {len(boards)}")
    for b in boards:
        board_id = str(b.get("id", ""))
        name = str(b.get("name", ""))
        url = str(b.get("url", ""))
        closed = bool(b.get("closed", False))
        status = "CLOSED" if closed else "OPEN"
        print(f"- {status} id={board_id} name={name} url={url}")
    return 0


def cmd_list_my_boards(args: argparse.Namespace) -> int:
    api_key = _require_env("TRELLO_API_KEY")
    token = _require_env("TRELLO_TOKEN")
    boards = list_my_boards(api_key=api_key, token=token)

    q = (args.query or "").strip().lower()
    if q:
        boards = [
            b
            for b in boards
            if q in str(b.get("name", "")).lower()
            or q in str(b.get("url", "")).lower()
        ]

    if args.json:
        _print_json(boards)
        return 0

    print(f"Boards acessíveis pelo token: {len(boards)}")
    for b in boards:
        board_id = str(b.get("id", ""))
        name = str(b.get("name", ""))
        url = str(b.get("url", ""))
        closed = bool(b.get("closed", False))
        org_id = str(b.get("idOrganization", "") or "")
        status = "CLOSED" if closed else "OPEN"
        org_txt = f" org={org_id}" if org_id else ""
        print(f"- {status} id={board_id}{org_txt} name={name} url={url}")
    return 0


def _ensure_board_webhook(
    *,
    api_key: str,
    token: str,
    board_id: str,
    callback_url: str,
    description: str,
    dry_run: bool,
) -> str:
    hooks = list_webhooks(api_key=api_key, token=token)
    for h in hooks:
        if h.id_model == board_id and h.callback_url.rstrip("/") == callback_url.rstrip("/"):
            return h.webhook_id

    if dry_run:
        print(
            "DRY-RUN: webhook não existe; criaria agora com:"
            f" idModel={board_id} callbackURL={callback_url}"
        )
        return ""

    created = trello_post_token_webhook(
        api_key=api_key,
        token=token,
        callback_url=callback_url,
        model_id=board_id,
        description=description,
    )
    webhook_id = str(created.get("id", ""))
    if not webhook_id:
        raise RuntimeError(f"Webhook criado mas sem id na resposta: {created}")
    return webhook_id


def cmd_ensure_board_webhook(args: argparse.Namespace) -> int:
    api_key = _require_env("TRELLO_API_KEY")
    token = _require_env("TRELLO_TOKEN")
    tenant_slug = args.tenant_slug.strip()
    callback_base = (
        args.callback_base
        or config("TRELLO_WEBHOOK_CALLBACK_URL", default="").strip()
    )
    if not callback_base:
        raise SystemExit(
            "Informe --callback-base (ex.: https://paulo-ecoprint.smartcoreassistant.com.br) "
            "ou defina TRELLO_WEBHOOK_CALLBACK_URL."
        )

    cb_url = _callback_url(callback_base, tenant_slug)
    board_id = args.board_id.strip()
    if not board_id:
        raise SystemExit("Informe --board-id.")

    # Verifica se o endpoint responde HEAD 200 (pré-requisito do Trello).
    try:
        head = requests.head(cb_url, timeout=10)
        print(f"HEAD {cb_url} -> {head.status_code}")
    except Exception as exc:
        print(f"Falha no HEAD do callback: {exc}")

    webhook_id = _ensure_board_webhook(
        api_key=api_key,
        token=token,
        board_id=board_id,
        callback_url=cb_url,
        description=f"Smart Assistant Webhook (Board) - {tenant_slug}",
        dry_run=args.dry_run,
    )
    if webhook_id:
        print(f"OK: webhook por Board garantido. webhook_id={webhook_id}")
    else:
        print("OK (dry-run).")
    return 0


def cmd_ensure_workspace_boards(args: argparse.Namespace) -> int:
    api_key = _require_env("TRELLO_API_KEY")
    token = _require_env("TRELLO_TOKEN")
    workspace_id = (args.workspace_id or config("TRELLO_WORKSPACE_ID", default="")).strip()
    if not workspace_id:
        raise SystemExit("Informe --workspace-id ou defina TRELLO_WORKSPACE_ID.")

    tenant_slug = args.tenant_slug.strip()
    callback_base = (
        args.callback_base
        or config("TRELLO_WEBHOOK_CALLBACK_URL", default="").strip()
    )
    if not callback_base:
        raise SystemExit(
            "Informe --callback-base (ex.: https://paulo-ecoprint.smartcoreassistant.com.br) "
            "ou defina TRELLO_WEBHOOK_CALLBACK_URL."
        )

    cb_url = _callback_url(callback_base, tenant_slug)
    boards = list_workspace_boards(
        api_key=api_key, token=token, workspace_id=workspace_id
    )

    # Opcional: filtra boards fechados
    if not args.include_closed:
        boards = [b for b in boards if not bool(b.get("closed", False))]

    limit = int(args.limit) if args.limit else 0
    if limit > 0:
        boards = boards[:limit]

    print(
        f"Workspace {workspace_id}: garantindo webhooks por Board em {len(boards)} boards "
        f"(include_closed={args.include_closed}, dry_run={args.dry_run})"
    )
    print(f"callbackURL alvo: {cb_url}")

    ok = 0
    for b in boards:
        board_id = str(b.get("id", "")).strip()
        name = str(b.get("name", "")).strip()
        if not board_id:
            continue
        try:
            webhook_id = _ensure_board_webhook(
                api_key=api_key,
                token=token,
                board_id=board_id,
                callback_url=cb_url,
                description=f"Smart Assistant Webhook (Board) - {tenant_slug} - {name}",
                dry_run=args.dry_run,
            )
            ok += 1
            status = "OK" if webhook_id else "DRY-RUN"
            print(f"- {status} board={board_id} name={name} webhook_id={webhook_id}")
        except Exception as exc:
            print(f"- ERRO board={board_id} name={name}: {exc}")

    print(f"Concluído. Boards processados com sucesso: {ok}/{len(boards)}")
    return 0


def cmd_resolve_board(args: argparse.Namespace) -> int:
    api_key = _require_env("TRELLO_API_KEY")
    token = _require_env("TRELLO_TOKEN")
    ident = _extract_board_identifier(args.value)
    if not ident:
        raise SystemExit(
            "Informe um ID/shortLink de board ou uma URL do Trello no formato "
            "https://trello.com/b/<shortLink>/..."
        )

    board = resolve_board(api_key=api_key, token=token, board_identifier=ident)
    # Normaliza saída para facilitar copiar o ID
    out = {
        "id": board.get("id"),
        "name": board.get("name"),
        "url": board.get("url"),
        "closed": board.get("closed"),
        "idOrganization": board.get("idOrganization"),
    }
    _print_json(out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trello_webhook_diagnose",
        description="Diagnóstico e correção (manual) de webhooks do Trello.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list-webhooks", help="Lista webhooks do token.")
    p_list.set_defaults(func=cmd_list_webhooks)

    p_boards = sub.add_parser(
        "list-boards", help="Lista boards do Workspace (Organization)."
    )
    p_boards.add_argument("--workspace-id", default="", help="ID do workspace.")
    p_boards.add_argument(
        "--json", action="store_true", help="Imprime JSON bruto."
    )
    p_boards.set_defaults(func=cmd_list_boards)

    p_my_boards = sub.add_parser(
        "list-my-boards",
        help="Lista boards acessíveis pelo token (inclui boards fora do workspace).",
    )
    p_my_boards.add_argument(
        "--query",
        default="",
        help="Filtra por substring no nome ou URL (case-insensitive).",
    )
    p_my_boards.add_argument(
        "--json", action="store_true", help="Imprime JSON bruto."
    )
    p_my_boards.set_defaults(func=cmd_list_my_boards)

    p_resolve = sub.add_parser(
        "resolve-board",
        help="Resolve um board por URL/shortLink e imprime o ID real do board.",
    )
    p_resolve.add_argument(
        "value",
        help="URL do board (trello.com/b/...) ou identificador (id/shortLink).",
    )
    p_resolve.set_defaults(func=cmd_resolve_board)

    p_ensure_board = sub.add_parser(
        "ensure-board-webhook",
        help="Garante um webhook por Board (idModel=board_id).",
    )
    p_ensure_board.add_argument("--board-id", required=True, help="ID do board.")
    p_ensure_board.add_argument(
        "--tenant-slug", required=True, help="Slug do tenant (ex.: paulo-ecoprint)."
    )
    p_ensure_board.add_argument(
        "--callback-base",
        default="",
        help="Base pública do sistema (ex.: https://paulo-ecoprint.smartcoreassistant.com.br).",
    )
    p_ensure_board.add_argument(
        "--dry-run", action="store_true", help="Não cria, apenas simula."
    )
    p_ensure_board.set_defaults(func=cmd_ensure_board_webhook)

    p_ensure_ws = sub.add_parser(
        "ensure-workspace-boards",
        help="Garante webhooks por Board para todos os boards do Workspace.",
    )
    p_ensure_ws.add_argument("--workspace-id", default="", help="ID do workspace.")
    p_ensure_ws.add_argument(
        "--tenant-slug", required=True, help="Slug do tenant."
    )
    p_ensure_ws.add_argument(
        "--callback-base",
        default="",
        help="Base pública do sistema (ex.: https://paulo-ecoprint.smartcoreassistant.com.br).",
    )
    p_ensure_ws.add_argument(
        "--include-closed",
        action="store_true",
        help="Inclui boards fechados.",
    )
    p_ensure_ws.add_argument(
        "--limit",
        default="",
        help="Limita a quantidade de boards processados (ex.: 10).",
    )
    p_ensure_ws.add_argument(
        "--dry-run", action="store_true", help="Não cria, apenas simula."
    )
    p_ensure_ws.set_defaults(func=cmd_ensure_workspace_boards)

    return p


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    fn = getattr(args, "func", None)
    if not fn:
        parser.print_help()
        return 2
    return int(fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
