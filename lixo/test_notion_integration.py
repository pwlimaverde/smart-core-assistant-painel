"""
Script de teste de integração com o Notion.

Este script testa a conexão real com a API do Notion e valida
que os dados estão sendo sincronizados corretamente.

Para executar:
    python test_notion_integration.py

Requisitos:
    - .env configurado com NOTION_TOKEN
    - .env configurado com NOTION_DATABASE_CONTATO_ID
    - .env configurado com NOTION_DATABASE_CLIENTE_ID
    - Databases criados no Notion com a estrutura correta
    - Integração conectada aos databases
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

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from smart_core_assistant_painel.app.notion_sync.exceptions import (
    NotionSyncError,
    SyncConfigError,
)
from smart_core_assistant_painel.app.notion_sync.models import (
    ClienteSync,
    ContatoSync,
    SyncLog,
)
from smart_core_assistant_painel.app.notion_sync.services import NotionSyncService
from smart_core_assistant_painel.app.ui.clientes.models import Cliente, Contato

console = Console()


def print_section(title: str) -> None:
    """Imprime um cabeçalho de seção."""
    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print(f"[bold yellow]{title}[/bold yellow]")
    console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")


def test_configuration() -> bool:
    """
    Testa se as configurações necessárias estão presentes.

    Returns:
        True se configurações estão OK, False caso contrário.
    """
    print_section("📋 1. Verificando Configurações")

    from decouple import config

    # Verifica NOTION_TOKEN
    token = config("NOTION_TOKEN", default=None)
    if token:
        token_preview = f"{token[:10]}...{token[-5:]}"
        console.print(f"✅ NOTION_TOKEN: [green]{token_preview}[/green]")
    else:
        console.print("❌ NOTION_TOKEN: [red]NÃO CONFIGURADO[/red]")
        return False

    # Verifica NOTION_DATABASE_CONTATO_ID
    contato_db = config("NOTION_DATABASE_CONTATO_ID", default=None)
    if contato_db:
        console.print(f"✅ NOTION_DATABASE_CONTATO_ID: [green]{contato_db}[/green]")
    else:
        console.print("❌ NOTION_DATABASE_CONTATO_ID: [red]NÃO CONFIGURADO[/red]")
        return False

    # Verifica NOTION_DATABASE_CLIENTE_ID
    cliente_db = config("NOTION_DATABASE_CLIENTE_ID", default=None)
    if cliente_db:
        console.print(f"✅ NOTION_DATABASE_CLIENTE_ID: [green]{cliente_db}[/green]")
    else:
        console.print("❌ NOTION_DATABASE_CLIENTE_ID: [red]NÃO CONFIGURADO[/red]")
        return False

    console.print("\n[bold green]✅ Todas as configurações estão presentes![/bold green]")
    return True


def test_connection() -> NotionSyncService | None:
    """
    Testa a conexão com o Notion.

    Returns:
        Instância do NotionSyncService se conexão OK, None caso contrário.
    """
    print_section("🔌 2. Testando Conexão com Notion")

    try:
        service = NotionSyncService()
        console.print("✅ NotionSyncService inicializado com sucesso")

        # Valida conexão
        is_valid = service.validate_connection()
        if is_valid:
            console.print("\n[bold green]✅ Conexão com Notion validada![/bold green]")
            return service
        else:
            console.print("\n[bold red]❌ Conexão com Notion falhou![/bold red]")
            return None

    except SyncConfigError as e:
        console.print(f"\n[bold red]❌ Erro de configuração:[/bold red]")
        console.print(f"   {e.message}")
        if e.details:
            console.print(f"   Detalhes: {e.details}")
        return None

    except Exception as e:
        console.print(f"\n[bold red]❌ Erro inesperado:[/bold red] {e}")
        return None


def test_contato_sync(service: NotionSyncService) -> bool:
    """
    Testa sincronização completa de um Contato.

    Args:
        service: Instância do NotionSyncService.

    Returns:
        True se teste passou, False caso contrário.
    """
    print_section("📞 3. Testando Sincronização de Contato")

    try:
        # Limpa contatos de teste anteriores
        console.print("[dim]Limpando contatos de teste anteriores...[/dim]")
        Contato.objects.filter(telefone="5511999887766").delete()

        # Cria contato de teste
        console.print("\n[yellow]→ Criando contato de teste...[/yellow]")
        contato = Contato.objects.create(
            telefone="5511999887766",
            nome_contato="Teste Integração Notion",
            email="teste.notion@example.com",
            nome_perfil_whatsapp="Teste WhatsApp",
            ativo=True
        )
        console.print(f"✅ Contato criado no Django: ID #{contato.id}")

        # Aguarda um momento para o signal processar
        import time
        time.sleep(2)

        # Verifica tracking
        console.print("\n[yellow]→ Verificando tracking...[/yellow]")
        sync_meta = contato.sync_metadata
        console.print(f"   Sincronizado: [{'green' if sync_meta.is_synced else 'red'}]{sync_meta.is_synced}[/]")
        console.print(f"   External ID: [cyan]{sync_meta.external_id or 'None'}[/cyan]")
        console.print(f"   Tentativas: [yellow]{sync_meta.sync_attempts}[/yellow]")

        if not sync_meta.is_synced:
            console.print(f"   Erro: [red]{sync_meta.sync_error}[/red]")
            return False

        # Verifica logs
        console.print("\n[yellow]→ Verificando logs...[/yellow]")
        logs = SyncLog.objects.filter(
            model_name="Contato",
            django_id=contato.id
        ).order_by("-created_at")

        table = Table(show_header=True)
        table.add_column("Operação", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Timestamp", style="dim")

        for log in logs[:5]:  # Últimos 5 logs
            status_color = "green" if log.status == "success" else "red" if log.status == "error" else "yellow"
            table.add_row(
                log.operation,
                f"[{status_color}]{log.get_status_display()}[/{status_color}]",
                str(log.created_at.strftime("%H:%M:%S"))
            )

        console.print(table)

        # Testa atualização
        console.print("\n[yellow]→ Testando atualização...[/yellow]")
        contato.nome_contato = "Teste Integração Notion (Atualizado)"
        contato.save()

        time.sleep(2)

        sync_meta.refresh_from_db()
        console.print(f"   Sincronizado após update: [{'green' if sync_meta.is_synced else 'red'}]{sync_meta.is_synced}[/]")

        # Limpa
        console.print("\n[yellow]→ Removendo contato de teste...[/yellow]")
        contato.delete()
        console.print("✅ Contato removido")

        console.print("\n[bold green]✅ Teste de Contato concluído com sucesso![/bold green]")
        return True

    except Exception as e:
        console.print(f"\n[bold red]❌ Erro no teste de Contato:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def test_cliente_sync(service: NotionSyncService) -> bool:
    """
    Testa sincronização completa de um Cliente.

    Args:
        service: Instância do NotionSyncService.

    Returns:
        True se teste passou, False caso contrário.
    """
    print_section("🏢 4. Testando Sincronização de Cliente")

    try:
        # Limpa clientes de teste anteriores
        console.print("[dim]Limpando clientes de teste anteriores...[/dim]")
        Cliente.objects.filter(nome_fantasia__icontains="Teste Integração Notion").delete()

        # Cria cliente de teste
        console.print("\n[yellow]→ Criando cliente de teste...[/yellow]")
        cliente = Cliente.objects.create(
            nome_fantasia="Teste Integração Notion Ltda",
            razao_social="Teste Integração Notion LTDA",
            tipo="juridica",
            cnpj="12.345.678/0001-99",
            telefone="(11) 3000-0000",
            ramo_atividade="Tecnologia",
            cidade="São Paulo",
            uf="SP",
            pais="Brasil",
            ativo=True
        )
        console.print(f"✅ Cliente criado no Django: ID #{cliente.id}")

        # Aguarda um momento para o signal processar
        import time
        time.sleep(2)

        # Verifica tracking
        console.print("\n[yellow]→ Verificando tracking...[/yellow]")
        sync_meta = cliente.sync_metadata
        console.print(f"   Sincronizado: [{'green' if sync_meta.is_synced else 'red'}]{sync_meta.is_synced}[/]")
        console.print(f"   External ID: [cyan]{sync_meta.external_id or 'None'}[/cyan]")
        console.print(f"   Tentativas: [yellow]{sync_meta.sync_attempts}[/yellow]")

        if not sync_meta.is_synced:
            console.print(f"   Erro: [red]{sync_meta.sync_error}[/red]")
            return False

        # Verifica logs
        console.print("\n[yellow]→ Verificando logs...[/yellow]")
        logs = SyncLog.objects.filter(
            model_name="Cliente",
            django_id=cliente.id
        ).order_by("-created_at")

        table = Table(show_header=True)
        table.add_column("Operação", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Timestamp", style="dim")

        for log in logs[:5]:  # Últimos 5 logs
            status_color = "green" if log.status == "success" else "red" if log.status == "error" else "yellow"
            table.add_row(
                log.operation,
                f"[{status_color}]{log.get_status_display()}[/{status_color}]",
                str(log.created_at.strftime("%H:%M:%S"))
            )

        console.print(table)

        # Testa atualização
        console.print("\n[yellow]→ Testando atualização...[/yellow]")
        cliente.razao_social = "Teste Integração Notion LTDA (Atualizado)"
        cliente.save()

        time.sleep(2)

        sync_meta.refresh_from_db()
        console.print(f"   Sincronizado após update: [{'green' if sync_meta.is_synced else 'red'}]{sync_meta.is_synced}[/]")

        # Limpa
        console.print("\n[yellow]→ Removendo cliente de teste...[/yellow]")
        cliente.delete()
        console.print("✅ Cliente removido")

        console.print("\n[bold green]✅ Teste de Cliente concluído com sucesso![/bold green]")
        return True

    except Exception as e:
        console.print(f"\n[bold red]❌ Erro no teste de Cliente:[/bold red] {e}")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def test_health_check(service: NotionSyncService) -> None:
    """
    Executa health check do serviço.

    Args:
        service: Instância do NotionSyncService.
    """
    print_section("🏥 5. Health Check")

    health = service.health_check()

    table = Table(show_header=True, title="Status da Integração")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="yellow")

    status_color = "green" if health["status"] == "healthy" else "red"
    table.add_row("Status", f"[{status_color}]{health['status']}[/{status_color}]")
    table.add_row("API Alcançável", f"[{'green' if health['api_reachable'] else 'red'}]{health['api_reachable']}[/]")
    table.add_row("Mensagem", health["message"] or "-")

    console.print(table)


def main() -> None:
    """Função principal do script de teste."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]🧪 Teste de Integração com Notion[/bold cyan]\n"
        "[dim]Validação completa da sincronização Django ↔ Notion[/dim]",
        border_style="cyan"
    ))

    # 1. Testa configurações
    if not test_configuration():
        console.print("\n")
        console.print(Panel.fit(
            "[bold red]❌ Configurações incompletas![/bold red]\n\n"
            "[dim]Configure as variáveis no .env:[/dim]\n"
            "- NOTION_TOKEN\n"
            "- NOTION_DATABASE_CONTATO_ID\n"
            "- NOTION_DATABASE_CLIENTE_ID\n\n"
            "[dim]Consulte .env.notion.example para instruções.[/dim]",
            border_style="red"
        ))
        return

    # 2. Testa conexão
    service = test_connection()
    if not service:
        console.print("\n")
        console.print(Panel.fit(
            "[bold red]❌ Falha na conexão com Notion![/bold red]\n\n"
            "[dim]Verifique:[/dim]\n"
            "- Token está correto e não expirou\n"
            "- Integração está conectada aos databases\n"
            "- IDs dos databases estão corretos",
            border_style="red"
        ))
        return

    # 3. Testa sincronização de Contato
    contato_ok = test_contato_sync(service)

    # 4. Testa sincronização de Cliente
    cliente_ok = test_cliente_sync(service)

    # 5. Health check
    test_health_check(service)

    # Resultado final
    console.print("\n")
    if contato_ok and cliente_ok:
        console.print(Panel.fit(
            "[bold green]✅ TODOS OS TESTES PASSARAM![/bold green]\n\n"
            "[dim]A integração com o Notion está funcionando perfeitamente.[/dim]\n"
            "[dim]Verifique os dados no Notion![/dim]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold yellow]⚠️  ALGUNS TESTES FALHARAM[/bold yellow]\n\n"
            f"[dim]Contato:[/dim] [{'green' if contato_ok else 'red'}]{'OK' if contato_ok else 'FALHOU'}[/]\n"
            f"[dim]Cliente:[/dim] [{'green' if cliente_ok else 'red'}]{'OK' if cliente_ok else 'FALHOU'}[/]\n\n"
            "[dim]Verifique os logs acima para mais detalhes.[/dim]",
            border_style="yellow"
        ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Teste cancelado pelo usuário (Ctrl+C).[/yellow]")
    except Exception as e:
        console.print("\n")
        console.print(Panel.fit(
            f"[bold red]❌ Erro crítico:[/bold red]\n\n{str(e)}",
            border_style="red"
        ))
        import traceback
        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise
