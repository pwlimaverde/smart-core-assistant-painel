"""
Comando para garantir que todos os fluxos tenham boards Trello com webhooks.

Uso: python -m smart_core_assistant_painel.app.manage ensure_trello_boards
"""

from typing import Any

from django.core.management.base import BaseCommand

from smart_core_assistant_painel.app.operacional.models import FluxoAtendimento
from smart_core_assistant_painel.app.tenants.middleware import (
    set_current_tenant,
)
from smart_core_assistant_painel.app.tenants.models import Tenant
from smart_core_assistant_painel.app.trello_sync.models import TrelloBoard
from smart_core_assistant_painel.app.trello_sync.services.flow_sync_service import (
    FlowSyncService,
)
from smart_core_assistant_painel.app.trello_sync.tasks import (
    _ensure_board_webhook,
)


class Command(BaseCommand):
    """Garante boards Trello para todos os fluxos existentes."""

    help = (
        "Garante que todos os FluxoAtendimento tenham board Trello com webhook"
    )

    def handle(self, *args: Any, **options: Any) -> None:
        """Executa o comando."""
        self.stdout.write("=" * 60)
        self.stdout.write("Garantindo boards Trello para fluxos existentes")
        self.stdout.write("=" * 60)

        for tenant in Tenant.objects.filter(is_active=True):
            self.stdout.write(f"\nTenant: {tenant.name} ({tenant.slug})")
            set_current_tenant(tenant)

            for fluxo in FluxoAtendimento.objects.all():
                self._ensure_board_for_fluxo(tenant, fluxo)

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Concluído!"))
        self.stdout.write("=" * 60)

    def _ensure_board_for_fluxo(
        self, tenant: Tenant, fluxo: FluxoAtendimento
    ) -> None:
        """Garante board e webhook para um fluxo."""
        try:
            board = TrelloBoard.objects.get(fluxo=fluxo)
            has_webhook = bool(board.webhook_id)
            self.stdout.write(
                f"  [OK] Fluxo '{fluxo.nome}' tem board: {board.external_id}"
            )
            self.stdout.write(
                f"       Webhook: {'Sim (' + board.webhook_id + ')' if has_webhook else 'Não'}"
            )

            if not has_webhook:
                self.stdout.write("       -> Registrando webhook...")
                try:
                    _ensure_board_webhook(tenant.slug, board)
                    board.refresh_from_db()
                    if board.webhook_id:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"       [OK] Webhook: {board.webhook_id}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                "       [ERRO] Falha ao registrar"
                            )
                        )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"       [ERRO] {e}"))

        except TrelloBoard.DoesNotExist:
            self.stdout.write(
                f"  [--] Fluxo '{fluxo.nome}' SEM board. Criando..."
            )
            try:
                service = FlowSyncService()
                board = service.ensure_board_for_fluxo(fluxo)
                if board:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"       [OK] Board criado: {board.external_id}"
                        )
                    )
                    self.stdout.write("       -> Registrando webhook...")
                    _ensure_board_webhook(tenant.slug, board)
                    board.refresh_from_db()
                    if board.webhook_id:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"       [OK] Webhook: {board.webhook_id}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                "       [!] Webhook não registrado"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR("       [ERRO] Falha ao criar board")
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"       [ERRO] {e}"))
