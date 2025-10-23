"""
Script para inspecionar database criado no Notion.

Este script permite verificar detalhadamente um database no Notion,
mostrando todas as propriedades, configurações e estrutura retornada
pela API.

Para executar:
    python inspect_database_created.py

Requisitos:
    - NOTION_TOKEN configurado no .env
    - ID do database a ser inspecionado
"""

import json
import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Configura o Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)

import django

django.setup()

from decouple import config
from notion_client import Client
from notion_client.errors import APIResponseError
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


def get_notion_client() -> Client:
    """
    Obtém cliente do Notion configurado.

    Returns:
        Cliente do Notion autenticado.

    Raises:
        SystemExit: Se token não estiver configurado.
    """
    token = config("NOTION_TOKEN", default=None)
    if not token:
        console.print(
            "\n[bold red]ERRO: NOTION_TOKEN não encontrado no .env[/bold red]"
        )
        console.print("Configure a variável NOTION_TOKEN no arquivo .env")
        sys.exit(1)

    return Client(auth=token)


def inspect_database(client: Client, database_id: str) -> None:
    """
    Inspeciona um database no Notion e mostra todas as informações.

    Args:
        client: Cliente do Notion.
        database_id: ID do database a inspecionar.
    """
    console.print(f"\n[yellow]→ Inspecionando database: {database_id}[/yellow]\n")

    try:
        # Busca informações do database
        database = client.databases.retrieve(database_id=database_id)

        # Título
        title_obj = database.get("title", [])
        if title_obj:
            title_text = "".join(
                item.get("plain_text", "") for item in title_obj
            )
        else:
            title_text = "Sem título"

        console.print(f"[bold cyan]Título:[/bold cyan] {title_text}")
        console.print(f"[bold cyan]ID:[/bold cyan] {database_id}")
        console.print(f"[bold cyan]Created:[/bold cyan] {database.get('created_time', 'N/A')}")
        console.print(f"[bold cyan]Updated:[/bold cyan] {database.get('last_edited_time', 'N/A')}")

        # Propriedades
        console.print("\n[bold cyan]═══ PROPRIEDADES ═══[/bold cyan]\n")
        properties = database.get("properties", {})

        if not properties:
            console.print("[red]✗ Nenhuma propriedade encontrada![/red]")
            console.print("[yellow]Isso indica que o database está vazio[/yellow]")
        else:
            console.print(f"[green]✓ {len(properties)} propriedades encontradas:[/green]\n")

            # Cria tabela de propriedades
            table = Table(show_header=True, title="Propriedades do Database")
            table.add_column("Nome", style="cyan", width=30)
            table.add_column("Tipo", style="green", width=20)
            table.add_column("Detalhes", style="yellow")

            for prop_name, prop_config in properties.items():
                prop_type = prop_config.get("type", "unknown")
                prop_id = prop_config.get("id", "N/A")

                # Detalhes adicionais baseado no tipo
                details = []
                if prop_type == "select" and "select" in prop_config:
                    options = prop_config["select"].get("options", [])
                    details.append(f"{len(options)} opções")
                elif prop_type == "multi_select" and "multi_select" in prop_config:
                    options = prop_config["multi_select"].get("options", [])
                    details.append(f"{len(options)} opções")
                elif prop_type == "number" and "number" in prop_config:
                    format_type = prop_config["number"].get("format", "number")
                    details.append(f"format: {format_type}")

                details.append(f"id: {prop_id[:8]}...")
                details_text = ", ".join(details)

                table.add_row(prop_name, prop_type, details_text)

            console.print(table)

        # Parent
        console.print("\n[bold cyan]═══ PARENT ═══[/bold cyan]\n")
        parent = database.get("parent", {})
        parent_type = parent.get("type", "unknown")
        console.print(f"[cyan]Tipo:[/cyan] {parent_type}")
        if parent_type == "page_id":
            console.print(f"[cyan]Page ID:[/cyan] {parent.get('page_id', 'N/A')}")
        elif parent_type == "workspace":
            console.print(f"[cyan]Workspace:[/cyan] {parent.get('workspace', 'N/A')}")

        # URL
        console.print("\n[bold cyan]═══ ACESSO ═══[/bold cyan]\n")
        url = database.get("url", "N/A")
        console.print(f"[cyan]URL:[/cyan] {url}")

        # Estrutura completa (JSON)
        console.print("\n[bold cyan]═══ ESTRUTURA COMPLETA (JSON) ═══[/bold cyan]\n")

        # Mostra keys principais
        keys_tree = Tree("[bold]Keys Retornadas pela API[/bold]")
        for key in database.keys():
            keys_tree.add(f"[cyan]{key}[/cyan]")

        console.print(keys_tree)

        # Pergunta se quer ver JSON completo
        console.print("\n[dim]Deseja ver o JSON completo do database? (s/n)[/dim]")
        choice = input("> ").strip().lower()

        if choice in ["s", "sim", "y", "yes"]:
            console.print("\n")
            # Remove alguns campos muito grandes para melhor visualização
            clean_db = {
                k: v
                for k, v in database.items()
                if k not in ["cover", "icon"]
            }
            json_output = JSON.from_data(clean_db)
            console.print(json_output)

        # Diagnóstico
        console.print("\n[bold cyan]═══ DIAGNÓSTICO ═══[/bold cyan]\n")

        if not properties:
            console.print(
                Panel.fit(
                    "[bold red]⚠ Database sem propriedades[/bold red]\n\n"
                    "[yellow]Possíveis causas:[/yellow]\n"
                    "1. Database inline criado recentemente (API delay)\n"
                    "2. Propriedades não foram criadas corretamente\n"
                    "3. Database criado vazio precisa de página de exemplo\n\n"
                    "[yellow]Soluções:[/yellow]\n"
                    "1. Aguarde 1-2 minutos e execute novamente\n"
                    "2. Crie uma página manualmente no database\n"
                    "3. Use o script com página de exemplo\n"
                    "4. Recrie o database via API com todas as propriedades",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel.fit(
                    "[bold green]✓ Database está OK![/bold green]\n\n"
                    f"O database possui {len(properties)} propriedades configuradas.\n"
                    "Você pode começar a sincronizar dados com este database.",
                    border_style="green",
                )
            )

    except APIResponseError as e:
        console.print(f"\n[bold red]Erro na API do Notion:[/bold red]")
        console.print(f"[dim]Status:[/dim] {e.status}")
        console.print(f"[dim]Código:[/dim] {e.code}")
        console.print(f"[dim]Mensagem:[/dim] {str(e)}")

        if e.status == 404:
            console.print(
                "\n[yellow]O database não foi encontrado. Verifique:[/yellow]"
            )
            console.print("1. O ID está correto")
            console.print("2. A integração tem acesso ao database")
            console.print("3. O database não foi deletado")
    except Exception as e:
        console.print(f"\n[bold red]Erro inesperado:[/bold red]")
        console.print(str(e))
        import traceback

        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")


def main() -> None:
    """Função principal do script."""
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Inspetor de Database Notion[/bold cyan]\n"
            "[dim]Mostra todas as informações de um database[/dim]",
            border_style="cyan",
        )
    )

    try:
        # Obtém cliente
        client = get_notion_client()
        console.print("\n[green]✓ Cliente Notion conectado[/green]")

        # Obtém database ID
        console.print(
            "\n[bold]Digite o ID do database a inspecionar:[/bold]"
        )
        console.print(
            "[dim](Pode ser o ID completo ou apenas os últimos caracteres)[/dim]"
        )

        database_id = input("> ").strip()

        if not database_id:
            console.print("\n[red]ID não pode estar vazio![/red]")
            sys.exit(1)

        # Remove hífens se tiver
        database_id = database_id.replace("-", "")

        # Se tiver menos de 32 caracteres, tenta buscar do .env
        if len(database_id) < 32:
            console.print(
                "\n[yellow]ID muito curto. Buscando databases configurados...[/yellow]"
            )

            from smart_core_assistant_painel.app.notion_sync.models import (
                NotionDatabaseConfig,
            )

            configs = NotionDatabaseConfig.objects.filter(is_active=True)

            if configs.exists():
                console.print("\n[cyan]Databases encontrados:[/cyan]")
                table = Table(show_header=True)
                table.add_column("#", style="cyan", width=5)
                table.add_column("Model", style="green")
                table.add_column("Nome", style="yellow")
                table.add_column("ID", style="dim")

                for idx, cfg in enumerate(configs, 1):
                    table.add_row(
                        str(idx),
                        cfg.model_name,
                        cfg.database_name,
                        cfg.database_id[:16] + "...",
                    )

                console.print(table)
                console.print("\n[bold]Digite o número do database:[/bold]")
                choice = input("> ").strip()

                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(configs):
                        selected = list(configs)[choice_idx]
                        database_id = selected.database_id
                        console.print(
                            f"\n[green]✓ Selecionado: {selected.database_name}[/green]"
                        )
                    else:
                        console.print("\n[red]Número inválido![/red]")
                        sys.exit(1)
                except ValueError:
                    console.print("\n[red]Número inválido![/red]")
                    sys.exit(1)
            else:
                console.print(
                    "\n[yellow]Nenhum database configurado encontrado[/yellow]"
                )
                sys.exit(1)

        # Inspeciona o database
        inspect_database(client, database_id)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operação cancelada pelo usuário.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold red]Erro Inesperado[/bold red]\n\n{str(e)}",
                border_style="red",
            )
        )
        import traceback

        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
