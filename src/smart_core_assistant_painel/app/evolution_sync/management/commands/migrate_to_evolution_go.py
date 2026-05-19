"""[INT-EVO-MGT-001] Management command: migrate_to_evolution_go.

Migra instâncias Evolution de ``api_version="v2"`` para ``api_version="go"``
de forma idempotente e opt-in, respeitando o rollback imediato via flag no
admin (sem necessidade de redeploy).

Uso típico:

    # Dry-run — lista o que seria alterado:
    uv run manage.py migrate_to_evolution_go --dry-run

    # Migrar todas as instâncias v2 ativas:
    uv run manage.py migrate_to_evolution_go

    # Migrar apenas instâncias de um tenant específico:
    uv run manage.py migrate_to_evolution_go --tenant-id <uuid>

    # Migrar apenas uma instância pelo nome:
    uv run manage.py migrate_to_evolution_go --instance-name atendimento

    # Migrar e já configurar media_storage_backend=s3 (Evolution Go com MinIO):
    uv run manage.py migrate_to_evolution_go --set-media-backend s3

    # Definir a lista de eventos assinados (subscribed_events):
    uv run manage.py migrate_to_evolution_go --subscribed-events MESSAGE MESSAGE_UPDATE PRESENCE CONNECTION CONTACTS QRCODE
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from smart_core_assistant_painel.app.evolution_sync.models import (
    APIVersion,
    EvolutionInstance,
    MediaStorageBackend,
)


class Command(BaseCommand):
    """Migração idempotente de instâncias Evolution v2 → Go."""

    help = (
        "Migra EvolutionInstance(s) de api_version='v2' para 'go'. "
        "Idempotente: instâncias já em 'go' são ignoradas. "
        "Use --dry-run para inspecionar sem salvar."
    )

    # ------------------------------------------------------------------ #
    # Argumentos
    # ------------------------------------------------------------------ #

    def add_arguments(self, parser: Any) -> None:  # type: ignore[override]
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Imprime o que seria alterado sem gravar no banco.",
        )
        parser.add_argument(
            "--tenant-id",
            type=str,
            default=None,
            metavar="UUID",
            help="Filtrar pelo UUID do tenant proprietário das instâncias.",
        )
        parser.add_argument(
            "--instance-name",
            type=str,
            default=None,
            metavar="NAME",
            help="Filtrar pelo nome exato (case-insensitive) da instância.",
        )
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            default=False,
            help="Incluir instâncias com active=False (padrão: apenas ativas).",
        )
        parser.add_argument(
            "--set-media-backend",
            type=str,
            choices=[MediaStorageBackend.NONE, MediaStorageBackend.S3],
            default=None,
            metavar="BACKEND",
            help=(
                "Também atualiza media_storage_backend. "
                "Valores: 'none' (download on-demand) | 's3' (Evolution Go com MinIO/S3)."
            ),
        )
        parser.add_argument(
            "--subscribed-events",
            nargs="*",
            default=None,
            metavar="EVENT",
            help=(
                "Substitui subscribed_events das instâncias migradas. "
                "Ex: MESSAGE MESSAGE_UPDATE PRESENCE CONNECTION CONTACTS QRCODE"
            ),
        )

    # ------------------------------------------------------------------ #
    # Execução
    # ------------------------------------------------------------------ #

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        tenant_id_raw: str | None = options["tenant_id"]
        instance_name: str | None = options["instance_name"]
        include_inactive: bool = options["include_inactive"]
        set_media_backend: str | None = options["set_media_backend"]
        subscribed_events: list[str] | None = options["subscribed_events"]

        # ---- validar tenant_id ---------------------------------------- #
        tenant_uuid: uuid.UUID | None = None
        if tenant_id_raw:
            try:
                tenant_uuid = uuid.UUID(tenant_id_raw)
            except ValueError:
                raise CommandError(
                    f"--tenant-id inválido: '{tenant_id_raw}' não é um UUID válido."
                )

        # ---- construir queryset --------------------------------------- #
        qs = EvolutionInstance.objects.filter(api_version=APIVersion.V2)

        if not include_inactive:
            qs = qs.filter(active=True)

        if tenant_uuid is not None:
            qs = qs.filter(tenant_id=tenant_uuid)

        if instance_name:
            qs = qs.filter(name__iexact=instance_name)

        total_candidates = qs.count()

        if total_candidates == 0:
            self.stdout.write(
                self.style.WARNING(
                    "Nenhuma instância v2 encontrada com os filtros fornecidos. "
                    "Verifique se já foram migradas ou ajuste os filtros."
                )
            )
            return

        # ---- resumo antes da operação --------------------------------- #
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n{'[DRY-RUN] ' if dry_run else ''}Migração Evolution v2 → Go"
            )
        )
        self.stdout.write(f"  Instâncias candidatas : {total_candidates}")
        if set_media_backend:
            self.stdout.write(f"  media_storage_backend  : {set_media_backend}")
        if subscribed_events is not None:
            self.stdout.write(
                f"  subscribed_events      : {json.dumps(subscribed_events)}"
            )
        self.stdout.write("")

        # ---- iterar e migrar ----------------------------------------- #
        migrated = 0
        skipped = 0
        errors = 0

        for instance in qs.order_by("id"):
            try:
                self._migrate_instance(
                    instance=instance,
                    dry_run=dry_run,
                    set_media_backend=set_media_backend,
                    subscribed_events=subscribed_events,
                )
                migrated += 1
            except Exception as exc:
                errors += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"  ERRO ao migrar '{instance.name}' (id={instance.pk}): {exc}"
                    )
                )

        # ---- relatório final ----------------------------------------- #
        self.stdout.write("")
        status_style = self.style.SUCCESS if errors == 0 else self.style.WARNING
        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            status_style(
                f"{prefix}Concluído — "
                f"migradas: {migrated} | "
                f"puladas: {skipped} | "
                f"erros: {errors}"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    "\nNenhuma alteração foi gravada. "
                    "Execute sem --dry-run para aplicar."
                )
            )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _migrate_instance(
        self,
        instance: EvolutionInstance,
        dry_run: bool,
        set_media_backend: str | None,
        subscribed_events: list[str] | None,
    ) -> None:
        """Migra uma instância individual de v2 → Go."""
        update_fields: list[str] = ["api_version"]

        instance.api_version = APIVersion.GO

        if set_media_backend is not None:
            instance.media_storage_backend = set_media_backend
            update_fields.append("media_storage_backend")

        if subscribed_events is not None:
            instance.subscribed_events = subscribed_events
            update_fields.append("subscribed_events")

        line = (
            f"  {'(dry-run) ' if dry_run else ''}"
            f"[id={instance.pk}] {instance.name!r}"
        )
        if instance.tenant_id:
            line += f" (tenant={instance.tenant_id})"
        line += " → api_version='go'"
        if set_media_backend:
            line += f", media_storage_backend='{set_media_backend}'"
        if subscribed_events is not None:
            line += f", subscribed_events={json.dumps(subscribed_events)}"

        self.stdout.write(self.style.MIGRATE_LABEL(line))

        if not dry_run:
            instance.save(update_fields=update_fields)
