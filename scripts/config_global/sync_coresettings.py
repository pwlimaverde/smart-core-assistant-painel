#!/usr/bin/env python3
"""Script para exportar ou restaurar CoreSettings no banco PostgreSQL remoto.

Este script possui dois modos:
- dump: Exporta configurações do banco remoto para JSON local
- restore: Importa configurações do JSON local para o banco remoto

Uso:
    uv run python scripts/config_global/sync_coresettings.py dump
    uv run python scripts/config_global/sync_coresettings.py restore
    uv run python scripts/config_global/sync_coresettings.py restore --yes
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Configurações do ambiente remoto
REMOTE_HOST = "192.168.3.127"
REMOTE_USER = "pwlim"
REMOTE_CONTAINER = "smartcoreassistant_postgres"
DATA_FILE = Path(__file__).parent / "coresettings.json"


def load_env() -> dict[str, str]:
    """Carrega variáveis de ambiente do arquivo .env do projeto."""
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    env_vars = {}

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip("\"'")
    return env_vars


def escape_sql(value: str) -> str:
    """Escapa valor para SQL."""
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def run_ssh_psql(
    sql: str, db_user: str, db_name: str, raw_output: bool = False
) -> subprocess.CompletedProcess:
    """Executa SQL no banco remoto via SSH + docker exec."""
    psql_flags = "-t -A" if raw_output else ""
    cmd = [
        "ssh",
        f"{REMOTE_USER}@{REMOTE_HOST}",
        f"docker exec -i {REMOTE_CONTAINER} psql -U {db_user} -d {db_name} {psql_flags}",
    ]
    return subprocess.run(
        cmd,
        input=sql,
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )


def dump_action() -> None:
    """Exporta dados do banco remoto para JSON local."""
    env = load_env()
    db_user = env.get("POSTGRES_USER", "postgres")
    db_name = env.get("POSTGRES_DB", "smart_core_db")

    print("=" * 60)
    print("  EXPORTAR CoreSettings (remoto → local)")
    print("=" * 60)
    print(f"\nHost: {REMOTE_USER}@{REMOTE_HOST}")
    print(f"Container: {REMOTE_CONTAINER}")
    print()

    query = (
        "SELECT json_agg(row_to_json(t)) FROM settings_manager_coresettings t;"
    )
    result = run_ssh_psql(query, db_user, db_name, raw_output=True)

    if result.returncode != 0:
        print(f"❌ Erro: {result.stderr}")
        sys.exit(1)

    json_str = result.stdout.strip()
    if not json_str:
        print("⚠️  Nenhum dado encontrado.")
        return

    data = json.loads(json_str)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ {len(data)} configurações exportadas para {DATA_FILE.name}")


def restore_action(yes: bool = False) -> None:
    """Importa dados do JSON local para o banco remoto."""
    if not DATA_FILE.exists():
        print(f"❌ Arquivo não encontrado: {DATA_FILE}")
        sys.exit(1)

    env = load_env()
    db_user = env.get("POSTGRES_USER", "postgres")
    db_name = env.get("POSTGRES_DB", "smart_core_db")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 60)
    print("  RESTAURAR CoreSettings (local → remoto)")
    print("=" * 60)
    print(f"\nHost: {REMOTE_USER}@{REMOTE_HOST}")
    print(f"Container: {REMOTE_CONTAINER}")
    print(f"Arquivo: {DATA_FILE.name}")
    print(f"Total: {len(data)} registros")
    print()

    if not yes:
        confirm = input("⚠️  Confirma? (s/N): ").strip().lower()
        if confirm != "s":
            print("Cancelado.")
            return

    # Gera SQL UPSERT
    sqls = []
    for item in data:
        key = escape_sql(item.get("key", ""))
        value = escape_sql(item.get("value", ""))
        encrypted = "true" if item.get("encrypted") else "false"
        description = escape_sql(item.get("description", ""))

        sqls.append(f"""
INSERT INTO settings_manager_coresettings (key, value, encrypted, description, created_at, updated_at)
VALUES ({key}, {value}, {encrypted}, {description}, NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value, encrypted = EXCLUDED.encrypted,
    description = EXCLUDED.description, updated_at = NOW();""")

    result = run_ssh_psql("\n".join(sqls), db_user, db_name)

    if result.returncode == 0:
        print(f"\n✓ {len(data)} configurações restauradas!")
    else:
        print(f"\n⚠️  Avisos: {result.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza CoreSettings")
    parser.add_argument("action", choices=["dump", "restore"], help="Ação")
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Confirma automaticamente"
    )
    args = parser.parse_args()

    if args.action == "dump":
        dump_action()
    else:
        restore_action(args.yes)


if __name__ == "__main__":
    main()
