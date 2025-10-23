"""
Script para inspecionar propriedades dos databases do Notion.

Uso:
    python inspect_database.py
"""

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
    "smart_core_assistant_painel.app.ui.core.settings"
)

import django
django.setup()

from decouple import config
from notion_client import Client
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def inspect_database(client: Client, db_id: str, db_name: str) -> None:
    """Inspeciona um database do Notion."""
    console.print(f"\n[bold cyan]Inspecionando: {db_name}[/bold cyan]")
    console.print(f"[dim]Database ID: {db_id}[/dim]\n")

    try:
        db = client.databases.retrieve(database_id=db_id)

        # DEBUG: Mostra estrutura completa
        console.print("[dim]DEBUG - Chaves da resposta:[/dim]")
        console.print(f"[dim]{list(db.keys())}[/dim]\n")

        # DEBUG: Mostra tipo do objeto
        console.print(f"[dim]DEBUG - Tipo: {type(db)}[/dim]\n")

        # Tenta diferentes formas de acessar propriedades
        properties = None

        # Tenta como dicionário
        if isinstance(db, dict):
            properties = db.get("properties", {})
            console.print(f"[dim]DEBUG - Properties (dict): {bool(properties)}[/dim]")

        # Tenta como objeto
        if hasattr(db, 'properties'):
            properties = db.properties
            console.print(f"[dim]DEBUG - Properties (attr): {bool(properties)}[/dim]")

        # DEBUG: Mostra o valor de properties
        import json
        console.print("\n[dim]DEBUG - Conteúdo de properties:[/dim]")
        console.print(f"[dim]{json.dumps(properties, indent=2, default=str) if properties else 'None'}[/dim]\n")

        if not properties:
            console.print("[red]Nenhuma propriedade encontrada![/red]")
            console.print("\n[yellow]DEBUG - Resposta completa do Notion:[/yellow]")
            console.print(f"[dim]{json.dumps(db, indent=2, default=str)}[/dim]")
            
            # Tenta resolver quando for Linked Database (data_sources)
            data_sources = db.get("data_sources", []) if isinstance(db, dict) else []
            if data_sources:
                console.print("\n[bold yellow]Possível Linked Database detectado. Inspecionando data_sources...[/bold yellow]")
                for ds in data_sources:
                    ds_id = ds.get("id")
                    ds_name = ds.get("name", "Data Source")
                    if ds_id:
                        console.print(f"[dim]→ Buscando data_source: {ds_name} ({ds_id})[/dim]")
                        try:
                            ds_db = client.databases.retrieve(database_id=ds_id)
                            ds_props = ds_db.get("properties", {})
                            if ds_props:
                                console.print(f"[green]✓ Propriedades encontradas no data_source ({len(ds_props)}):[/green]")
                                # Tabela das propriedades do data_source
                                ds_table = Table(show_header=True, title=f"Propriedades de {ds_name}")
                                ds_table.add_column("Nome da Propriedade", style="cyan")
                                ds_table.add_column("Tipo", style="yellow")
                                ds_table.add_column("ID", style="dim")
                                for prop_name, prop_data in ds_props.items():
                                    prop_type = prop_data.get("type", "unknown")
                                    prop_id = prop_data.get("id", "N/A")
                                    ds_table.add_row(prop_name, prop_type, prop_id)
                                console.print(ds_table)
                            else:
                                console.print("[yellow]Nenhuma propriedade no data_source[/yellow]")
                        except Exception as e:
                            console.print(f"[red]Falha ao buscar data_source {ds_id}: {e}[/red]")
            return

        # Cria tabela de propriedades
        table = Table(show_header=True, title=f"Propriedades de {db_name}")
        table.add_column("Nome da Propriedade", style="cyan")
        table.add_column("Tipo", style="yellow")
        table.add_column("ID", style="dim")

        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "unknown") if isinstance(prop_data, dict) else getattr(prop_data, 'type', 'unknown')
            prop_id = prop_data.get("id", "N/A") if isinstance(prop_data, dict) else getattr(prop_data, 'id', 'N/A')
            table.add_row(prop_name, prop_type, prop_id)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Erro ao inspecionar database: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def main() -> None:
    """Função principal."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Inspetor de Databases do Notion[/bold cyan]",
        border_style="cyan"
    ))

    # Obtém configurações
    token = config("NOTION_TOKEN", default=None)
    contato_db = config("NOTION_DATABASE_CONTATO_ID", default=None)
    cliente_db = config("NOTION_DATABASE_CLIENTE_ID", default=None)

    # Fallback: buscar IDs ativos do Django se env vars não existirem
    contato_name = "Contatos"
    cliente_name = "Clientes"
    if not contato_db or not cliente_db:
        try:
            from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig
            configs = NotionDatabaseConfig.objects.filter(is_active=True)
            for cfg in configs:
                if cfg.model_name.lower() == "contato" and not contato_db:
                    contato_db = cfg.database_id
                    contato_name = cfg.database_name or contato_name
                if cfg.model_name.lower() == "cliente" and not cliente_db:
                    cliente_db = cfg.database_id
                    cliente_name = cfg.database_name or cliente_name
        except Exception as e:
            console.print(f"[yellow]Aviso: não foi possível carregar NotionDatabaseConfig: {e}[/yellow]")

    if not token:
        console.print("\n[red]❌ NOTION_TOKEN não configurado![/red]")
        return

    # Cria cliente
    client = Client(auth=token)

    # Inspeciona Contatos
    if contato_db:
        inspect_database(client, contato_db, contato_name)
    else:
        console.print("\n[yellow]NOTION_DATABASE_CONTATO_ID nao configurado e sem fallback[/yellow]")

    # Inspeciona Clientes
    if cliente_db:
        inspect_database(client, cliente_db, cliente_name)
    else:
        console.print("\n[yellow]NOTION_DATABASE_CLIENTE_ID nao configurado e sem fallback[/yellow]")

    console.print("\n")


if __name__ == "__main__":
    main()
