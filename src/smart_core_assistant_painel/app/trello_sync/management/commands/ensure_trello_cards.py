"""
Comando Django para garantir que todos os atendimentos ativos tenham
um card Trello associado.

Util para corrigir atendimentos que foram criados antes da etapa ser
definida, ou quando o TrelloCard não foi criado por algum motivo.
"""

from typing import Any

from django.core.management.base import BaseCommand

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.tenants.middleware import (
    set_current_tenant,
)
from smart_core_assistant_painel.app.tenants.models import Tenant
from smart_core_assistant_painel.app.trello_sync.models import TrelloCard
from smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service import (
    TicketSyncService,
)


class Command(BaseCommand):
    help = "Garante que todos os atendimentos ativos tenham um card Trello"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas lista os atendimentos sem criar cards",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            help="Slug de um tenant específico (opcional)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options.get("dry_run", False)
        specific_tenant: str | None = options.get("tenant")

        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "[*] Sincronização de Cards Trello para Atendimentos"
            )
        )
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 60))

        # Busca tenants
        tenants_query = Tenant.objects.filter(active=True)
        if specific_tenant:
            tenants_query = tenants_query.filter(slug=specific_tenant)

        tenants = tenants_query.select_related("database_config")
        tenants_with_db = [t for t in tenants if hasattr(t, "database_config")]

        if not tenants_with_db:
            self.stdout.write(
                self.style.WARNING(
                    "Nenhum tenant encontrado com banco de dados."
                )
            )
            return

        total_created = 0
        total_skipped = 0
        total_errors = 0

        for tenant in tenants_with_db:
            self.stdout.write(f"\n[Tenant: {tenant.slug}]")
            set_current_tenant(tenant)

            try:
                # Busca atendimentos ativos sem card
                atendimentos = Atendimento.objects.filter(
                    status__in=[
                        StatusAtendimento.FILA,
                        StatusAtendimento.EM_ATENDIMENTO,
                        StatusAtendimento.PENDENCIA,
                    ],
                ).exclude(
                    id__in=TrelloCard.objects.values_list(
                        "atendimento_id", flat=True
                    )
                )

                count = atendimentos.count()
                self.stdout.write(f"  Atendimentos sem card: {count}")

                if count == 0:
                    self.stdout.write(
                        self.style.SUCCESS("  [OK] Todos já têm card")
                    )
                    continue

                if dry_run:
                    for a in atendimentos[:10]:
                        self.stdout.write(
                            f"    - ID {a.id}: etapa={a.etapa_atual_id}"
                        )
                    if count > 10:
                        self.stdout.write(f"    ... e mais {count - 10}")
                    continue

                # Cria cards
                service = TicketSyncService()
                for atendimento in atendimentos:
                    if not atendimento.etapa_atual_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f"    [SKIP] ID {atendimento.id}: sem etapa"
                            )
                        )
                        total_skipped += 1
                        continue

                    try:
                        card = service.ensure_card_for_atendimento(atendimento)
                        if card:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"    [OK] ID {atendimento.id}: "
                                    f"card {card.external_id} criado"
                                )
                            )
                            total_created += 1
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"    [SKIP] ID {atendimento.id}: "
                                    "card não criado (já existia ou sem etapa)"
                                )
                            )
                            total_skipped += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"    [ERRO] ID {atendimento.id}: {e}"
                            )
                        )
                        total_errors += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  [ERRO] Falha no tenant: {e}")
                )
                total_errors += 1

        # Resumo
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING("[i] Resumo"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  [OK] Cards criados:  {total_created}")
        self.stdout.write(f"  [SKIP] Ignorados:    {total_skipped}")
        self.stdout.write(f"  [ERRO] Erros:        {total_errors}")

        if total_errors > 0:
            self.stdout.write(
                self.style.ERROR(
                    "\n[!] Alguns cards falharam. Verifique os logs acima."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n[OK] Sincronização concluída com sucesso!"
                )
            )
