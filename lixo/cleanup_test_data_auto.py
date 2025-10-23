"""
Script para limpar dados de teste do sistema de sincronização (versão automática).

Este script remove automaticamente todos os dados de teste criados durante
a validação, sem solicitar confirmação.

Para executar:
    python cleanup_test_data_auto.py
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

from smart_core_assistant_painel.app.notion_sync.models import (
    ClienteSync,
    ContatoSync,
    SyncConfig,
    SyncLog,
)
from smart_core_assistant_painel.app.ui.clientes.models import Cliente, Contato

console = Console()


def main() -> None:
    """Função principal do script de limpeza automática."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold yellow]🧹 Limpeza Automática de Dados de Teste[/bold yellow]",
        border_style="yellow"
    ))

    # Conta registros antes
    console.print("\n[bold cyan]📊 Contagem ANTES da limpeza:[/bold cyan]")
    before_table = Table(show_header=True)
    before_table.add_column("Model", style="cyan")
    before_table.add_column("Quantidade", justify="right", style="yellow")

    contatos_count = Contato.objects.count()
    clientes_count = Cliente.objects.count()
    contato_sync_count = ContatoSync.objects.count()
    cliente_sync_count = ClienteSync.objects.count()
    logs_count = SyncLog.objects.count()
    configs_count = SyncConfig.objects.count()

    before_table.add_row("Contatos", str(contatos_count))
    before_table.add_row("Clientes", str(clientes_count))
    before_table.add_row("ContatoSync", str(contato_sync_count))
    before_table.add_row("ClienteSync", str(cliente_sync_count))
    before_table.add_row("SyncLog", str(logs_count))
    before_table.add_row("SyncConfig", str(configs_count))

    console.print(before_table)

    # Executa limpeza
    console.print("\n[bold yellow]🗑️  Executando limpeza...[/bold yellow]\n")

    deleted = {}

    # 1. Deleta todos os Contatos
    console.print("[dim]→ Deletando Contatos...[/dim]")
    deleted["contatos"] = Contato.objects.all().delete()[0]
    console.print(f"  ✅ {deleted['contatos']} contatos deletados")

    # 2. Deleta todos os Clientes
    console.print("[dim]→ Deletando Clientes...[/dim]")
    deleted["clientes"] = Cliente.objects.all().delete()[0]
    console.print(f"  ✅ {deleted['clientes']} clientes deletados")

    # 3. Deleta tracking órfãos (se houver - CASCADE deveria ter deletado)
    console.print("[dim]→ Verificando tracking órfãos...[/dim]")
    orphan_contato = ContatoSync.objects.all().delete()[0]
    orphan_cliente = ClienteSync.objects.all().delete()[0]
    console.print(f"  ✅ {orphan_contato} ContatoSync órfãos deletados")
    console.print(f"  ✅ {orphan_cliente} ClienteSync órfãos deletados")

    # 4. Deleta TODOS os logs
    console.print("[dim]→ Deletando Logs...[/dim]")
    deleted["logs"] = SyncLog.objects.all().delete()[0]
    console.print(f"  ✅ {deleted['logs']} logs deletados")

    # 5. Deleta TODAS as configurações
    console.print("[dim]→ Deletando Configurações...[/dim]")
    deleted["configs"] = SyncConfig.objects.all().delete()[0]
    console.print(f"  ✅ {deleted['configs']} configurações deletadas")

    # Conta registros depois
    console.print("\n[bold cyan]📊 Contagem APÓS a limpeza:[/bold cyan]")
    after_table = Table(show_header=True)
    after_table.add_column("Model", style="cyan")
    after_table.add_column("Quantidade", justify="right", style="green")

    after_table.add_row("Contatos", str(Contato.objects.count()))
    after_table.add_row("Clientes", str(Cliente.objects.count()))
    after_table.add_row("ContatoSync", str(ContatoSync.objects.count()))
    after_table.add_row("ClienteSync", str(ClienteSync.objects.count()))
    after_table.add_row("SyncLog", str(SyncLog.objects.count()))
    after_table.add_row("SyncConfig", str(SyncConfig.objects.count()))

    console.print(after_table)

    # Resumo final
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]✅ Limpeza concluída com sucesso![/bold green]\n\n"
        "[dim]Banco de dados limpo e pronto para novo teste.[/dim]",
        border_style="green"
    ))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print("\n")
        console.print(Panel.fit(
            f"[bold red]❌ Erro durante limpeza:[/bold red]\n\n{str(e)}",
            border_style="red"
        ))
        import traceback
        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise
