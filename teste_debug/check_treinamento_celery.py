"""Script de debug para verificar estado de vetorização e Celery."""

import os

# Configura o ambiente Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.core.settings",
)

import django

django.setup()

from django_celery_results.models import TaskResult
from rich.console import Console
from rich.table import Table

from smart_core_assistant_painel.app.treinamento.models import (
    Documento,
    Treinamento,
)

console = Console()


def check_treinamentos() -> None:
    """Verifica estado dos treinamentos."""
    console.print("\n[bold cyan]📊 Estado dos Treinamentos[/bold cyan]")

    # Treinamentos com ambos False
    pendentes = Treinamento.objects.filter(
        treinamento_finalizado=False, treinamento_vetorizado=False
    )
    console.print(f"  - Pendentes (não finalizados): {pendentes.count()}")

    # Treinamentos finalizados mas não vetorizados (deveriam estar sendo processados)
    aguardando = Treinamento.objects.filter(
        treinamento_finalizado=True, treinamento_vetorizado=False
    )
    console.print(
        f"  - [yellow]Aguardando vetorização: {aguardando.count()}[/yellow]"
    )

    if aguardando.exists():
        console.print(
            "\n[bold yellow]⚠️ Treinamentos aguardando vetorização:[/]"
        )
        table = Table(show_header=True)
        table.add_column("ID")
        table.add_column("Tag")
        table.add_column("Grupo")
        table.add_column("Conteúdo (chars)")
        table.add_column("Data Criação")

        for t in aguardando[:10]:
            table.add_row(
                str(t.id),
                t.tag,
                t.grupo,
                str(len(t.conteudo) if t.conteudo else 0),
                str(t.data_criacao),
            )
        console.print(table)

    # Treinamentos vetorizados
    vetorizados = Treinamento.objects.filter(
        treinamento_finalizado=True, treinamento_vetorizado=True
    )
    console.print(
        f"  - [green]Vetorizados com sucesso: {vetorizados.count()}[/green]"
    )

    # Documentos criados
    total_docs = Documento.objects.count()
    console.print(
        f"\n[bold cyan]📄 Total de Documentos (chunks): {total_docs}[/]"
    )


def check_celery_results() -> None:
    """Verifica resultados das tarefas Celery."""
    console.print("\n[bold cyan]🔄 Resultados Celery[/bold cyan]")

    # Últimas 10 tarefas relacionadas a treinamento
    tasks = TaskResult.objects.filter(
        task_name__icontains="treinamento"
    ).order_by("-date_done")[:10]

    if not tasks:
        console.print("[yellow]  Nenhuma tarefa de treinamento encontrada[/]")
        return

    table = Table(show_header=True)
    table.add_column("Task ID (short)")
    table.add_column("Task Name")
    table.add_column("Status")
    table.add_column("Date Done")
    table.add_column("Result (truncated)")

    for task in tasks:
        # Truncar ID e resultado para visualização
        task_id_short = task.task_id[:8] + "..." if task.task_id else "N/A"
        result_preview = str(task.result)[:50] if task.result else "N/A"

        # Colorir status
        status = task.status or "N/A"
        if status == "SUCCESS":
            status = f"[green]{status}[/green]"
        elif status == "FAILURE":
            status = f"[red]{status}[/red]"
        elif status == "PENDING":
            status = f"[yellow]{status}[/yellow]"

        table.add_row(
            task_id_short,
            task.task_name or "N/A",
            status,
            str(task.date_done) if task.date_done else "N/A",
            result_preview,
        )

    console.print(table)

    # Verificar tarefas com falha
    failed = TaskResult.objects.filter(
        task_name__icontains="treinamento", status="FAILURE"
    )
    if failed.exists():
        console.print(f"\n[bold red]❌ Tarefas com falha: {failed.count()}[/]")
        for f in failed[:3]:
            console.print(f"\n[red]Traceback ({f.task_id[:8]}):[/]")
            console.print(
                f.traceback[:500] if f.traceback else "Sem traceback"
            )


def check_redis_connection() -> None:
    """Verifica conexão com Redis."""
    console.print("\n[bold cyan]🔗 Verificando conexão Redis[/bold cyan]")
    try:
        from django.conf import settings

        broker_url = settings.CELERY_BROKER_URL
        console.print(f"  - Broker URL: {broker_url}")

        import redis

        # Parse URL básico
        r = redis.from_url(broker_url)
        r.ping()
        console.print("[green]  ✓ Conexão com Redis OK[/]")
    except Exception as e:
        console.print(f"[red]  ✗ Erro ao conectar com Redis: {e}[/]")


def check_celery_inspect() -> None:
    """Inspeciona estado do worker Celery."""
    console.print("\n[bold cyan]👷 Estado do Worker Celery[/bold cyan]")
    try:
        from smart_core_assistant_painel.app.core.celery import app

        inspect = app.control.inspect()

        # Verificar workers ativos
        active_workers = inspect.active() or {}
        if active_workers:
            console.print("[green]  ✓ Workers ativos encontrados[/]")
            for worker, tasks in active_workers.items():
                console.print(
                    f"    - {worker}: {len(tasks)} tarefas em execução"
                )
        else:
            console.print("[yellow]  ⚠️ Nenhum worker ativo encontrado![/]")

        # Verificar filas registradas
        registered = inspect.registered() or {}
        if registered:
            for worker, task_list in registered.items():
                treinamento_tasks = [
                    t for t in task_list if "treinamento" in t.lower()
                ]
                if treinamento_tasks:
                    console.print(
                        f"\n[cyan]  Tasks de treinamento registradas ({worker}):[/]"
                    )
                    for t in treinamento_tasks:
                        console.print(f"    • {t}")

    except Exception as e:
        console.print(f"[red]  ✗ Erro ao inspecionar Celery: {e}[/]")


if __name__ == "__main__":
    console.print("[bold magenta]═══ Diagnóstico de Vetorização ═══[/]")

    check_treinamentos()
    check_celery_results()
    check_redis_connection()
    check_celery_inspect()

    console.print("\n[bold magenta]═══ Fim do Diagnóstico ═══[/]\n")
