"""
Comando Django para executar migracoes em todos os bancos de tenants.

Util apos alteracoes de schema (ex: VectorField de 1024 para 1536) quando
e necessario aplicar migracoes em todos os tenants cadastrados de uma vez.
"""

from typing import Any

from django.core.management.base import BaseCommand

from smart_core_assistant_painel.app.tenants.models import (
    Tenant,
    TenantDatabase,
)
from smart_core_assistant_painel.app.tenants.services.connection_tester import (
    TenantMigrationRunner,
)


class Command(BaseCommand):
    help = "Executa migracoes Django nos bancos de dados de todos os tenants"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas lista os tenants sem executar migracoes",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            help="Slug de um tenant especifico para migrar (opcional)",
        )
        parser.add_argument(
            "--skip-invalid",
            action="store_true",
            help="Pula tenants com conexao invalida sem interromper",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options.get("dry_run", False)
        specific_tenant: str | None = options.get("tenant")
        skip_invalid: bool = options.get("skip_invalid", False)

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(
            self.style.MIGRATE_HEADING("[*] Migracao em Massa de Tenants")
        )
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))

        # Busca todos os tenants ativos com configuracao de banco
        tenants_query = Tenant.objects.filter(active=True)

        if specific_tenant:
            tenants_query = tenants_query.filter(slug=specific_tenant)

        tenants = tenants_query.select_related("database_config")

        # Filtra apenas tenants com database configurado
        tenants_with_db: list[Tenant] = [
            t for t in tenants if hasattr(t, "database_config")
        ]

        total = len(tenants_with_db)
        self.stdout.write(
            f"\n[i] Encontrados {total} tenant(s) com banco configurado\n"
        )

        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    "Nenhum tenant encontrado com configuracao de banco."
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING("[DRY-RUN] Apenas listando:\n")
            )
            for tenant in tenants_with_db:
                config: TenantDatabase = tenant.database_config  # type: ignore[attr-defined]
                status = "[OK]" if config.connection_valid else "[X]"
                self.stdout.write(
                    f"  {status} {tenant.slug} -> "
                    f"{config.host}:{config.port}/{config.database_name}"
                )
            return

        # Executa migracoes
        success_count = 0
        error_count = 0
        skipped_count = 0

        for idx, tenant in enumerate(tenants_with_db, 1):
            config: TenantDatabase = tenant.database_config  # type: ignore[attr-defined]

            self.stdout.write(f"\n[{idx}/{total}] Processando: {tenant.slug}")
            self.stdout.write(
                f"       Host: {config.host}:{config.port}/{config.database_name}"
            )

            success, message = TenantMigrationRunner.run_migrations(config)

            if success:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"       [OK] {message}"))
            else:
                if skip_invalid:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"       [SKIP] {message}")
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"       [ERRO] {message}")
                    )

        # Resumo final
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING("[i] Resumo da Execucao"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  [OK] Sucesso:  {success_count}")
        if skipped_count > 0:
            self.stdout.write(f"  [SKIP] Pulados:  {skipped_count}")
        if error_count > 0:
            self.stdout.write(f"  [ERRO] Erros:    {error_count}")
        self.stdout.write(f"  [i] Total:    {total}")

        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    "\n[!] Algumas migracoes falharam. "
                    "Verifique os logs acima para detalhes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n[OK] Todas as migracoes foram concluidas com sucesso!"
                )
            )
