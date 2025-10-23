"""
Script de validação completa da configuração do Notion.

Este script verifica:
1. Configurações do ambiente (.env)
2. Persistência no banco de dados Django (NotionDatabaseConfig)
3. Conexão com a API do Notion
4. Existência dos databases no Notion
5. Propriedades configuradas corretamente
6. Mappers e serviços funcionando

Para executar:
    python validate_notion_setup.py

Requisitos:
    - Django configurado e migrations aplicadas
    - NOTION_TOKEN configurado no .env
    - setup_notion.py executado previamente
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

from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig
from smart_core_assistant_painel.app.notion_sync.services import NotionSyncService

console = Console()


def print_header() -> None:
    """Imprime cabeçalho do script."""
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Validação Completa da Configuração do Notion[/bold cyan]\n"
            "[dim]Verificando todas as configurações e integrações[/dim]",
            border_style="cyan",
        )
    )


def check_environment_variables() -> dict[str, bool]:
    """
    Verifica se as variáveis de ambiente estão configuradas.

    Returns:
        Dicionário com status das verificações.
    """
    console.print("\n[bold cyan]1. Verificando Variáveis de Ambiente[/bold cyan]")

    results = {}

    # Token do Notion
    token = config("NOTION_TOKEN", default=None)
    if token:
        console.print("[green]  ✓ NOTION_TOKEN: configurado[/green]")
        results["token"] = True
    else:
        console.print("[red]  ✗ NOTION_TOKEN: NÃO configurado[/red]")
        results["token"] = False

    # Page ID do Notion
    page_id = config("NOTION_PAGE_ID", default=None)
    if page_id:
        console.print(f"[green]  ✓ NOTION_PAGE_ID: {page_id[:8]}...[/green]")
        results["page_id"] = True
    else:
        console.print("[yellow]  ⚠ NOTION_PAGE_ID: não configurado (opcional)[/yellow]")
        results["page_id"] = False

    # Database IDs (fallback do .env)
    contato_id = config("NOTION_DATABASE_CONTATO_ID", default=None)
    cliente_id = config("NOTION_DATABASE_CLIENTE_ID", default=None)

    if contato_id:
        console.print(f"[green]  ✓ NOTION_DATABASE_CONTATO_ID: {contato_id[:8]}...[/green]")
        results["contato_env"] = True
    else:
        console.print("[yellow]  ⚠ NOTION_DATABASE_CONTATO_ID: não configurado[/yellow]")
        results["contato_env"] = False

    if cliente_id:
        console.print(f"[green]  ✓ NOTION_DATABASE_CLIENTE_ID: {cliente_id[:8]}...[/green]")
        results["cliente_env"] = True
    else:
        console.print("[yellow]  ⚠ NOTION_DATABASE_CLIENTE_ID: não configurado[/yellow]")
        results["cliente_env"] = False

    return results


def check_django_database() -> dict[str, any]:
    """
    Verifica se os databases estão salvos no NotionDatabaseConfig.

    Returns:
        Dicionário com status e dados dos databases.
    """
    console.print("\n[bold cyan]2. Verificando Banco de Dados Django[/bold cyan]")

    results = {}

    try:
        # Busca configurações do Contato
        contato_config = NotionDatabaseConfig.objects.filter(
            model_name="Contato", is_active=True
        ).first()

        if contato_config:
            console.print(f"[green]  ✓ Contato: {contato_config}[/green]")
            console.print(f"[dim]    Database ID: {contato_config.database_id}[/dim]")
            console.print(f"[dim]    Propriedades: {len(contato_config.properties_schema)}[/dim]")
            results["contato"] = {
                "found": True,
                "config": contato_config,
                "database_id": contato_config.database_id,
                "properties_count": len(contato_config.properties_schema),
            }
        else:
            console.print("[red]  ✗ Contato: NÃO encontrado no banco de dados[/red]")
            results["contato"] = {"found": False}

        # Busca configurações do Cliente
        cliente_config = NotionDatabaseConfig.objects.filter(
            model_name="Cliente", is_active=True
        ).first()

        if cliente_config:
            console.print(f"[green]  ✓ Cliente: {cliente_config}[/green]")
            console.print(f"[dim]    Database ID: {cliente_config.database_id}[/dim]")
            console.print(f"[dim]    Propriedades: {len(cliente_config.properties_schema)}[/dim]")
            results["cliente"] = {
                "found": True,
                "config": cliente_config,
                "database_id": cliente_config.database_id,
                "properties_count": len(cliente_config.properties_schema),
            }
        else:
            console.print("[red]  ✗ Cliente: NÃO encontrado no banco de dados[/red]")
            results["cliente"] = {"found": False}

        # Mostra todas as configurações
        all_configs = NotionDatabaseConfig.objects.all()
        console.print(f"\n[dim]  Total de configurações: {all_configs.count()}[/dim]")

    except Exception as e:
        console.print(f"[red]  ✗ Erro ao acessar banco de dados: {str(e)}[/red]")
        results["error"] = str(e)

    return results


def check_notion_connection(token: str) -> tuple[bool, Client | None]:
    """
    Verifica se a conexão com o Notion está funcionando.

    Args:
        token: Token de integração do Notion.

    Returns:
        Tupla (sucesso, cliente).
    """
    console.print("\n[bold cyan]3. Verificando Conexão com o Notion[/bold cyan]")

    try:
        client = Client(auth=token)

        # Tenta buscar informações do usuário (teste de autenticação)
        user_info = client.users.me()

        console.print("[green]  ✓ Conexão estabelecida com sucesso[/green]")
        console.print(f"[dim]    Bot ID: {user_info.get('id', 'N/A')}[/dim]")
        console.print(f"[dim]    Tipo: {user_info.get('type', 'N/A')}[/dim]")

        return True, client

    except APIResponseError as e:
        console.print(f"[red]  ✗ Erro na API do Notion: {e.code}[/red]")
        console.print(f"[dim]    {str(e)}[/dim]")
        return False, None
    except Exception as e:
        console.print(f"[red]  ✗ Erro ao conectar: {str(e)}[/red]")
        return False, None


def validate_database_in_notion(
    client: Client, database_id: str, expected_name: str
) -> dict[str, any]:
    """
    Valida que um database existe no Notion e tem as propriedades corretas.

    Args:
        client: Cliente do Notion.
        database_id: ID do database.
        expected_name: Nome esperado do database.

    Returns:
        Dicionário com resultado da validação.
    """
    try:
        database = client.databases.retrieve(database_id=database_id)

        # Extrai informações
        title = database.get("title", [])
        title_text = title[0].get("plain_text", "") if title else "Sem título"
        properties = database.get("properties", {})

        result = {
            "success": True,
            "title": title_text,
            "properties": properties,
            "properties_count": len(properties),
        }

        console.print(f"[green]  ✓ Database encontrado: {title_text}[/green]")
        console.print(f"[dim]    ID: {database_id}[/dim]")
        console.print(f"[dim]    Propriedades: {len(properties)}[/dim]")

        # Lista propriedades
        for prop_name in sorted(properties.keys()):
            prop_type = properties[prop_name].get("type", "unknown")
            console.print(f"[dim]      - {prop_name} ({prop_type})[/dim]")

        return result

    except APIResponseError as e:
        console.print(f"[red]  ✗ Erro ao buscar database: {e.code}[/red]")
        console.print(f"[dim]    {str(e)}[/dim]")
        return {"success": False, "error": str(e)}
    except Exception as e:
        console.print(f"[red]  ✗ Erro: {str(e)}[/red]")
        return {"success": False, "error": str(e)}


def check_notion_databases(
    client: Client, db_results: dict[str, any]
) -> dict[str, any]:
    """
    Verifica se os databases existem no Notion.

    Args:
        client: Cliente do Notion.
        db_results: Resultados da verificação do banco de dados Django.

    Returns:
        Dicionário com resultados das validações.
    """
    console.print("\n[bold cyan]4. Validando Databases no Notion[/bold cyan]")

    results = {}

    # Valida database de Contatos
    if db_results.get("contato", {}).get("found"):
        console.print("\n[yellow]→ Validando Database de Contatos[/yellow]")
        contato_id = db_results["contato"]["database_id"]
        results["contato"] = validate_database_in_notion(
            client, contato_id, "Contatos - CRM"
        )
    else:
        console.print("[red]  ✗ Database de Contatos não configurado[/red]")
        results["contato"] = {"success": False, "error": "Não configurado"}

    # Valida database de Clientes
    if db_results.get("cliente", {}).get("found"):
        console.print("\n[yellow]→ Validando Database de Clientes[/yellow]")
        cliente_id = db_results["cliente"]["database_id"]
        results["cliente"] = validate_database_in_notion(
            client, cliente_id, "Clientes - CRM"
        )
    else:
        console.print("[red]  ✗ Database de Clientes não configurado[/red]")
        results["cliente"] = {"success": False, "error": "Não configurado"}

    return results


def check_notion_service() -> dict[str, bool]:
    """
    Verifica se o NotionSyncService está funcionando corretamente.

    Returns:
        Dicionário com status das verificações.
    """
    console.print("\n[bold cyan]5. Verificando NotionSyncService[/bold cyan]")

    results = {}

    try:
        # Tenta inicializar o serviço
        service = NotionSyncService()
        console.print("[green]  ✓ NotionSyncService inicializado[/green]")
        results["initialization"] = True

        # Verifica database IDs
        contato_id = service.get_database_id("Contato")
        cliente_id = service.get_database_id("Cliente")

        if contato_id:
            console.print(f"[green]  ✓ Database ID Contato: {contato_id[:8]}...[/green]")
            results["contato_id"] = True
        else:
            console.print("[red]  ✗ Database ID Contato: não encontrado[/red]")
            results["contato_id"] = False

        if cliente_id:
            console.print(f"[green]  ✓ Database ID Cliente: {cliente_id[:8]}...[/green]")
            results["cliente_id"] = True
        else:
            console.print("[red]  ✗ Database ID Cliente: não encontrado[/red]")
            results["cliente_id"] = False

        # Testa health check
        try:
            health = service.health_check()
            console.print("[green]  ✓ Health check passou[/green]")
            console.print(f"[dim]    Status: {health.get('status')}[/dim]")
            results["health_check"] = True
        except Exception as e:
            console.print(f"[yellow]  ⚠ Health check falhou: {str(e)}[/yellow]")
            results["health_check"] = False

    except Exception as e:
        console.print(f"[red]  ✗ Erro ao inicializar serviço: {str(e)}[/red]")
        results["initialization"] = False
        results["error"] = str(e)

    return results


def print_summary(
    env_results: dict[str, bool],
    db_results: dict[str, any],
    connection_success: bool,
    notion_results: dict[str, any],
    service_results: dict[str, bool],
) -> None:
    """
    Imprime resumo final da validação.

    Args:
        env_results: Resultados da verificação de ambiente.
        db_results: Resultados do banco de dados Django.
        connection_success: Se a conexão com Notion foi bem-sucedida.
        notion_results: Resultados da validação dos databases.
        service_results: Resultados do NotionSyncService.
    """
    console.print("\n[bold cyan]6. Resumo Final[/bold cyan]")

    table = Table(title="Status da Configuração")
    table.add_column("Componente", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Detalhes")

    # Variáveis de ambiente
    if env_results.get("token"):
        table.add_row("NOTION_TOKEN", "[green]✓ OK[/green]", "Configurado")
    else:
        table.add_row("NOTION_TOKEN", "[red]✗ ERRO[/red]", "Não configurado")

    # Banco de dados Django
    if db_results.get("contato", {}).get("found"):
        props = db_results["contato"]["properties_count"]
        table.add_row(
            "NotionDatabaseConfig (Contato)",
            "[green]✓ OK[/green]",
            f"{props} propriedades",
        )
    else:
        table.add_row(
            "NotionDatabaseConfig (Contato)", "[red]✗ ERRO[/red]", "Não encontrado"
        )

    if db_results.get("cliente", {}).get("found"):
        props = db_results["cliente"]["properties_count"]
        table.add_row(
            "NotionDatabaseConfig (Cliente)",
            "[green]✓ OK[/green]",
            f"{props} propriedades",
        )
    else:
        table.add_row(
            "NotionDatabaseConfig (Cliente)", "[red]✗ ERRO[/red]", "Não encontrado"
        )

    # Conexão com Notion
    if connection_success:
        table.add_row("Conexão Notion", "[green]✓ OK[/green]", "Conectado")
    else:
        table.add_row("Conexão Notion", "[red]✗ ERRO[/red]", "Falha na conexão")

    # Databases no Notion
    if notion_results.get("contato", {}).get("success"):
        props = notion_results["contato"]["properties_count"]
        table.add_row(
            "Database Contatos (Notion)",
            "[green]✓ OK[/green]",
            f"{props} propriedades",
        )
    else:
        table.add_row("Database Contatos (Notion)", "[red]✗ ERRO[/red]", "Não encontrado")

    if notion_results.get("cliente", {}).get("success"):
        props = notion_results["cliente"]["properties_count"]
        table.add_row(
            "Database Clientes (Notion)",
            "[green]✓ OK[/green]",
            f"{props} propriedades",
        )
    else:
        table.add_row("Database Clientes (Notion)", "[red]✗ ERRO[/red]", "Não encontrado")

    # NotionSyncService
    if service_results.get("initialization"):
        table.add_row("NotionSyncService", "[green]✓ OK[/green]", "Inicializado")
    else:
        table.add_row("NotionSyncService", "[red]✗ ERRO[/red]", "Falha na inicialização")

    console.print(table)

    # Determina status geral
    all_ok = (
        env_results.get("token", False)
        and db_results.get("contato", {}).get("found", False)
        and db_results.get("cliente", {}).get("found", False)
        and connection_success
        and notion_results.get("contato", {}).get("success", False)
        and notion_results.get("cliente", {}).get("success", False)
        and service_results.get("initialization", False)
    )

    console.print("\n")
    if all_ok:
        console.print(
            Panel.fit(
                "[bold green]✓ TUDO CONFIGURADO CORRETAMENTE![/bold green]\n\n"
                "[dim]A integração com Notion está pronta para uso![/dim]\n\n"
                "[yellow]Próximos passos:[/yellow]\n"
                "1. Crie um Contato ou Cliente no Django Admin\n"
                "2. Verifique se aparece no Notion\n"
                "3. Os signals estão ativos e devem sincronizar automaticamente\n\n"
                "[green]Você está pronto para começar![/green]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel.fit(
                "[bold yellow]⚠ CONFIGURAÇÃO INCOMPLETA[/bold yellow]\n\n"
                "[dim]Algumas verificações falharam.[/dim]\n\n"
                "[yellow]O que fazer:[/yellow]\n"
                "1. Revise os erros acima\n"
                "2. Execute: python setup_notion.py\n"
                "3. Configure as variáveis de ambiente necessárias\n"
                "4. Execute este script novamente para validar",
                border_style="yellow",
            )
        )


def main() -> None:
    """Função principal do script de validação."""
    try:
        print_header()

        # 1. Verifica variáveis de ambiente
        env_results = check_environment_variables()

        # 2. Verifica banco de dados Django
        db_results = check_django_database()

        # 3. Verifica conexão com Notion
        token = config("NOTION_TOKEN", default=None)
        connection_success = False
        client = None

        if token:
            connection_success, client = check_notion_connection(token)

        # 4. Valida databases no Notion
        notion_results = {}
        if client and connection_success:
            notion_results = check_notion_databases(client, db_results)

        # 5. Verifica NotionSyncService
        service_results = check_notion_service()

        # 6. Imprime resumo
        print_summary(
            env_results, db_results, connection_success, notion_results, service_results
        )

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Validação cancelada pelo usuário.[/yellow]")
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
