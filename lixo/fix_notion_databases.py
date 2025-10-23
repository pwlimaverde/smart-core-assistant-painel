"""
Script para adicionar propriedades aos databases existentes no Notion.

Este script corrige databases que foram criados sem propriedades,
adicionando todas as colunas necessárias para sincronização.

Para executar:
    python fix_notion_databases.py

Requisitos:
    - NOTION_TOKEN configurado no .env
    - NOTION_DATABASE_CONTATO_ID configurado no .env
    - NOTION_DATABASE_CLIENTE_ID configurado no .env
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
from loguru import logger
from notion_client import Client
from notion_client.errors import APIResponseError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def fix_contatos_database(client: Client, database_id: str) -> bool:
    """
    Adiciona propriedades ao database de Contatos.

    Args:
        client: Cliente do Notion.
        database_id: ID do database de Contatos.

    Returns:
        True se bem-sucedido, False caso contrário.
    """
    console.print("\n[yellow]Corrigindo database de Contatos...[/yellow]")

    try:
        # Define as propriedades necessárias
        properties = {
            "Nome": {
                "title": {}
            },
            "Telefone": {
                "rich_text": {}
            },
            "Email": {
                "email": {}
            },
            "WhatsApp": {
                "rich_text": {}
            },
            "Ativo": {
                "checkbox": {}
            },
            "Data Cadastro": {
                "date": {}
            },
            "Última Interação": {
                "date": {}
            },
            "Django ID": {
                "number": {
                    "format": "number"
                }
            }
        }

        # Atualiza o database
        console.print("[dim]Adicionando propriedades...[/dim]")
        client.databases.update(
            database_id=database_id,
            properties=properties
        )

        console.print("[green]✅ Database de Contatos atualizado![/green]")

        # Verifica se as propriedades foram criadas
        console.print("[dim]Verificando propriedades...[/dim]")
        db = client.databases.retrieve(database_id=database_id)
        props = db.get("properties", {})

        if not props:
            console.print("[red]❌ Propriedades não encontradas após update![/red]")
            return False

        console.print(f"[green]✅ {len(props)} propriedades confirmadas[/green]")

        # Lista as propriedades criadas
        table = Table(title="Propriedades Criadas - Contatos", show_header=True)
        table.add_column("Propriedade", style="cyan")
        table.add_column("Tipo", style="yellow")

        for prop_name, prop_data in props.items():
            prop_type = prop_data.get("type", "unknown")
            table.add_row(prop_name, prop_type)

        console.print(table)

        return True

    except APIResponseError as e:
        console.print(f"[red]❌ Erro ao atualizar database de Contatos:[/red]")
        console.print(f"Status: {e.status}")
        console.print(f"Código: {e.code}")
        console.print(f"Erro: {str(e)}")
        return False

    except Exception as e:
        console.print(f"[red]❌ Erro inesperado:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def fix_clientes_database(client: Client, database_id: str) -> bool:
    """
    Adiciona propriedades ao database de Clientes.

    Args:
        client: Cliente do Notion.
        database_id: ID do database de Clientes.

    Returns:
        True se bem-sucedido, False caso contrário.
    """
    console.print("\n[yellow]Corrigindo database de Clientes...[/yellow]")

    try:
        # Define as propriedades necessárias
        properties = {
            "Nome Fantasia": {
                "title": {}
            },
            "Razão Social": {
                "rich_text": {}
            },
            "Tipo": {
                "select": {
                    "options": [
                        {
                            "name": "Pessoa Física",
                            "color": "blue"
                        },
                        {
                            "name": "Pessoa Jurídica",
                            "color": "green"
                        }
                    ]
                }
            },
            "CNPJ": {
                "rich_text": {}
            },
            "CPF": {
                "rich_text": {}
            },
            "Telefone": {
                "phone_number": {}
            },
            "Site": {
                "url": {}
            },
            "Ramo de Atividade": {
                "rich_text": {}
            },
            "Endereço": {
                "rich_text": {}
            },
            "CEP": {
                "rich_text": {}
            },
            "Cidade": {
                "rich_text": {}
            },
            "UF": {
                "rich_text": {}
            },
            "País": {
                "rich_text": {}
            },
            "Ativo": {
                "checkbox": {}
            },
            "Data Cadastro": {
                "date": {}
            },
            "Última Atualização": {
                "date": {}
            },
            "Django ID": {
                "number": {
                    "format": "number"
                }
            }
        }

        # Atualiza o database
        console.print("[dim]Adicionando propriedades...[/dim]")
        client.databases.update(
            database_id=database_id,
            properties=properties
        )

        console.print("[green]✅ Database de Clientes atualizado![/green]")

        # Verifica se as propriedades foram criadas
        console.print("[dim]Verificando propriedades...[/dim]")
        db = client.databases.retrieve(database_id=database_id)
        props = db.get("properties", {})

        if not props:
            console.print("[red]❌ Propriedades não encontradas após update![/red]")
            return False

        console.print(f"[green]✅ {len(props)} propriedades confirmadas[/green]")

        # Lista as propriedades criadas
        table = Table(title="Propriedades Criadas - Clientes", show_header=True)
        table.add_column("Propriedade", style="cyan")
        table.add_column("Tipo", style="yellow")

        for prop_name, prop_data in props.items():
            prop_type = prop_data.get("type", "unknown")
            table.add_row(prop_name, prop_type)

        console.print(table)

        return True

    except APIResponseError as e:
        console.print(f"[red]❌ Erro ao atualizar database de Clientes:[/red]")
        console.print(f"Status: {e.status}")
        console.print(f"Código: {e.code}")
        console.print(f"Erro: {str(e)}")
        return False

    except Exception as e:
        console.print(f"[red]❌ Erro inesperado:[/red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def main() -> None:
    """Função principal do script."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Correcao de Databases do Notion[/bold cyan]\n"
        "[dim]Adicionando propriedades aos databases existentes[/dim]",
        border_style="cyan"
    ))

    # Obtém configurações
    token = config("NOTION_TOKEN", default=None)
    contato_db_id = config("NOTION_DATABASE_CONTATO_ID", default=None)
    cliente_db_id = config("NOTION_DATABASE_CLIENTE_ID", default=None)

    # Valida configurações
    if not token:
        console.print("\n[red]❌ NOTION_TOKEN não configurado no .env![/red]")
        sys.exit(1)

    if not contato_db_id:
        console.print("\n[red]❌ NOTION_DATABASE_CONTATO_ID não configurado no .env![/red]")
        sys.exit(1)

    if not cliente_db_id:
        console.print("\n[red]❌ NOTION_DATABASE_CLIENTE_ID não configurado no .env![/red]")
        sys.exit(1)

    # Cria cliente do Notion
    console.print("\n[yellow]Conectando ao Notion...[/yellow]")
    client = Client(auth=token)
    console.print("[green]✅ Conectado![/green]")

    # Corrige databases
    results = {}

    # Contatos
    results["contatos"] = fix_contatos_database(client, contato_db_id)

    # Clientes
    results["clientes"] = fix_clientes_database(client, cliente_db_id)

    # Resultado final
    console.print("\n")
    if all(results.values()):
        console.print(Panel.fit(
            "[bold green]✅ SUCESSO![/bold green]\n\n"
            "[dim]Todos os databases foram corrigidos com sucesso.[/dim]\n"
            "[dim]As propriedades foram adicionadas e validadas.[/dim]\n\n"
            "[yellow]Próximos passos:[/yellow]\n"
            "1. Execute: python test_notion_integration.py\n"
            "2. Crie contatos/clientes no Django\n"
            "3. Verifique os dados no Notion!\n\n"
            "[green]Agora a sincronização deve funcionar perfeitamente![/green]",
            border_style="green"
        ))
    else:
        failed = [k for k, v in results.items() if not v]
        console.print(Panel.fit(
            f"[bold yellow]⚠️  PARCIALMENTE CONCLUÍDO[/bold yellow]\n\n"
            f"[dim]Alguns databases falharam:[/dim] {', '.join(failed)}\n\n"
            "[yellow]Verifique os erros acima e tente novamente.[/yellow]",
            border_style="yellow"
        ))
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operacao cancelada pelo usuario.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print("\n")
        console.print(Panel.fit(
            f"[bold red]❌ Erro Critico[/bold red]\n\n{str(e)}",
            border_style="red"
        ))
        import traceback
        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
