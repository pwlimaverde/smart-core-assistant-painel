"""
Script de teste direto com a API do Notion para debug.

Este script testa diretamente a criação de databases e adição de propriedades
para entender o comportamento real da API.

Para executar:
    python test_notion_api_direct.py

Requisitos:
    - NOTION_TOKEN configurado no .env
    - NOTION_PAGE_ID configurado no .env
"""

import json
import os
import sys
import time
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
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel

console = Console()


def test_create_database_with_properties() -> None:
    """
    Testa criação de database com propriedades usando diferentes abordagens.
    """
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Teste Direto da API do Notion[/bold cyan]\n"
            "[dim]Testando criacao de database e propriedades[/dim]",
            border_style="cyan",
        )
    )

    # Obtém configurações
    token = config("NOTION_TOKEN", default=None)
    page_id = config("NOTION_PAGE_ID", default=None)

    if not token or not page_id:
        console.print("\n[red]ERRO: NOTION_TOKEN ou NOTION_PAGE_ID não configurados![/red]")
        sys.exit(1)

    client = Client(auth=token)

    console.print(f"\n[green]OK Token configurado[/green]")
    console.print(f"[green]OK Page ID: {page_id}[/green]")

    # ========================================================================
    # TESTE 1: Criar database COM propriedades no CREATE
    # ========================================================================
    console.print("\n[bold yellow]=== TESTE 1: CREATE com todas as propriedades ===[/bold yellow]\n")

    properties_full = {
        "Nome": {"title": {}},
        "Email": {"email": {}},
        "Telefone": {"rich_text": {}},
        "Ativo": {"checkbox": {}},
    }

    try:
        console.print("[dim]Criando database com propriedades no CREATE...[/dim]")

        response = client.databases.create(
            parent={"type": "page_id", "page_id": page_id},
            title=[{"type": "text", "text": {"content": "TESTE 1 - CREATE Full"}}],
            properties=properties_full,
        )

        db_id_test1 = response["id"]
        console.print(f"[green]OK Database criado: {db_id_test1}[/green]")

        # Aguarda um pouco
        time.sleep(2)

        # Busca o database
        console.print("[dim]Buscando database criado...[/dim]")
        db_get = client.databases.retrieve(database_id=db_id_test1)

        props = db_get.get("properties", {})
        console.print(f"[cyan]Propriedades retornadas: {len(props)}[/cyan]")

        if props:
            console.print("[green]OK SUCESSO! Propriedades criadas:[/green]")
            for prop_name in sorted(props.keys()):
                console.print(f"  * {prop_name}")
        else:
            console.print("[red]X FALHA! Nenhuma propriedade retornada[/red]")
            console.print(f"[dim]Keys na resposta: {list(db_get.keys())}[/dim]")

        # Mostra JSON completo
        console.print("\n[bold]Resposta completa do GET:[/bold]")
        console.print(JSON.from_data(db_get))

    except Exception as e:
        console.print(f"[red]X Erro no teste 1: {str(e)}[/red]")

    # ========================================================================
    # TESTE 2: Criar database básico + PATCH para adicionar propriedades
    # ========================================================================
    console.print("\n\n[bold yellow]=== TESTE 2: CREATE basico + PATCH ===[/bold yellow]\n")

    try:
        # Passo 1: Criar database básico
        console.print("[dim]Criando database basico (apenas title)...[/dim]")

        response = client.databases.create(
            parent={"type": "page_id", "page_id": page_id},
            title=[{"type": "text", "text": {"content": "TESTE 2 - CREATE + PATCH"}}],
            properties={"Nome": {"title": {}}},
        )

        db_id_test2 = response["id"]
        console.print(f"[green]OK Database criado: {db_id_test2}[/green]")

        # Passo 2: PATCH para adicionar propriedades
        console.print("[dim]Executando PATCH para adicionar propriedades...[/dim]")

        properties_to_add = {
            "Nome": {"title": {}},  # Já existe
            "Email": {"email": {}},
            "Telefone": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
        }

        patch_response = client.databases.update(
            database_id=db_id_test2,
            properties=properties_to_add,
        )

        console.print(f"[green]OK PATCH executado (status: 200 OK)[/green]")

        # Mostra resposta do PATCH
        console.print("\n[bold]Resposta do PATCH:[/bold]")
        patch_props = patch_response.get("properties", {})
        console.print(f"[cyan]Propriedades na resposta do PATCH: {len(patch_props)}[/cyan]")
        if patch_props:
            for prop_name in sorted(patch_props.keys()):
                console.print(f"  * {prop_name}")
        else:
            console.print("[yellow]Nenhuma propriedade na resposta do PATCH[/yellow]")

        # Aguarda mais tempo
        console.print("\n[dim]Aguardando 5 segundos antes do GET...[/dim]")
        time.sleep(5)

        # Passo 3: GET para verificar
        console.print("[dim]Buscando database apos PATCH...[/dim]")
        db_get = client.databases.retrieve(database_id=db_id_test2)

        props = db_get.get("properties", {})
        console.print(f"[cyan]Propriedades retornadas no GET: {len(props)}[/cyan]")

        if props:
            console.print("[green]OK SUCESSO! Propriedades apos PATCH:[/green]")
            for prop_name in sorted(props.keys()):
                console.print(f"  * {prop_name}")
        else:
            console.print("[red]X FALHA! Nenhuma propriedade retornada no GET[/red]")
            console.print(f"[dim]Keys na resposta: {list(db_get.keys())}[/dim]")

        # Mostra JSON completo
        console.print("\n[bold]Resposta completa do GET apos PATCH:[/bold]")
        console.print(JSON.from_data(db_get))

    except Exception as e:
        console.print(f"[red]X Erro no teste 2: {str(e)}[/red]")
        import traceback
        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")

    # ========================================================================
    # TESTE 3: Verificar se e questao de API version ou tipo de database
    # ========================================================================
    console.print("\n\n[bold yellow]=== TESTE 3: Informacoes da API ===[/bold yellow]\n")

    try:
        # Busca informações do usuário/bot
        user_info = client.users.me()
        console.print("[green]Informações do Bot:[/green]")
        console.print(f"  * ID: {user_info.get('id', 'N/A')}")
        console.print(f"  * Type: {user_info.get('type', 'N/A')}")
        console.print(f"  * Name: {user_info.get('name', 'N/A')}")

    except Exception as e:
        console.print(f"[red]X Erro no teste 3: {str(e)}[/red]")

    # ========================================================================
    # CONCLUSAO
    # ========================================================================
    console.print("\n\n[bold cyan]=== CONCLUSAO ===[/bold cyan]\n")
    console.print(
        "[yellow]Se nenhum dos testes retornou propriedades no GET,[/yellow]\n"
        "[yellow]isso indica uma limitacao da API do Notion com databases inline.[/yellow]\n\n"
        "[cyan]Possiveis causas:[/cyan]\n"
        "1. A API nao retorna 'properties' para databases recem-criados\n"
        "2. Databases inline (parent=page_id) tem comportamento diferente\n"
        "3. E necessario criar uma pagina no database para 'materializar' as propriedades\n"
        "4. A versao da API tem limitacoes nao documentadas\n\n"
        "[green]Proximo teste:[/green]\n"
        "Tente criar uma página no database e depois busque novamente."
    )


if __name__ == "__main__":
    try:
        test_create_database_with_properties()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Teste cancelado pelo usuário.[/yellow]")
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
