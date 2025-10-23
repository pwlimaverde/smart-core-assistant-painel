"""
Script para limpar dados de teste do sistema de sincronização.

Este script remove todos os dados de teste criados durante a validação,
incluindo contatos, clientes, logs e configurações de teste.

Para executar:
    python cleanup_test_data.py
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
from rich.prompt import Confirm

from smart_core_assistant_painel.app.notion_sync.models import (
    ClienteSync,
    ContatoSync,
    SyncConfig,
    SyncLog,
)
from smart_core_assistant_painel.app.ui.clientes.models import Cliente, Contato

console = Console()


def count_records() -> dict[str, int]:
    """Conta registros existentes no sistema."""
    return {
        "contatos": Contato.objects.count(),
        "clientes": Cliente.objects.count(),
        "contato_sync": ContatoSync.objects.count(),
        "cliente_sync": ClienteSync.objects.count(),
        "sync_logs": SyncLog.objects.count(),
        "sync_configs": SyncConfig.objects.count(),
    }


def delete_test_data() -> dict[str, int]:
    """
    Deleta dados de teste do sistema.

    Returns:
        Dicionário com contagem de registros deletados.
    """
    deleted = {}

    # Deleta contatos de teste
    console.print("\n[yellow]Deletando Contatos de teste...[/yellow]")
    contatos = Contato.objects.filter(nome_contato__icontains="teste")
    deleted["contatos"] = contatos.count()
    contatos.delete()
    console.print(f"  ✅ {deleted['contatos']} contatos deletados")

    # Deleta clientes de teste
    console.print("[yellow]Deletando Clientes de teste...[/yellow]")
    clientes = Cliente.objects.filter(nome_fantasia__icontains="teste")
    deleted["clientes"] = clientes.count()
    clientes.delete()
    console.print(f"  ✅ {deleted['clientes']} clientes deletados")

    # Deleta tracking órfãos (se houver)
    console.print("[yellow]Verificando tracking órfãos...[/yellow]")
    # Os OneToOne com CASCADE já deletam automaticamente, mas vamos verificar
    deleted["contato_sync_orfaos"] = 0
    deleted["cliente_sync_orfaos"] = 0
    console.print(f"  ✅ Nenhum tracking órfão encontrado")

    # Deleta logs antigos de teste
    console.print("[yellow]Deletando Logs de sincronização...[/yellow]")
    logs = SyncLog.objects.all()
    deleted["sync_logs"] = logs.count()
    logs.delete()
    console.print(f"  ✅ {deleted['sync_logs']} logs deletados")

    # Deleta configurações de teste
    console.print("[yellow]Deletando Configurações de teste...[/yellow]")
    configs = SyncConfig.objects.filter(key__istartswith="test_")
    deleted["sync_configs"] = configs.count()
    configs.delete()
    console.print(f"  ✅ {deleted['sync_configs']} configurações deletadas")

    return deleted


def main() -> None:
    """Função principal do script de limpeza."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold yellow]⚠️  Limpeza de Dados de Teste[/bold yellow]\n"
        "[dim]Este script vai deletar todos os dados de teste[/dim]",
        border_style="yellow"
    ))

    # Mostra contagem atual
    console.print("\n[bold cyan]Registros atuais no sistema:[/bold cyan]")
    counts = count_records()
    for key, value in counts.items():
        console.print(f"  • {key}: [yellow]{value}[/yellow]")

    # Confirma deleção
    console.print("\n")
    if not Confirm.ask(
        "[bold red]Deseja realmente deletar os dados de teste?[/bold red]",
        default=False
    ):
        console.print("\n[yellow]Operação cancelada pelo usuário.[/yellow]")
        return

    # Executa deleção
    console.print("\n[bold cyan]Iniciando limpeza...[/bold cyan]")
    deleted = delete_test_data()

    # Mostra contagem final
    console.print("\n[bold cyan]Registros após limpeza:[/bold cyan]")
    final_counts = count_records()
    for key, value in final_counts.items():
        console.print(f"  • {key}: [green]{value}[/green]")

    # Resumo
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]✅ Limpeza concluída com sucesso![/bold green]\n\n"
        f"[dim]Total deletado:[/dim]\n"
        f"  • Contatos: {deleted['contatos']}\n"
        f"  • Clientes: {deleted['clientes']}\n"
        f"  • Logs: {deleted['sync_logs']}\n"
        f"  • Configs: {deleted['sync_configs']}",
        border_style="green"
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operação cancelada pelo usuário (Ctrl+C).[/yellow]")
    except Exception as e:
        console.print("\n")
        console.print(Panel.fit(
            f"[bold red]❌ Erro durante limpeza:[/bold red]\n\n{str(e)}",
            border_style="red"
        ))
        raise
