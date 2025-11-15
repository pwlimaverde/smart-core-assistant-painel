"""Script básico para listar atendentes (membros) no ClickUp.

Este utilitário permite carregar e visualizar os membros do Workspace
(time) e, opcionalmente, os membros com acesso a uma List específica.
Também oferece uma busca por e-mail para validar se o atendente
informado está corretamente visível no ClickUp.

Comentários em Português para explicar a lógica e decisões.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from decouple import config
from loguru import logger
from rich.console import Console
from rich.table import Table

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (  # noqa: E501
    ClicupUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)


def build_service(
    list_id: Optional[str], observability: bool = True
) -> ClicupUnifiedDataService:
    """Inicializa o adapter do ClickUp reutilizando configuração do projeto.

    Observação: credenciais são lidas do .env via `decouple` dentro
    do próprio adapter. Aqui apenas fornecemos parâmetros mínimos da
    interface unificada para ativar logs e definir uma List padrão.
    """
    default_list: str = list_id or config("CLICKUP_DEFAULT_LIST_ID", default="")
    params = UnifieldDataServicesParameters(
        data_source_id=default_list,
        provider="clicup",
        root_container_name="Unified Data Root",
        enable_observability=observability,
        error=UnifieldDataServicesError("Fetch ClickUp members script"),
    )
    return ClicupUnifiedDataService(params)


def normalize_entry(entry: Dict[str, Any]) -> Dict[str, str]:
    """Normaliza um registro de membro retornado pela API.

    Comentário: alguns endpoints retornam `{"user": {...}}` enquanto
    outros já retornam o próprio `user`. Este helper padroniza campos.
    """
    user: Dict[str, Any] = (
        entry.get("user") if isinstance(entry.get("user"), dict) else entry
    )
    return {
        "id": str(user.get("id", "")),
        "username": str(user.get("username", "")),
        "email": str(user.get("email", "")),
        "role": str(user.get("role", "")),
    }


def render_members(title: str, members: List[Dict[str, Any]]) -> None:
    """Renderiza uma tabela com os membros no terminal (Rich)."""
    console = Console()
    table = Table(title=title)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Username", style="green")
    table.add_column("Email", style="magenta")
    table.add_column("Role", style="yellow")

    for raw in members:
        m = normalize_entry(raw)
        table.add_row(m["id"], m["username"], m["email"], m["role"])

    console.print(table)


def main() -> None:
    """Ponto de entrada do script.

    - Lista membros do Workspace (time).
    - Opcionalmente, lista membros da List informada.
    - Permite buscar um e-mail para validação rápida.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Listar membros do ClickUp (Workspace e List opcional)."
        )
    )
    parser.add_argument(
        "--list-id",
        type=str,
        default=config("CLICKUP_DEFAULT_LIST_ID", default=""),
        help=(
            "ID da List para verificar acessos. Se ausente, usa o "
            "valor de CLICKUP_DEFAULT_LIST_ID do .env, se existir."
        ),
    )
    parser.add_argument(
        "--space-name",
        type=str,
        default=config("CLICKUP_APP_ESPACO", default=""),
        help=(
            "Nome do Space onde está a List (ex.: smart core assistant)."
        ),
    )
    parser.add_argument(
        "--folder-name",
        type=str,
        default="",
        help=(
            "Nome do Folder onde está a List (ex.: Comercial)."
        ),
    )
    parser.add_argument(
        "--list-name",
        type=str,
        default="",
        help=(
            "Nome da List (ex.: Atendimento). Usado para resolver o ID"
            " quando --list-id não foi passado."
        ),
    )
    parser.add_argument(
        "--email",
        type=str,
        default="",
        help=(
            "E-mail para buscar o membro diretamente (case-insensitive)."
        ),
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="",
        help=(
            "ID do usuário no ClickUp para verificação direta (ex.: 152476517)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Silencia logs informativos e mostra apenas a tabela.",
    )
    parser.add_argument(
        "--dump-hierarchy",
        action="store_true",
        help=(
            "Imprime Spaces, Folders e Lists disponíveis para facilitar a escolha."
        ),
    )

    args = parser.parse_args()

    # Configura logging conforme preferência do usuário
    if args.quiet:
        logger.remove()

    # Inicializa o serviço
    service = build_service(args.list_id or None, observability=not args.quiet)

    # Opcional: imprimir hierarquia para facilitar identificação
    if args.dump_hierarchy:
        spaces = service.list_spaces()
        console = Console()
        table = Table(title="Spaces → Folders → Lists")
        table.add_column("Space ID", style="cyan", no_wrap=True)
        table.add_column("Space Name", style="green")
        table.add_column("Folder Name", style="magenta")
        table.add_column("List ID", style="yellow")
        table.add_column("List Name", style="white")
        for sp in spaces:
            sid = str(sp.get("id", ""))
            sname = str(sp.get("name", ""))
            try:
                folders = service.list_folders(sid)
            except Exception:
                folders = []
            if not folders:
                table.add_row(sid, sname, "-", "-", "-")
            else:
                for f in folders:
                    fname = str(f.get("name", ""))
                    fid = str(f.get("id", ""))
                    try:
                        lists = service.list_folder_lists(fid)
                    except Exception:
                        lists = []
                    if not lists:
                        table.add_row(sid, sname, fname, "-", "-")
                    else:
                        for lst in lists:
                            table.add_row(
                                sid,
                                sname,
                                fname,
                                str(lst.get("id", "")),
                                str(lst.get("name", "")),
                            )
        console.print(table)

    # Resolver list_id por nomes (Space/Folder/List) se necessário
    resolved_list_id: str = args.list_id
    if not resolved_list_id and args.space_name and args.folder_name and args.list_name:
        try:
            # Comentário: evita `ensure_space_by_name` para não criar recursos.
            spaces = service.list_spaces()
            space = next(
                (s for s in spaces if str(s.get("name", "")) == args.space_name),
                None,
            )
            if not space:
                logger.warning(
                    "Space não encontrado pelo nome: {name}", name=args.space_name
                )
                # Ajuda: listar nomes disponíveis
                disp = ", ".join(str(s.get("name", "")) for s in spaces)
                logger.info("Spaces disponíveis: {names}", names=disp)
            else:
                space_id = str(space.get("id", ""))
                folder = service.find_folder_by_name(space_id, args.folder_name)
                if not folder:
                    logger.warning(
                        "Folder não encontrado em space {space}: {folder}",
                        space=args.space_name,
                        folder=args.folder_name,
                    )
                    try:
                        # Lista folders para ajudar
                        flds = service.list_folders(space_id)
                        dispf = ", ".join(str(f.get("name", "")) for f in flds)
                        logger.info(
                            "Folders disponíveis em {space}: {names}",
                            space=args.space_name,
                            names=dispf,
                        )
                    except Exception:
                        pass
                else:
                    folder_id = str(folder.get("id", ""))
                    lst = service.find_list_in_folder_by_name(folder_id, args.list_name)
                    if lst:
                        resolved_list_id = str(lst.get("id", ""))
                        logger.info(
                            "List resolvida por nome: {name} -> {id}",
                            name=args.list_name,
                            id=resolved_list_id,
                        )
                    else:
                        logger.warning(
                            "List '{list}' não encontrada em folder '{folder}'",
                            list=args.list_name,
                            folder=args.folder_name,
                        )
                        try:
                            lists = service.list_folder_lists(folder_id)
                            displ = ", ".join(str(l.get("name", "")) for l in lists)
                            logger.info(
                                "Lists disponíveis em {folder}: {names}",
                                folder=args.folder_name,
                                names=displ,
                            )
                        except Exception:
                            pass
        except Exception as exc:
            logger.error(
                "Falha ao resolver list por nomes: {err}", err=str(exc)
            )

    # Lista usuários do Workspace
    workspace_members: List[Dict[str, Any]] = service.list_team_members()
    render_members("Workspace members (team)", workspace_members)

    # Lista usuários com acesso à List (quando fornecida)
    list_id_for_members: Optional[str] = resolved_list_id or None
    if list_id_for_members:
        list_members: List[Dict[str, Any]] = service.list_list_members(
            list_id_for_members
        )
        render_members(
            f"List members (list_id={list_id_for_members})", list_members
        )

    # Busca direta por e-mail para validação
    email: str = args.email.strip()
    if email:
        # Preferir escopo de List quando informado
        member = service.find_member_by_email(email, list_id_for_members)
        if member:
            m = normalize_entry(member)
            logger.info(
                "Membro encontrado: id={id} username={user} email={email}",
                id=m["id"],
                user=m["username"],
                email=m["email"],
            )
        else:
            logger.warning(
                "Nenhum membro com e-mail '{email}' no escopo consultado.",
                email=email,
            )

    # Verificação direta por user-id
    user_id: str = args.user_id.strip()
    if user_id and list_id_for_members:
        members = service.list_list_members(list_id_for_members)
        found = False
        for raw in members:
            m = normalize_entry(raw)
            if m["id"] == user_id:
                found = True
                logger.info(
                    "User ID presente na List: id={id} username={user} email={email}",
                    id=m["id"],
                    user=m["username"],
                    email=m["email"],
                )
                break
        if not found:
            logger.warning(
                "User ID {id} não foi encontrado em list_id={list}",
                id=user_id,
                list=list_id_for_members,
            )


if __name__ == "__main__":
    main()