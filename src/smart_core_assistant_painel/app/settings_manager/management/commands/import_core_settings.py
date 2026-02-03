import json
from pathlib import Path
from typing import Any, cast

from django.core.management.base import BaseCommand, CommandError

from smart_core_assistant_painel.app.settings_manager.models import (
    CoreSettings,
)
from smart_core_assistant_painel.app.tenants.utils.encryption import (
    encrypt_value,
)


class Command(BaseCommand):
    help = "Importa configurações globais (CoreSettings) a partir de um JSON."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--input",
            "-i",
            required=True,
            help="Caminho do JSON exportado (ou lista de itens).",
        )
        parser.add_argument(
            "--use-resolved-value",
            action="store_true",
            help="Usa 'resolved_value' (se existir) como value no banco.",
        )
        parser.add_argument(
            "--encrypt-when-flagged",
            action="store_true",
            help="Se encrypted=true, criptografa o value antes de salvar.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida e conta itens, mas não grava no banco.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        input_opt = options.get("input")
        if not input_opt or not isinstance(input_opt, str):
            raise CommandError("--input é obrigatório.")

        input_path = Path(input_opt)
        use_resolved_value: bool = bool(options.get("use_resolved_value"))
        encrypt_when_flagged: bool = bool(options.get("encrypt_when_flagged"))
        dry_run: bool = bool(options.get("dry_run"))

        if not input_path.exists():
            raise CommandError(f"Arquivo não encontrado: {input_path}")

        raw = input_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise CommandError(f"JSON inválido: {e}") from e

        items: list[dict[str, Any]]
        if isinstance(data, dict) and "core_settings" in data:
            data_dict = cast(dict[str, Any], data)
            core_settings: Any = data_dict["core_settings"]
            if not isinstance(core_settings, list):
                raise CommandError("'core_settings' deve ser uma lista.")
            items = cast(list[dict[str, Any]], core_settings)
        elif isinstance(data, list):
            items = cast(list[dict[str, Any]], data)
        elif isinstance(data, dict):
            items = [
                {"key": str(k), "value": v, "encrypted": False}
                for k, v in cast(dict[Any, Any], data).items()
            ]
        else:
            raise CommandError(
                "Formato inválido. Use o JSON gerado pelo export_core_settings."
            )

        created = 0
        updated = 0
        processed = 0

        for item in items:
            key = item.get("key")
            if not key or not isinstance(key, str):
                raise CommandError("Item sem 'key' válida.")

            encrypted_flag = bool(item.get("encrypted", False))
            description = item.get("description") or ""
            if not isinstance(description, str):
                description = str(description)

            value: Any = item.get("value", "")
            if use_resolved_value and "resolved_value" in item:
                value = item.get("resolved_value", "")
                if encrypted_flag and not encrypt_when_flagged:
                    raise CommandError(
                        f"'{key}' está marcado como encrypted=true, "
                        "mas --encrypt-when-flagged não foi informado."
                    )

            if value is None:
                value_str = ""
            elif isinstance(value, str):
                value_str = value
            else:
                value_str = str(value)

            if encrypt_when_flagged and encrypted_flag and value_str:
                value_str = encrypt_value(value_str)

            processed += 1

            if dry_run:
                continue

            _, was_created = CoreSettings.objects.update_or_create(
                key=key,
                defaults={
                    "value": value_str,
                    "encrypted": encrypted_flag,
                    "description": description,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry-run concluído: {processed} itens validados."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Import concluído: {processed} processados "
                f"({created} criados, {updated} atualizados)."
            )
        )
