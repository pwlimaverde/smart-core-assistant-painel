#!/usr/bin/env python3
"""Script para sincronizar CoreSettings com o banco PostgreSQL em PRODUÇÃO.

Este script conecta ao servidor Hostinger via SSH e executa comandos SQL
no container Docker do PostgreSQL para gerenciar as configurações globais.

Modos disponíveis:
- dump: Exporta configurações do banco remoto para JSON local
- restore: Importa configurações do JSON local para o banco remoto

Uso:
    uv run python scripts/config_global/sync_coresettings_prod.py dump
    uv run python scripts/config_global/sync_coresettings_prod.py restore
    uv run python scripts/config_global/sync_coresettings_prod.py restore --yes
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

DATA_FILE = Path(__file__).parent / "coresettings.json"
ENV_DEPLOY_FILE = Path(__file__).parent.parent.parent / ".env.deploy"
ENV_PROD_FILE = Path(__file__).parent.parent.parent / ".env.prod"


def load_env_file(env_path: Path) -> dict[str, str]:
    """Carrega variáveis de um arquivo .env."""
    env_vars: dict[str, str] = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip("\"'")
    return env_vars


def get_config() -> dict[str, str]:
    """Carrega configurações do .env.deploy e .env.prod."""
    deploy = load_env_file(ENV_DEPLOY_FILE)
    prod = load_env_file(ENV_PROD_FILE)

    if not deploy.get("HOSTINGER_SSH_HOST"):
        print("❌ Erro: .env.deploy não encontrado ou incompleto.")
        print(f"   Esperado em: {ENV_DEPLOY_FILE}")
        sys.exit(1)

    if not prod.get("POSTGRES_DB"):
        print("❌ Erro: .env.prod não encontrado ou incompleto.")
        print(f"   Esperado em: {ENV_PROD_FILE}")
        sys.exit(1)

    return {
        # SSH Hostinger
        "ssh_host": deploy.get("HOSTINGER_SSH_HOST", ""),
        "ssh_user": deploy.get("HOSTINGER_SSH_USER", "root"),
        "ssh_port": deploy.get("HOSTINGER_SSH_PORT", "22"),
        "ssh_alias": deploy.get("HOSTINGER_SSH_ALIAS", ""),
        # PostgreSQL Produção
        "db_container": prod.get(
            "POSTGRES_HOST", "smartcoreassistant_postgres"
        ),
        "db_name": prod.get("POSTGRES_DB", "smart_core_db"),
        "db_user": prod.get("POSTGRES_USER", "postgres"),
    }


def escape_sql(value: Optional[str]) -> str:
    """Escapa valor para SQL."""
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def run_ssh_psql(
    sql: str,
    config: dict[str, str],
    raw_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Executa SQL no banco remoto via SSH + docker exec.

    Args:
        sql: Comando SQL a executar
        config: Dicionário com configurações de conexão
        raw_output: Se True, retorna saída sem formatação

    Returns:
        Resultado do subprocess
    """
    psql_flags = "-t -A" if raw_output else ""

    # Usa alias SSH se disponível, senão usa host direto
    if config["ssh_alias"]:
        ssh_target = config["ssh_alias"]
    else:
        ssh_target = f"{config['ssh_user']}@{config['ssh_host']}"

    # Monta comando docker exec para psql
    docker_cmd = (
        f"docker exec -i {config['db_container']} "
        f"psql -U {config['db_user']} -d {config['db_name']} {psql_flags}"
    )

    cmd = ["ssh", ssh_target, docker_cmd]

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
    """Exporta dados do banco de produção para JSON local."""
    config = get_config()

    print("=" * 60)
    print("  EXPORTAR CoreSettings (PRODUÇÃO → local)")
    print("=" * 60)
    print(f"\n🌐 SSH: {config['ssh_user']}@{config['ssh_host']}")
    print(f"🐳 Container: {config['db_container']}")
    print(f"🗄️  Database: {config['db_name']}")
    print()

    query = (
        "SELECT json_agg(row_to_json(t)) FROM settings_manager_coresettings t;"
    )
    result = run_ssh_psql(query, config, raw_output=True)

    if result.returncode != 0:
        print(f"❌ Erro SSH/SQL: {result.stderr}")
        sys.exit(1)

    json_str = result.stdout.strip()
    if not json_str or json_str == "":
        print("⚠️  Nenhum dado encontrado na tabela.")
        return

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSON: {e}")
        print(f"   Resposta: {json_str[:200]}...")
        sys.exit(1)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(data)} configurações exportadas para {DATA_FILE.name}")


def restore_action(yes: bool = False) -> None:
    """Importa dados do JSON local para o banco de produção."""
    if not DATA_FILE.exists():
        print(f"❌ Arquivo não encontrado: {DATA_FILE}")
        sys.exit(1)

    config = get_config()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 60)
    print("  RESTAURAR CoreSettings (local → PRODUÇÃO)")
    print("=" * 60)
    print(f"\n🌐 SSH: {config['ssh_user']}@{config['ssh_host']}")
    print(f"🐳 Container: {config['db_container']}")
    print(f"🗄️  Database: {config['db_name']}")
    print(f"📄 Arquivo: {DATA_FILE.name}")
    print(f"📊 Total: {len(data)} registros")
    print()

    if not yes:
        print("⚠️  ATENÇÃO: Você está prestes a modificar o banco de PRODUÇÃO!")
        confirm = input("   Confirma? (s/N): ").strip().lower()
        if confirm != "s":
            print("❌ Operação cancelada.")
            return

    # Gera SQL UPSERT para cada configuração
    sqls: list[str] = []
    for item in data:
        key = escape_sql(item.get("key", ""))
        value = escape_sql(item.get("value", ""))
        encrypted = "true" if item.get("encrypted") else "false"
        description = escape_sql(item.get("description", ""))

        sqls.append(
            f"""
INSERT INTO settings_manager_coresettings (key, value, encrypted, description, created_at, updated_at)
VALUES ({key}, {value}, {encrypted}, {description}, NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    encrypted = EXCLUDED.encrypted,
    description = EXCLUDED.description,
    updated_at = NOW();"""
        )

    result = run_ssh_psql("\n".join(sqls), config)

    if result.returncode == 0:
        print(f"\n✅ {len(data)} configurações restauradas com sucesso!")
    else:
        print(f"\n⚠️  Avisos/Erros: {result.stderr}")
        if result.stdout:
            print(f"   Saída: {result.stdout}")


def test_connection() -> None:
    """Testa a conexão SSH e acesso ao container PostgreSQL."""
    config = get_config()

    print("=" * 60)
    print("  TESTE DE CONEXÃO")
    print("=" * 60)
    print(f"\n🌐 SSH: {config['ssh_user']}@{config['ssh_host']}")
    print(f"🐳 Container: {config['db_container']}")
    print(f"🗄️  Database: {config['db_name']}")
    print()

    # Testa conexão simples
    result = run_ssh_psql("SELECT 1;", config, raw_output=True)

    if result.returncode == 0 and "1" in result.stdout:
        print("✅ Conexão bem-sucedida!")

        # Conta registros existentes
        count_result = run_ssh_psql(
            "SELECT COUNT(*) FROM settings_manager_coresettings;",
            config,
            raw_output=True,
        )
        if count_result.returncode == 0:
            count = count_result.stdout.strip()
            print(f"📊 Registros na tabela: {count}")
    else:
        print(f"❌ Falha na conexão: {result.stderr}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sincroniza CoreSettings com banco de PRODUÇÃO (Hostinger)"
    )
    parser.add_argument(
        "action",
        choices=["dump", "restore", "test"],
        help="Ação: dump (exportar), restore (importar), test (testar conexão)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Confirma automaticamente (bypass prompt)",
    )
    args = parser.parse_args()

    if args.action == "dump":
        dump_action()
    elif args.action == "restore":
        restore_action(args.yes)
    else:
        test_connection()


if __name__ == "__main__":
    main()
