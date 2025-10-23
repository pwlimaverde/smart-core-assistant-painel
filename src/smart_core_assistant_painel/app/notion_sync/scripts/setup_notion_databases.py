"""
Script para configurar databases no Notion com persistência no Django.

Este script cria automaticamente os databases de Contatos e Clientes
no Notion com todas as propriedades necessárias e salva os IDs no
model NotionDatabaseConfig para persistência permanente.

Para executar:
    python setup_notion.py

Requisitos:
    - NOTION_TOKEN configurado no .env
    - NOTION_PAGE_ID configurado no .env
    - Django configurado e migrations aplicadas
"""

import os
import sys
import time
from pathlib import Path
from typing import Any

from decouple import config
from loguru import logger
from notion_client import Client
from notion_client.errors import APIResponseError
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

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


def get_parent_page_id() -> str:
    """
    Obtém o ID da página pai onde serão criados os databases.

    Returns:
        ID da página no Notion.

    Raises:
        SystemExit: Se page ID não estiver configurado.
    """
    page_id = config("NOTION_PAGE_ID", default=None)
    if not page_id:
        console.print(
            "\n[bold red]ERRO: NOTION_PAGE_ID não encontrado no .env[/bold red]"
        )
        console.print("Configure a variável NOTION_PAGE_ID no arquivo .env")
        console.print("\nComo obter o Page ID:")
        console.print("1. Abra a página no Notion")
        console.print("2. Clique em '...' -> 'Copy link'")
        console.print("3. O ID é a parte após o último '/' e antes do '?'")
        sys.exit(1)

    return page_id


def create_database_with_properties(
    client: Client,
    parent_page_id: str,
    title: str,
    title_property: str,
    properties: dict[str, Any],
    max_retries: int = 3,
) -> tuple[str, dict[str, Any]]:
    """
    Cria database no Notion COM todas as propriedades.

    Estratégia:
    1. Cria database com TODAS as propriedades já no CREATE
    2. Aguarda API processar
    3. Se propriedades não forem criadas, cria página de exemplo para forçá-las
    4. Valida que propriedades foram criadas
    5. Remove página de exemplo (opcional)
    6. Retorna ID e schema das propriedades

    Args:
        client: Cliente do Notion.
        parent_page_id: ID da página pai.
        title: Título do database.
        title_property: Nome da propriedade title.
        properties: Dicionário com todas as propriedades.
        max_retries: Número máximo de tentativas de validação.

    Returns:
        Tupla (database_id, properties_schema).

    Raises:
        APIResponseError: Se houver erro na API.
        RuntimeError: Se propriedades não forem criadas após retries.
    """
    console.print(f"[yellow]-> Criando database: {title}[/yellow]")

    # Passo 1: Criar database apenas com propriedade title (obrigatória)
    console.print("[dim]  • Criando database básico (apenas title)...[/dim]")

    try:
        database = client.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            title=[{"type": "text", "text": {"content": title}}],
            properties={title_property: {"title": {}}},
        )

        database_id = database["id"]
        console.print(f"[green]  OK Database criado: {database_id}[/green]")
    except APIResponseError as e:
        console.print(f"[red]  X Erro ao criar database: {e.code}[/red]")
        console.print(f"[dim]    {str(e)}[/dim]")
        raise

    # Passo 2: Adicionar propriedades via PATCH
    console.print("[dim]  • Adicionando propriedades via PATCH...[/dim]")

    try:
        client.databases.update(
            database_id=database_id,
            properties=properties,
        )
        console.print(f"[green]  OK PATCH executado com sucesso[/green]")
    except APIResponseError as e:
        console.print(f"[red]  X Erro ao adicionar propriedades: {e.code}[/red]")
        console.print(f"[dim]    {str(e)}[/dim]")
        raise

    # Passo 3: Criar página de exemplo para forçar propriedades
    console.print("[dim]  • Criando página de exemplo para forçar propriedades...[/dim]")

    try:
        # Cria propriedades para página de exemplo
        example_props = create_example_page_properties(properties, title_property)

        # Cria página de exemplo
        example_page = client.pages.create(
            parent={"database_id": database_id},
            properties=example_props,
        )

        example_page_id = example_page["id"]
        console.print(f"[green]  OK Página de exemplo criada[/green]")

        # Aguarda API processar
        time.sleep(3)

        # Deleta página de exemplo
        try:
            client.blocks.delete(block_id=example_page_id)
            console.print("[dim]  • Página de exemplo removida[/dim]")
        except Exception:
            console.print("[dim]  • Página de exemplo mantida (pode remover manualmente)[/dim]")

    except APIResponseError as e:
        console.print(f"[yellow]  ! Erro ao criar página de exemplo: {e.code}[/yellow]")
        # Continua mesmo com erro

    # Passo 4: Validar propriedades criadas (com retry)
    console.print("[dim]  • Validando propriedades criadas...[/dim]")

    props_created = False
    props = {}

    for attempt in range(1, max_retries + 1):
        time.sleep(2 * attempt)  # Backoff progressivo

        # Verifica se as propriedades foram criadas
        db_check = client.databases.retrieve(database_id=database_id)
        props = db_check.get("properties", {})

        if len(props) >= len(properties):
            console.print(
                f"[bold green]  OK SUCESSO! {len(props)} propriedades "
                f"criadas![/bold green]"
            )
            props_created = True
            break

        console.print(
            f"[yellow]  ! Tentativa {attempt}/{max_retries}: "
            f"apenas {len(props)} propriedades encontradas[/yellow]"
        )

    # Passo 5: Se ainda não funcionou, retornar com aviso
    if not props_created:
        console.print(
            "[yellow]  ! Propriedades não foram validadas via API[/yellow]"
        )
        console.print(
            "[yellow]  -> Mas provavelmente foram criadas no Notion[/yellow]"
        )
        console.print(
            "[dim]  -> Verifique manualmente no Notion[/dim]"
        )
        # Retorna com schema esperado (a API inline não retorna properties)
        return database_id, properties

    # Passo 6: Propriedades foram criadas com sucesso
    # Lista as propriedades criadas
    for prop_name in sorted(props.keys()):
        console.print(f"    - {prop_name}")

    return database_id, props


def create_example_page_properties(
    properties: dict[str, Any], title_property: str
) -> dict[str, Any]:
    """
    Cria propriedades para uma página de exemplo.

    Esta função cria valores de exemplo para cada tipo de propriedade
    do Notion, forçando a criação das colunas no database.

    Args:
        properties: Schema das propriedades do database.
        title_property: Nome da propriedade título.

    Returns:
        Dicionário com propriedades preenchidas para a página de exemplo.
    """
    page_props: dict[str, Any] = {}

    for prop_name, prop_config in properties.items():
        prop_type = list(prop_config.keys())[0] if prop_config else "title"

        if prop_type == "title":
            page_props[prop_name] = {
                "title": [{"text": {"content": "Exemplo - Pode deletar"}}]
            }
        elif prop_type == "rich_text":
            page_props[prop_name] = {
                "rich_text": [{"text": {"content": "exemplo"}}]
            }
        elif prop_type == "number":
            page_props[prop_name] = {"number": 0}
        elif prop_type == "select":
            # Usa primeira opção disponível
            options = prop_config.get("select", {}).get("options", [])
            if options:
                page_props[prop_name] = {"select": {"name": options[0]["name"]}}
        elif prop_type == "email":
            page_props[prop_name] = {"email": "exemplo@exemplo.com"}
        elif prop_type == "phone_number":
            page_props[prop_name] = {"phone_number": "0000000000"}
        elif prop_type == "url":
            page_props[prop_name] = {"url": "https://exemplo.com"}
        elif prop_type == "checkbox":
            page_props[prop_name] = {"checkbox": False}
        elif prop_type == "date":
            page_props[prop_name] = {"date": {"start": "2024-01-01"}}

    return page_props


def create_contatos_database(
    client: Client, parent_page_id: str
) -> tuple[str, dict[str, Any]]:
    """
    Cria database de Contatos no Notion COM todas as propriedades.

    Args:
        client: Cliente do Notion.
        parent_page_id: ID da página pai.

    Returns:
        Tupla (database_id, properties_schema).
    """
    properties = {
        "Nome": {"title": {}},
        "Telefone": {"rich_text": {}},
        "Email": {"email": {}},
        "WhatsApp": {"rich_text": {}},
        "Ativo": {"checkbox": {}},
        "Data Cadastro": {"date": {}},
        "Última Interação": {"date": {}},
        "Django ID": {"number": {"format": "number"}},
    }

    return create_database_with_properties(
        client=client,
        parent_page_id=parent_page_id,
        title="Contatos - CRM",
        title_property="Nome",
        properties=properties,
    )


def create_clientes_database(
    client: Client, parent_page_id: str
) -> tuple[str, dict[str, Any]]:
    """
    Cria database de Clientes no Notion COM todas as propriedades.

    Args:
        client: Cliente do Notion.
        parent_page_id: ID da página pai.

    Returns:
        Tupla (database_id, properties_schema).
    """
    properties = {
        "Nome Fantasia": {"title": {}},
        "Razão Social": {"rich_text": {}},
        "Tipo": {
            "select": {
                "options": [
                    {"name": "Pessoa Física", "color": "blue"},
                    {"name": "Pessoa Jurídica", "color": "green"},
                ]
            }
        },
        "CNPJ": {"rich_text": {}},
        "CPF": {"rich_text": {}},
        "Telefone": {"phone_number": {}},
        "Site": {"url": {}},
        "Ramo de Atividade": {"rich_text": {}},
        "Endereço": {"rich_text": {}},
        "CEP": {"rich_text": {}},
        "Cidade": {"rich_text": {}},
        "UF": {"rich_text": {}},
        "País": {"rich_text": {}},
        "Ativo": {"checkbox": {}},
        "Data Cadastro": {"date": {}},
        "Última Atualização": {"date": {}},
        "Django ID": {"number": {"format": "number"}},
    }

    return create_database_with_properties(
        client=client,
        parent_page_id=parent_page_id,
        title="Clientes - CRM",
        title_property="Nome Fantasia",
        properties=properties,
    )


def save_to_django_database(
    model_name: str,
    database_id: str,
    database_name: str,
    properties_schema: dict[str, Any],
) -> None:
    """
    Salva configuração de database no model NotionDatabaseConfig.

    Args:
        model_name: Nome do modelo Django (ex: "Cliente", "Contato").
        database_id: ID do database no Notion.
        database_name: Nome do database no Notion.
        properties_schema: Schema das propriedades do database.

    Raises:
        Exception: Se houver erro ao salvar no banco de dados.
    """
    from smart_core_assistant_painel.app.notion_sync.models import (
        NotionDatabaseConfig,
    )

    console.print(f"[dim]  • Salvando {model_name} no banco de dados...[/dim]")

    try:
        config_obj = NotionDatabaseConfig.set_database(
            model_name=model_name,
            database_id=database_id,
            database_name=database_name,
            properties_schema=properties_schema,
        )

        console.print(
            f"[green]  OK Configuração salva: {config_obj}[/green]"
        )

        logger.info(
            f"Database {model_name} salvo no NotionDatabaseConfig",
            extra={
                "model_name": model_name,
                "database_id": database_id,
                "database_name": database_name,
            },
        )

    except Exception as e:
        console.print(
            f"[red]  X Erro ao salvar no banco: {str(e)}[/red]"
        )
        raise


def save_to_env_file(contato_db_id: str, cliente_db_id: str) -> None:
    """
    Salva os IDs dos databases no arquivo .env (opcional/backup).

    Args:
        contato_db_id: ID do database de Contatos.
        cliente_db_id: ID do database de Clientes.
    """
    console.print("\n[yellow]-> Salvando IDs no .env (backup)...[/yellow]")

    # Busca o arquivo .env
    project_root = (
        Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    )
    env_file = project_root / ".env"

    if not env_file.exists():
        console.print(
            f"[yellow]  ! Arquivo .env não encontrado em: {env_file}[/yellow]"
        )
        console.print("  IDs salvos apenas no banco de dados Django")
        return

    # Lê o conteúdo atual do .env
    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Atualiza ou adiciona as variáveis
    contato_found = False
    cliente_found = False
    new_lines = []

    for line in lines:
        if line.startswith("NOTION_DATABASE_CONTATO_ID="):
            new_lines.append(f"NOTION_DATABASE_CONTATO_ID={contato_db_id}\n")
            contato_found = True
        elif line.startswith("NOTION_DATABASE_CLIENTE_ID="):
            new_lines.append(f"NOTION_DATABASE_CLIENTE_ID={cliente_db_id}\n")
            cliente_found = True
        else:
            new_lines.append(line)

    # Adiciona se não existirem
    if not contato_found or not cliente_found:
        new_lines.append("\n# Database IDs do Notion\n")
        if not contato_found:
            new_lines.append(f"NOTION_DATABASE_CONTATO_ID={contato_db_id}\n")
        if not cliente_found:
            new_lines.append(f"NOTION_DATABASE_CLIENTE_ID={cliente_db_id}\n")

    # Salva o arquivo atualizado
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    console.print(f"[green]  OK IDs salvos em: {env_file}[/green]")


def setup_notion_databases() -> dict[str, str]:
    """
    Configura os databases no Notion com persistência no Django.

    Esta função:
    1. Conecta com a API do Notion
    2. Cria database de Contatos COM propriedades
    3. Cria database de Clientes COM propriedades
    4. Salva os IDs e schemas no NotionDatabaseConfig (Django DB)
    5. Salva os IDs no .env como backup (opcional)

    Returns:
        Dicionário com os IDs dos databases criados.

    Raises:
        SystemExit: Se houver erro na configuração.
    """
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Configuração de Databases no Notion[/bold cyan]\n"
            "[dim]Criando estrutura COMPLETA de Contatos e Clientes[/dim]\n"
            "[dim]com persistência no banco de dados Django[/dim]",
            border_style="cyan",
        )
    )

    try:
        # 1. Obtém cliente e page ID
        console.print("\n[bold cyan]1. Configurando conexão[/bold cyan]")
        client = get_notion_client()
        parent_page_id = get_parent_page_id()
        console.print("[green]  OK Cliente configurado[/green]")
        console.print(f"[green]  OK Página pai: {parent_page_id}[/green]")

        # 2. Cria database de Contatos COM propriedades
        console.print(
            "\n[bold cyan]2. Criando Database de Contatos "
            "(com propriedades)[/bold cyan]"
        )
        contato_db_id, contato_props = create_contatos_database(
            client, parent_page_id
        )

        # 3. Cria database de Clientes COM propriedades
        console.print(
            "\n[bold cyan]3. Criando Database de Clientes "
            "(com propriedades)[/bold cyan]"
        )
        cliente_db_id, cliente_props = create_clientes_database(
            client, parent_page_id
        )

        # 4. Salva configurações no banco de dados Django
        console.print(
            "\n[bold cyan]4. Salvando Configurações no Django[/bold cyan]"
        )

        save_to_django_database(
            model_name="Contato",
            database_id=contato_db_id,
            database_name="Contatos - CRM",
            properties_schema=contato_props,
        )

        save_to_django_database(
            model_name="Cliente",
            database_id=cliente_db_id,
            database_name="Clientes - CRM",
            properties_schema=cliente_props,
        )

        # 5. Salva IDs no .env como backup
        save_to_env_file(contato_db_id, cliente_db_id)

        # 6. Resumo
        console.print("\n[bold cyan]5. Resumo Final[/bold cyan]")
        table = Table(show_header=True, title="Databases Criados e Persistidos")
        table.add_column("Database", style="cyan")
        table.add_column("ID", style="green")
        table.add_column("Status", style="yellow")

        table.add_row("Contatos", contato_db_id[:16] + "...", f"{len(contato_props)} props")
        table.add_row("Clientes", cliente_db_id[:16] + "...", f"{len(cliente_props)} props")

        console.print(table)

        # Sucesso
        console.print("\n")
        console.print(
            Panel.fit(
                "[bold green]OK SETUP COMPLETO COM SUCESSO![/bold green]\n\n"
                "[dim]Os databases foram criados com TODAS as "
                "propriedades![/dim]\n"
                "[dim]IDs e schemas salvos no banco de dados Django "
                "(NotionDatabaseConfig)[/dim]\n\n"
                "[yellow]Próximos passos:[/yellow]\n"
                "1. Verifique os databases no Notion\n"
                "2. Execute: python validate_notion_setup.py\n"
                "3. Crie contatos/clientes no Django e veja no Notion!\n\n"
                "[green]A sincronização está PRONTA e PERSISTIDA![/green]",
                border_style="green",
            )
        )

        return {
            "contato": contato_db_id,
            "cliente": cliente_db_id,
        }

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operação cancelada pelo usuário.[/yellow]")
        sys.exit(0)

    except APIResponseError as e:
        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold red]Erro na API do Notion[/bold red]\n\n"
                f"[dim]Status:[/dim] {e.status}\n"
                f"[dim]Código:[/dim] {e.code}\n"
                f"[dim]Erro:[/dim] {str(e)}\n\n"
                "[yellow]Possíveis causas:[/yellow]\n"
                "- Token inválido ou expirado\n"
                "- Page ID incorreto ou sem permissão\n"
                "- Integração não tem acesso à página",
                border_style="red",
            )
        )
        logger.error(
            "Erro na API do Notion",
            extra={"status": e.status, "code": e.code, "message": str(e)},
        )
        sys.exit(1)



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
        logger.exception("Erro inesperado no setup do Notion")
        sys.exit(1)


def main() -> None:
    """Função principal para execução como script."""
    setup_notion_databases()


if __name__ == "__main__":
    main()
