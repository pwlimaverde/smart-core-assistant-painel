import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from django.core.management.base import BaseCommand, CommandError

from smart_core_assistant_painel.app.settings_manager.models import (
    CoreSettings,
)


class Command(BaseCommand):
    help = "Exporta as configurações globais (CoreSettings) para um JSON."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--output",
            "-o",
            default=None,
            help="Caminho do arquivo de saída. Se omitido, imprime no stdout.",
        )
        parser.add_argument(
            "--pretty",
            action="store_true",
            help="Formata o JSON com indentação para leitura humana.",
        )
        parser.add_argument(
            "--include-decrypted",
            action="store_true",
            help="Inclui um campo 'resolved_value' com valor descriptografado (se aplicável).",
        )
        parser.add_argument(
            "--skip-decrypt-errors",
            action="store_true",
            help="Se falhar ao descriptografar, define resolved_value como null ao invés de abortar.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        output: Optional[str] = options.get("output")
        pretty: bool = bool(options.get("pretty"))
        include_decrypted: bool = bool(options.get("include_decrypted"))
        skip_decrypt_errors: bool = bool(options.get("skip_decrypt_errors"))

        exported_at = datetime.now(timezone.utc).isoformat()
        items: list[dict[str, Any]] = []

        for obj in CoreSettings.objects.all().order_by("key"):
            row: dict[str, Any] = {
                "key": obj.key,
                "value": obj.value,
                "encrypted": bool(obj.encrypted),
                "description": obj.description or "",
                "updated_at": obj.updated_at.isoformat()
                if getattr(obj, "updated_at", None)
                else None,
                "created_at": obj.created_at.isoformat()
                if getattr(obj, "created_at", None)
                else None,
            }

            if include_decrypted:
                try:
                    row["resolved_value"] = obj.get_value()
                except Exception as e:
                    if skip_decrypt_errors:
                        row["resolved_value"] = None
                    else:
                        raise CommandError(
                            f"Falha ao descriptografar '{obj.key}': {e}"
                        )

            items.append(row)

        payload = {
            "version": 1,
            "exported_at": exported_at,
            "core_settings": items,
        }

        indent = 2 if pretty else None
        json_text = json.dumps(payload, ensure_ascii=False, indent=indent)

        if output:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_text, encoding="utf-8")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Export concluído: {len(items)} itens em {out_path}"
                )
            )
        else:
            self.stdout.write(json_text)
