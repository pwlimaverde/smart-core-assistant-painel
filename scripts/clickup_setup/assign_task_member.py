"""
Script para atribuir/remover/substituir responsáveis (assignees) em uma
tarefa do ClickUp usando o endpoint Update Task (PUT /task/{task_id}).

Este script:
- Obtém detalhes da tarefa e identifica o `list_id`.
- Verifica se o(s) usuário(s) informado(s) têm acesso à List via
  `GET /list/{list_id}/member` (diagnóstico).
- Atualiza responsáveis usando uma das modalidades:
  - replace: substitui a lista completa via `assignees: [ids]`.
  - add: adiciona sem remover via `assignees: {"add": [ids]}`.
  - remove: remove via `assignees: {"rem": [ids]}`.
- Rebusca a tarefa e apresenta um relatório com o resultado.

Observação:
- Defina `CLICKUP_API_TOKEN` no ambiente (use .env). Caso não esteja
  disponível, o script tentará usar `CLICKUP_OAUTH_ACCESS_TOKEN` ou
  `CLICKUP_PERSONAL_TOKEN`. Não compartilhe segredos.
- Se o ClickApp "Multiple Assignees" estiver desativado, apenas o
  último ID informado será mantido.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import requests
from loguru import logger
from rich.console import Console
from rich.table import Table


API_BASE: str = "https://api.clickup.com/api/v2"
console: Console = Console()


def get_env_token() -> str:
    """Obtém o token do ClickUp da variável de ambiente ou do .env.

    Comentário (PT-BR): para evitar falhas quando o CWD não está
    na raiz do projeto, usamos `AutoConfig` com `search_path` apontando
    para a raiz relativa ao arquivo deste script.

    Retorna:
        str: Token da API do ClickUp.

    Levanta:
        ValueError: Caso nenhuma variável de token esteja definida.
    """

    token: str = ""
    try:
        # Tenta usar python-decouple com caminho fixo da raiz do projeto
        from decouple import AutoConfig  # type: ignore

        project_root: Path = Path(__file__).resolve().parents[2]
        config = AutoConfig(search_path=str(project_root))

        # Ordem de busca: CLICKUP_API_TOKEN, depois OAuth ou pessoal
        token = config("CLICKUP_API_TOKEN", default="")
        if not token:
            token = config("CLICKUP_OAUTH_ACCESS_TOKEN", default="")
        if not token:
            token = config("CLICKUP_PERSONAL_TOKEN", default="")
    except Exception:
        # Fallback para variáveis de ambiente do sistema
        token = os.getenv("CLICKUP_API_TOKEN", "")
        if not token:
            token = os.getenv("CLICKUP_OAUTH_ACCESS_TOKEN", "")
        if not token:
            token = os.getenv("CLICKUP_PERSONAL_TOKEN", "")

    if not token:
        raise ValueError(
            "Nenhum token encontrado. Defina uma das variáveis "
            "CLICKUP_API_TOKEN, CLICKUP_OAUTH_ACCESS_TOKEN ou "
            "CLICKUP_PERSONAL_TOKEN no .env ou no sistema."
        )
    return token


def get_task(token: str, task_id: str) -> Dict[str, Any]:
    """Obtém detalhes de uma tarefa.

    Args:
        token: Token de autenticação do ClickUp.
        task_id: ID da tarefa no ClickUp.

    Returns:
        Dict[str, Any]: Dados da tarefa em formato JSON.

    Raises:
        RuntimeError: Em caso de falha na requisição.
    """

    url: str = f"{API_BASE}/task/{task_id}"
    headers: Dict[str, str] = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Falha ao obter tarefa ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def extract_assignees(task: Dict[str, Any]) -> List[int]:
    """Extrai IDs dos responsáveis da tarefa como inteiros.

    Args:
        task: Dicionário com dados da tarefa.

    Returns:
        List[int]: Lista de IDs de usuários responsáveis (inteiros).
    """

    raw = task.get("assignees", [])
    result: List[int] = []
    for item in raw:
        user_id = item.get("id")
        if isinstance(user_id, int):
            result.append(user_id)
        elif isinstance(user_id, str) and user_id.isdigit():
            result.append(int(user_id))
    return result


def extract_list_id(task: Dict[str, Any]) -> Optional[int]:
    """Extrai o ID da List associada à tarefa.

    Args:
        task: Dicionário com dados da tarefa.

    Returns:
        Optional[int]: ID da List ou None se não disponível.
    """

    list_obj = task.get("list")
    if isinstance(list_obj, dict):
        lid = list_obj.get("id")
        if isinstance(lid, int):
            return lid
        if isinstance(lid, str) and lid.isdigit():
            return int(lid)
    return None


def get_list_members(token: str, list_id: int) -> List[int]:
    """Obtém IDs de usuários que têm acesso à List.

    Args:
        token: Token de autenticação do ClickUp.
        list_id: ID da List.

    Returns:
        List[int]: IDs dos membros com acesso à List.
    """

    url: str = f"{API_BASE}/list/{list_id}/member"
    headers: Dict[str, str] = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        logger.warning(
            "Não foi possível obter membros da List "
            f"({resp.status_code})."
        )
        return []
    data: Dict[str, Any] = resp.json()
    members = data.get("members", [])
    ids: List[int] = []
    for m in members:
        # Estruturas variam; tentamos id direto ou user.id
        direct = m.get("id")
        user = m.get("user", {})
        user_id = user.get("id") if isinstance(user, dict) else None
        if isinstance(direct, int):
            ids.append(direct)
        elif isinstance(direct, str) and direct.isdigit():
            ids.append(int(direct))
        elif isinstance(user_id, int):
            ids.append(user_id)
        elif isinstance(user_id, str) and user_id.isdigit():
            ids.append(int(user_id))
    return ids


def put_assignees_add(
    token: str, task_id: str, assignees: List[int]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Adiciona responsáveis usando `assignees: {"add": [...]}`.

    Alguns ambientes exigem IDs como strings.
    """

    url: str = f"{API_BASE}/task/{task_id}"
    headers: Dict[str, str] = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    str_ids: List[str] = [str(x) for x in assignees]
    body: Dict[str, Any] = {"assignees": {"add": str_ids}}
    resp = requests.put(url, json=body, headers=headers, timeout=30)
    ok: bool = 200 <= resp.status_code < 300
    msg: str = (
        "PUT /task (assignees.add) OK" if ok
        else f"PUT falhou: {resp.status_code}"
    )
    data: Dict[str, Any] = {}
    try:
        data = resp.json()
    except Exception:
        data = {}
    if not ok and resp.text:
        msg = f"{msg} - {resp.text}"
    return ok, msg, data


def put_replace_assignees(
    token: str, task_id: str, assignees: List[int]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Substitui a lista de responsáveis via PUT /task/{task_id}.

    Args:
        token: Token do ClickUp.
        task_id: ID da tarefa.
        assignees: Lista final de IDs inteiros.

    Returns:
        Tuple[bool, str, Dict[str, Any]]: Sucesso, mensagem e corpo.
    """

    url: str = f"{API_BASE}/task/{task_id}"
    headers: Dict[str, str] = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    body: Dict[str, Any] = {"assignees": assignees}
    resp = requests.put(url, json=body, headers=headers, timeout=30)
    ok: bool = 200 <= resp.status_code < 300
    msg: str = "PUT /task OK" if ok else f"PUT falhou: {resp.status_code}"
    data: Dict[str, Any] = {}
    try:
        data = resp.json()
    except Exception:
        data = {}
    if not ok and resp.text:
        msg = f"{msg} - {resp.text}"
    return ok, msg, data


def put_replace_assignees_str(
    token: str, task_id: str, assignees: List[int]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Substitui responsáveis enviando IDs como strings.

    Alguns Workspaces/versões da API aceitam apenas strings
    para IDs de usuários. Este fallback converte os IDs.

    Args:
        token: Token do ClickUp.
        task_id: ID da tarefa.
        assignees: Lista final de IDs inteiros.

    Returns:
        Tuple[bool, str, Dict[str, Any]]: Sucesso, mensagem e corpo.
    """

    url: str = f"{API_BASE}/task/{task_id}"
    headers: Dict[str, str] = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    str_ids: List[str] = [str(x) for x in assignees]
    body: Dict[str, Any] = {"assignees": str_ids}
    resp = requests.put(url, json=body, headers=headers, timeout=30)
    ok: bool = 200 <= resp.status_code < 300
    msg: str = (
        "PUT /task (strings) OK" if ok else f"PUT falhou: {resp.status_code}"
    )
    data: Dict[str, Any] = {}
    try:
        data = resp.json()
    except Exception:
        data = {}
    if not ok and resp.text:
        msg = f"{msg} - {resp.text}"
    return ok, msg, data


def put_replace_assignee_single(
    token: str, task_id: str, user_id: int
) -> Tuple[bool, str, Dict[str, Any]]:
    """Define único responsável usando campo singular `assignee`.

    Alguns ambientes aceitam apenas o campo singular na atualização.

    Args:
        token: Token do ClickUp.
        task_id: ID da tarefa.
        user_id: ID do usuário (inteiro).

    Returns:
        Tuple[bool, str, Dict[str, Any]]: Sucesso, mensagem e corpo.
    """

    url: str = f"{API_BASE}/task/{task_id}"
    headers: Dict[str, str] = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    body: Dict[str, Any] = {"assignee": user_id}
    resp = requests.put(url, json=body, headers=headers, timeout=30)
    ok: bool = 200 <= resp.status_code < 300
    msg: str = (
        "PUT /task (assignee) OK" if ok else f"PUT falhou: {resp.status_code}"
    )
    data: Dict[str, Any] = {}
    try:
        data = resp.json()
    except Exception:
        data = {}
    if not ok and resp.text:
        msg = f"{msg} - {resp.text}"
    return ok, msg, data


def put_assignees_rem(
    token: str, task_id: str, assignees: List[int]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Remove responsáveis usando `assignees: {"rem": [...]}`.

    IDs enviados como strings por compatibilidade.
    """

    url: str = f"{API_BASE}/task/{task_id}"
    headers: Dict[str, str] = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    str_ids: List[str] = [str(x) for x in assignees]
    body: Dict[str, Any] = {"assignees": {"rem": str_ids}}
    resp = requests.put(url, json=body, headers=headers, timeout=30)
    ok: bool = 200 <= resp.status_code < 300
    msg: str = (
        "PUT /task (assignees.rem) OK" if ok
        else f"PUT falhou: {resp.status_code}"
    )
    data: Dict[str, Any] = {}
    try:
        data = resp.json()
    except Exception:
        data = {}
    if not ok and resp.text:
        msg = f"{msg} - {resp.text}"
    return ok, msg, data


def render_report(
    task_id: str,
    before: List[int],
    after: List[int],
    list_id: Optional[int],
    in_list: Optional[bool],
    operation: str,
    update_msg: Optional[str],
) -> None:
    """Renderiza relatório no terminal com Rich.

    Args:
        task_id: ID da tarefa.
        before: IDs antes da operação.
        after: IDs depois da operação.
        list_id: ID da List.
        in_list: Se o usuário tem acesso à List.
        operation: Operação executada (replace, add, remove).
        update_msg: Mensagem do Update Task (PUT /task).
    """

    table = Table(title="Diagnóstico de Atribuição de Responsável")
    table.add_column("Campo", style="cyan")
    table.add_column("Valor", style="green")
    table.add_row("Task ID", task_id)
    table.add_row("List ID", str(list_id) if list_id else "-")
    table.add_row("Assignees antes", str(before))
    table.add_row("Assignees depois", str(after))
    if in_list is not None:
        table.add_row("Usuário tem acesso à List", str(in_list))
    table.add_row("Operação", operation)
    if update_msg:
        table.add_row("Update Task", update_msg)
    console.print(table)


def main() -> None:
    """Ponto de entrada do script."""

    parser = argparse.ArgumentParser(
        description=(
            "Atribui um responsável a uma tarefa no ClickUp e "
            "gera diagnóstico detalhado."
        )
    )
    parser.add_argument(
        "--task-id",
        required=True,
        type=str,
        help="ID da tarefa (ex.: 86ad86g4a)",
    )
    parser.add_argument(
        "--user-id",
        required=True,
        type=int,
        help="ID do usuário (inteiro, ex.: 152476517)",
    )
    parser.add_argument(
        "--user-ids",
        required=False,
        type=str,
        help=(
            "IDs de usuários separados por vírgula para operações "
            "em lote (ex.: 123,456)"
        ),
    )
    parser.add_argument(
        "--mode",
        required=False,
        type=str,
        choices=["replace", "add", "remove"],
        default="add",
        help=(
            "Modo de atualização: replace (substitui), add (adiciona), "
            "remove (remove)"
        ),
    )
    parser.add_argument(
        "--token",
        required=False,
        type=str,
        help=(
            "Token da API (opcional; sobrepõe .env se informado)"
        ),
    )
    args = parser.parse_args()

    # Permite sobrepor o token via parâmetro CLI
    token: str = args.token if args.token else get_env_token()
    task: Dict[str, Any] = get_task(token, args.task_id)
    before: List[int] = extract_assignees(task)
    list_id: Optional[int] = extract_list_id(task)

    in_list: Optional[bool] = None
    if list_id is not None:
        members: List[int] = get_list_members(token, list_id)
        in_list = args.user_id in members

    # Determina IDs-alvo conforme CLI
    target_ids: List[int] = []
    if args.user_ids:
        try:
            target_ids = [
                int(x.strip()) for x in args.user_ids.split(",") if x.strip()
            ]
        except Exception:
            raise ValueError(
                "Parâmetro --user-ids inválido. Use CSV de inteiros."
            )
    else:
        target_ids = [args.user_id]

    # Executa operação conforme modo
    operation: str = args.mode
    update_msg: Optional[str] = None
    if operation == "replace":
        # Primeiro tenta com IDs inteiros; se falhar, faz fallback para strings
        ok, msg, _ = put_replace_assignees(token, args.task_id, target_ids)
        if ok:
            update_msg = msg
        else:
            ok2, msg2, _ = put_replace_assignees_str(
                token, args.task_id, target_ids
            )
            update_msg = f"{msg} | fallback(strings): {msg2}"
    elif operation == "add":
        ok, msg, _ = put_assignees_add(token, args.task_id, target_ids)
        update_msg = msg
    else:  # remove
        ok, msg, _ = put_assignees_rem(token, args.task_id, target_ids)
        update_msg = msg

    updated: Dict[str, Any] = get_task(token, args.task_id)
    after: List[int] = extract_assignees(updated)

    render_report(
        task_id=args.task_id,
        before=before,
        after=after,
        list_id=list_id,
        in_list=in_list,
        operation=operation,
        update_msg=update_msg,
    )

    # Confirmação: em replace, todos devem estar; em add/remove, ao menos um
    if operation == "replace":
        assigned_ok: bool = all(uid in after for uid in target_ids)
    else:
        assigned_ok = any(uid in after for uid in target_ids)

    if assigned_ok:
        console.print(
            "[bold green]Atualização confirmada no ClickUp.[/bold green]"
        )
    else:
        console.print(
            "[bold red]Atualização não confirmada. "
            "Verifique acesso dos usuários à List, "
            "o ClickApp 'Multiple Assignees', tipagem dos IDs e o escopo "
            "do token (API pessoal ou OAuth).[/bold red]"
        )


if __name__ == "__main__":
    main()