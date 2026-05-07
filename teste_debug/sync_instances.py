"""Script para sincronizar EvolutionInstance → AppInstance
no tenant existente de testes.

Uso:
    uv run python teste_debug/sync_instances.py

O que faz:
    1. Lista todas as EvolutionInstance ativas
    2. Para cada uma, cria ou atualiza o AppInstance
       correspondente pela api_key
    3. Vincula ao departamento "Atendimento" se existir
    4. Exibe relatório do que foi feito
"""

import os
import sys
from pathlib import Path

# Configura Django antes de importar models
src_dir = str(Path(__file__).resolve().parent.parent / "src")
sys.path.insert(0, src_dir)
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.settings",
)

import django  # noqa: E402

django.setup()

from smart_core_assistant_painel.app.evolution_sync.models import (  # noqa: E402
    EvolutionInstance,
)
from smart_core_assistant_painel.app.operacional.models import (  # noqa: E402
    AppInstance,
    Departamento,
)


def sync_instances() -> None:
    """Sincroniza todas as EvolutionInstance ativas
    com AppInstance."""
    instances = EvolutionInstance.objects.filter(active=True)
    print(f"\n{'=' * 60}")
    print(f"  EvolutionInstances ativas encontradas: {instances.count()}")
    print(f"{'=' * 60}\n")

    if not instances.exists():
        print("  Nenhuma instância Evolution ativa encontrada.")
        return

    # Busca departamento "Atendimento" para vincular
    dept_atendimento = Departamento.objects.filter(
        nome__icontains="atendimento", ativo=True
    ).first()

    if dept_atendimento:
        print(
            f"  Departamento encontrado: {dept_atendimento.nome} "
            f"(ID: {dept_atendimento.id})\n"
        )
    else:
        print("  ⚠ Departamento 'Atendimento' não encontrado.\n")

    for inst in instances:
        print(f"  → {inst.name}")
        print(f"    api_key: {inst.api_key[:12]}...")
        print(f"    resposta_bot: {inst.resposta_bot}")
        print(f"    connection_state: {inst.connection_state}")

        if not inst.api_key:
            print("    ✗ Sem api_key, pulando.\n")
            continue

        app_inst, created = AppInstance.objects.update_or_create(
            api_key=inst.api_key,
            defaults={
                "channel": "evolution_api",
                "display_name": inst.name,
                "resposta_bot": inst.resposta_bot,
                "active": inst.active,
            },
        )

        # Vincular ao departamento se não tem nenhum
        if dept_atendimento and not app_inst.departamento:
            app_inst.departamento = dept_atendimento
            app_inst.save(update_fields=["departamento"])
            print(
                f"    ✓ Vinculado ao departamento: "
                f"{dept_atendimento.nome}"
            )

        status = "CRIADO" if created else "ATUALIZADO"
        print(f"    ✓ AppInstance {status} (ID: {app_inst.id})\n")

    # Relatório final
    print(f"{'=' * 60}")
    print("  Relatório Final:")
    print(
        f"  AppInstances ativas: "
        f"{AppInstance.objects.filter(active=True).count()}"
    )
    for ai in AppInstance.objects.filter(active=True):
        dept_name = ai.departamento.nome if ai.departamento else "—"
        owner_name = ai.owner.nome if ai.owner else "—"
        print(
            f"    • {ai.display_name or ai.api_key[:12]} "
            f"| dept={dept_name} "
            f"| owner={owner_name} "
            f"| bot={ai.resposta_bot}"
        )
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    sync_instances()
