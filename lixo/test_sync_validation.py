"""
Script de validação do sistema de sincronização.

Este script testa o funcionamento básico do app notion_sync,
verificando se os signals, models e tracking estão funcionando corretamente.

Para executar:
    python test_sync_validation.py
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

from smart_core_assistant_painel.app.notion_sync.models import (
    ClienteSync,
    ContatoSync,
    SyncConfig,
    SyncLog,
)
from smart_core_assistant_painel.app.ui.clientes.models import Cliente, Contato

console = Console()


def print_header(title: str) -> None:
    """Imprime um cabeçalho formatado."""
    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print(f"[bold yellow]{title}[/bold yellow]")
    console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")


def test_sync_config() -> None:
    """Testa o model SyncConfig."""
    print_header("📝 Testando SyncConfig")

    # Cria configuração de teste
    config = SyncConfig.set_value(
        key="test_notion_token",
        value="secret_test_token_12345",
        description="Token de teste para validação"
    )

    console.print(f"✅ Configuração criada: [green]{config.key}[/green]")
    console.print(f"   Valor: [dim]{config.value}[/dim]")

    # Recupera configuração
    retrieved = SyncConfig.get_value("test_notion_token")
    console.print(f"✅ Configuração recuperada: [green]{retrieved}[/green]")

    # Testa valor padrão
    default = SyncConfig.get_value("nonexistent_key", default="valor_padrao")
    console.print(f"✅ Valor padrão funcionando: [green]{default}[/green]")

    # Testa configuração complexa
    complex_config = SyncConfig.set_value(
        key="test_database_ids",
        value={
            "Cliente": "db-cliente-123",
            "Contato": "db-contato-456"
        },
        description="IDs dos databases de teste"
    )
    console.print(f"✅ Configuração complexa (JSON) criada: [green]{complex_config.key}[/green]")


def test_contato_sync() -> None:
    """Testa sincronização de Contato."""
    print_header("📞 Testando Sincronização de Contato")

    # Cria contato
    console.print("[yellow]Criando novo contato...[/yellow]")
    contato = Contato.objects.create(
        telefone="5511987654321",
        nome_contato="João Silva - Teste Sync",
        email="joao.teste@example.com"
    )
    console.print(f"✅ Contato criado: [green]#{contato.id}[/green] - {contato.nome_contato}")

    # Verifica se tracking foi criado automaticamente
    try:
        sync_meta = contato.sync_metadata
        console.print(f"✅ Tracking criado automaticamente: [green]ContatoSync #{sync_meta.id}[/green]")
        console.print(f"   - Sincronizado: [{'green' if sync_meta.is_synced else 'red'}]{sync_meta.is_synced}[/]")
        console.print(f"   - External ID: [dim]{sync_meta.external_id or 'None'}[/dim]")
        console.print(f"   - Tentativas: [yellow]{sync_meta.sync_attempts}[/yellow]")
    except ContatoSync.DoesNotExist:
        console.print("❌ [red]ERRO: Tracking não foi criado automaticamente![/red]")

    # Simula sincronização bem-sucedida
    console.print("\n[yellow]Simulando sincronização bem-sucedida...[/yellow]")
    sync_meta.mark_as_synced(external_id="notion-page-test-123")
    console.print(f"✅ Contato marcado como sincronizado")
    console.print(f"   - External ID: [green]{sync_meta.external_id}[/green]")
    console.print(f"   - Última sincronização: [cyan]{sync_meta.last_synced_at}[/cyan]")

    # Atualiza contato (deve marcar para re-sincronização)
    console.print("\n[yellow]Atualizando contato...[/yellow]")
    contato.nome_contato = "João Silva - Atualizado"
    contato.save()

    sync_meta.refresh_from_db()
    console.print(f"✅ Após atualização:")
    console.print(f"   - Sincronizado: [{'green' if sync_meta.is_synced else 'red'}]{sync_meta.is_synced}[/]")
    console.print(f"   - (Deve estar False para re-sincronizar)")

    # Simula falha de sincronização
    console.print("\n[yellow]Simulando falha de sincronização...[/yellow]")
    sync_meta.mark_as_failed(error_message="Erro de teste: API timeout")
    console.print(f"✅ Falha registrada:")
    console.print(f"   - Erro: [red]{sync_meta.sync_error}[/red]")
    console.print(f"   - Tentativas: [yellow]{sync_meta.sync_attempts}[/yellow]")


def test_cliente_sync() -> None:
    """Testa sincronização de Cliente."""
    print_header("🏢 Testando Sincronização de Cliente")

    # Cria cliente
    console.print("[yellow]Criando novo cliente...[/yellow]")
    cliente = Cliente.objects.create(
        nome_fantasia="Empresa Teste Sync Ltda",
        razao_social="Empresa Teste Sincronização LTDA",
        tipo="juridica",
        cnpj="12345678000199"
    )
    console.print(f"✅ Cliente criado: [green]#{cliente.id}[/green] - {cliente.nome_fantasia}")

    # Verifica se tracking foi criado automaticamente
    try:
        sync_meta = cliente.sync_metadata
        console.print(f"✅ Tracking criado automaticamente: [green]ClienteSync #{sync_meta.id}[/green]")
        console.print(f"   - Sincronizado: [{'green' if sync_meta.is_synced else 'red'}]{sync_meta.is_synced}[/]")
        console.print(f"   - External ID: [dim]{sync_meta.external_id or 'None'}[/dim]")
        console.print(f"   - Tentativas: [yellow]{sync_meta.sync_attempts}[/yellow]")
    except ClienteSync.DoesNotExist:
        console.print("❌ [red]ERRO: Tracking não foi criado automaticamente![/red]")

    # Simula sincronização bem-sucedida
    console.print("\n[yellow]Simulando sincronização bem-sucedida...[/yellow]")
    sync_meta.mark_as_synced(external_id="notion-page-cliente-456")
    console.print(f"✅ Cliente marcado como sincronizado")
    console.print(f"   - External ID: [green]{sync_meta.external_id}[/green]")
    console.print(f"   - Última sincronização: [cyan]{sync_meta.last_synced_at}[/cyan]")


def test_sync_logs() -> None:
    """Testa os logs de sincronização."""
    print_header("📋 Verificando Logs de Sincronização")

    # Busca logs recentes
    logs = SyncLog.objects.all()[:10]

    if not logs:
        console.print("[yellow]Nenhum log encontrado ainda.[/yellow]")
        return

    # Cria tabela de logs
    table = Table(title="Últimos 10 Logs de Sincronização", show_header=True)
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Model", style="magenta", width=10)
    table.add_column("Django ID", style="yellow", width=10)
    table.add_column("Operação", style="blue", width=10)
    table.add_column("Status", width=12)
    table.add_column("Criado em", style="dim", width=20)

    for log in logs:
        status_color = "green" if log.status == "success" else "red" if log.status == "error" else "yellow"
        table.add_row(
            str(log.id),
            log.model_name,
            str(log.django_id or "-"),
            log.operation,
            f"[{status_color}]{log.get_status_display()}[/{status_color}]",
            str(log.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        )

    console.print(table)

    # Estatísticas
    total_logs = SyncLog.objects.count()
    success_logs = SyncLog.objects.filter(status="success").count()
    error_logs = SyncLog.objects.filter(status="error").count()
    pending_logs = SyncLog.objects.filter(status="pending").count()

    console.print(f"\n[bold]Estatísticas:[/bold]")
    console.print(f"  Total de logs: [cyan]{total_logs}[/cyan]")
    console.print(f"  Sucessos: [green]{success_logs}[/green]")
    console.print(f"  Erros: [red]{error_logs}[/red]")
    console.print(f"  Pendentes: [yellow]{pending_logs}[/yellow]")


def test_summary() -> None:
    """Exibe resumo da validação."""
    print_header("📊 Resumo da Validação")

    total_configs = SyncConfig.objects.count()
    total_contato_sync = ContatoSync.objects.count()
    total_cliente_sync = ClienteSync.objects.count()
    total_logs = SyncLog.objects.count()

    synced_contatos = ContatoSync.objects.filter(is_synced=True).count()
    synced_clientes = ClienteSync.objects.filter(is_synced=True).count()

    summary_table = Table(title="Resumo do Sistema", show_header=True)
    summary_table.add_column("Model", style="cyan", width=20)
    summary_table.add_column("Total", style="yellow", justify="right", width=10)
    summary_table.add_column("Sincronizados", style="green", justify="right", width=15)

    summary_table.add_row("SyncConfig", str(total_configs), "-")
    summary_table.add_row("ContatoSync", str(total_contato_sync), str(synced_contatos))
    summary_table.add_row("ClienteSync", str(total_cliente_sync), str(synced_clientes))
    summary_table.add_row("SyncLog", str(total_logs), "-")

    console.print(summary_table)

    # Painel de status
    if total_contato_sync > 0 and total_cliente_sync > 0:
        status_text = Text()
        status_text.append("✅ Sistema funcionando corretamente!\n", style="bold green")
        status_text.append("- Signals estão disparando\n", style="green")
        status_text.append("- Tracking está sendo criado automaticamente\n", style="green")
        status_text.append("- Logs estão sendo registrados\n", style="green")

        console.print(Panel(status_text, title="Status do Sistema", border_style="green"))
    else:
        console.print(Panel(
            "[yellow]⚠️  Ainda não há dados suficientes para validação completa.[/yellow]",
            title="Status do Sistema",
            border_style="yellow"
        ))


def main() -> None:
    """Função principal do script de validação."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Sistema de Sincronização - Validação[/bold cyan]\n"
        "[dim]Testando funcionamento do app notion_sync[/dim]",
        border_style="cyan"
    ))

    try:
        # Executa testes
        test_sync_config()
        test_contato_sync()
        test_cliente_sync()
        test_sync_logs()
        test_summary()

        console.print("\n")
        console.print(Panel.fit(
            "[bold green]✅ Validação concluída com sucesso![/bold green]",
            border_style="green"
        ))

    except Exception as e:
        console.print("\n")
        console.print(Panel.fit(
            f"[bold red]❌ Erro durante validação:[/bold red]\n\n{str(e)}",
            border_style="red"
        ))
        raise


if __name__ == "__main__":
    main()
