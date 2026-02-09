from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from loguru import logger

from smart_core_assistant_painel.app.settings_manager.models import (
    CoreSettings,
)
from smart_core_assistant_painel.app.tenants.utils.encryption import (
    encrypt_value,
)


def _find_repo_root(start: Path) -> Path:
    """Encontra a raiz do repo (onde existe pyproject.toml)."""
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def _looks_like_fernet_token(value: str) -> bool:
    # Tokens Fernet tipicamente começam com 'gAAAA'.
    return value.startswith("gAAAA")


# Mapeamento parcial (core_key -> env var). Usamos apenas para override opcional
# em desenvolvimento, mantendo o CoreSettings como fonte principal.
_ENV_BY_CORE_KEY: dict[str, str] = {
    "groq_api_key": "GROQ_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "huggingface_api_key": "HUGGINGFACE_API_KEY",
    "llm_class": "LLM_CLASS",
    "model": "MODEL",
    "llm_temperature": "LLM_TEMPERATURE",
    "embeddings_class": "EMBEDDINGS_CLASS",
    "embeddings_model": "EMBEDDINGS_MODEL",
    "chunk_size": "CHUNK_SIZE",
    "chunk_overlap": "CHUNK_OVERLAP",
    "similarity_threshold": "SIMILARITY_THRESHOLD",
    "vector_distance_threshold": "VECTOR_DISTANCE_THRESHOLD",
    "time_cache": "TIME_CACHE",
    "prompt_system_analise_conteudo": "PROMPT_SYSTEM_ANALISE_CONTEUDO",
    "prompt_human_analise_conteudo": "PROMPT_HUMAN_ANALISE_CONTEUDO",
    "prompt_system_melhoria_conteudo": "PROMPT_SYSTEM_MELHORIA_CONTEUDO",
    "prompt_human_melhoria_conteudo": "PROMPT_HUMAN_MELHORIA_CONTEUDO",
    "prompt_system_analise_previa_mensagem": "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM",
    "prompt_human_analise_previa_mensagem": "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM",
    "prompt_intent_system": "PROMPT_INTENT_SYSTEM",
    "prompt_intent_footer": "PROMPT_INTENT_FOOTER",
    "prompt_template_user_rag": "PROMPT_TEMPLATE_USER_RAG",
    "prompt_regras_resposta": "PROMPT_REGRAS_RESPOSTA",
    "prompt_regras_transferencia": "PROMPT_REGRAS_TRANSFERENCIA",
}


class Command(BaseCommand):
    help = (
        "Bootstrap de CoreSettings: cria chaves globais ausentes no banco a partir "
        "do backup scripts/config_global/coresettings.json (ou arquivo informado). "
        "Não sobrescreve valores existentes por padrão."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--input",
            "-i",
            help=(
                "Caminho do JSON (lista) com CoreSettings. "
                "Default: scripts/config_global/coresettings.json"
            ),
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Sobrescreve valores existentes no CoreSettings.",
        )
        parser.add_argument(
            "--no-encrypt-when-flagged",
            action="store_true",
            help=(
                "Não criptografa valores quando encrypted=true no arquivo. "
                "Útil apenas para debug."
            ),
        )
        parser.add_argument(
            "--no-env-override",
            action="store_true",
            help=(
                "Não sobrescreve valores do arquivo com variáveis de ambiente (quando existirem)."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        input_opt = options.get("input")
        overwrite: bool = bool(options.get("overwrite"))
        encrypt_when_flagged: bool = not bool(
            options.get("no_encrypt_when_flagged", False)
        )
        use_env_override: bool = not bool(
            options.get("no_env_override", False)
        )

        repo_root = _find_repo_root(Path(__file__).resolve())
        default_path = (
            repo_root / "scripts" / "config_global" / "coresettings.json"
        )
        input_path = Path(input_opt) if input_opt else default_path

        if not input_path.exists():
            raise CommandError(f"Arquivo não encontrado: {input_path}")

        raw = input_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise CommandError(f"JSON inválido: {e}") from e

        if not isinstance(data, list):
            raise CommandError(
                "Formato inválido: esperado uma lista de itens."
            )

        created = 0
        updated = 0
        skipped = 0

        for item in data:
            if not isinstance(item, dict):
                continue

            key = item.get("key")
            if not key or not isinstance(key, str):
                continue

            encrypted_flag = bool(item.get("encrypted", False))
            description = item.get("description") or ""
            if not isinstance(description, str):
                description = str(description)

            value: Any = item.get("value", "")
            value_str = "" if value is None else str(value)

            if use_env_override:
                env_name = _ENV_BY_CORE_KEY.get(key)
                if env_name:
                    env_val = os.environ.get(env_name, "").strip()
                    if env_val:
                        value_str = env_val

            if encrypted_flag and encrypt_when_flagged and value_str:
                # Evita dupla-criptografia quando o valor já parece token Fernet.
                if not _looks_like_fernet_token(value_str):
                    try:
                        value_str = encrypt_value(value_str)
                    except Exception as e:
                        # Segurança: não logar valor; apenas o key.
                        logger.warning(
                            "Falha ao criptografar CoreSetting "
                            f"(key={key}). Salvando como texto puro. "
                            f"Tipo={type(e).__name__}, Mensagem={e}"
                        )
                        encrypted_flag = False

            if overwrite:
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
                continue

            # Modo default: não sobrescrever configurações existentes.
            _, was_created = CoreSettings.objects.get_or_create(
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
                skipped += 1

        msg = (
            f"Bootstrap CoreSettings concluído: {created} criados, "
            f"{updated} atualizados, {skipped} ignorados."
        )
        self.stdout.write(self.style.SUCCESS(msg))
