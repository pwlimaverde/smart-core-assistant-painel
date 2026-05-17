#!/usr/bin/env python3
"""Marca todos os atendimentos ativos de um tenant como 'resolvido'.

Uso (dentro do container em produção):
    docker exec smartcoreassistant_app \
        python scripts/atendimentos/resolver_todos_atendimentos.py \
        [--tenant SLUG] [--dry-run]

Argumentos opcionais:
    --tenant SLUG   Slug do tenant (padrão: primeiro tenant ativo com banco)
    --dry-run       Apenas lista os atendimentos sem alterar

Exemplo:
    docker exec smartcoreassistant_app \
        python scripts/atendimentos/resolver_todos_atendimentos.py \
        --tenant paulo-ecoprint
"""

import argparse
import os
import sys

# Garante que o manage.py possa ser encontrado via DJANGO_SETTINGS_MODULE
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.settings",
)

import django  # noqa: E402

django.setup()

from django.utils import timezone  # noqa: E402

from smart_core_assistant_painel.app.tenants.models import Tenant  # noqa: E402
from smart_core_assistant_painel.app.tenants.services.connection_tester import (  # noqa: E402
    TenantMigrationRunner,
)


def main(tenant_slug: str | None, dry_run: bool) -> None:
    print("=" * 60)
    print("  RESOLVER TODOS OS ATENDIMENTOS DO TENANT")
    print("=" * 60)

    # Localiza o tenant
    qs = Tenant.objects.filter(active=True)
    if tenant_slug:
        qs = qs.filter(slug=tenant_slug)

    tenants_with_db = [
        t for t in qs.select_related("database_config")
        if hasattr(t, "database_config")
    ]

    if not tenants_with_db:
        print(f"[ERRO] Nenhum tenant encontrado (slug={tenant_slug!r}).")
        sys.exit(1)

    tenant = tenants_with_db[0]
    print(f"\nTenant : {tenant.slug} | {tenant.name}")

    # Configura conexão dinâmica para o banco do tenant
    db_config = tenant.database_config  # type: ignore[attr-defined]
    alias = TenantMigrationRunner.configure_tenant_database(db_config)
    print(f"Database alias: {alias}")
    print(f"Host: {db_config.host}:{db_config.port}/{db_config.database_name}")

    # Importa APÓS setup do Django
    from smart_core_assistant_painel.app.atendimentos.models import (
        Atendimento,
        StatusAtendimento,
    )

    STATUS_ATIVOS = [
        StatusAtendimento.FILA,
        StatusAtendimento.EM_ATENDIMENTO,
        StatusAtendimento.PENDENCIA,
    ]

    ativos_qs = Atendimento.objects.using(alias).filter(status__in=STATUS_ATIVOS)
    total = ativos_qs.count()

    print(f"\nAtendimentos ativos encontrados: {total}")
    if total == 0:
        print("Nada a fazer.")
        return

    if dry_run:
        print("\n[DRY-RUN] Os seguintes atendimentos seriam resolvidos:")
        for atd in ativos_qs.values("id", "status", "data_inicio")[:50]:
            print(f"  id={atd['id']} status={atd['status']} data_inicio={atd['data_inicio']}")
        if total > 50:
            print(f"  ... e mais {total - 50} atendimentos.")
        return

    # Executa o update em lote (sem disparar signals ou métodos do modelo)
    agora = timezone.now()
    atualizados = ativos_qs.update(
        status=StatusAtendimento.RESOLVIDO,
        data_fim=agora,
    )

    print(f"\n[OK] {atualizados} atendimento(s) marcados como 'resolvido'.")
    print(f"     data_fim = {agora.isoformat()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resolve todos os atendimentos ativos de um tenant."
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default=None,
        help="Slug do tenant (padrão: primeiro tenant ativo com banco configurado)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lista sem modificar",
    )
    args = parser.parse_args()
    main(tenant_slug=args.tenant, dry_run=args.dry_run)
