#!/usr/bin/env python3
"""Script para gerenciar containers Docker em 4 stacks modulares.

Stacks disponíveis:
- data: PostgreSQL + Redis (dados persistentes)
- app: Django + Migrate (aplicação principal)
- workers: Celery Worker + Beat (processamento assíncrono)
- infra: Cloudflared + Flower (infraestrutura/túnel)

Permite executar comandos docker compose remotamente via DOCKER_HOST.
"""

import os
import subprocess
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# ============================================
# Diretório dos compose files (relativo à raiz)
# ============================================
COMPOSE_DIR = "docker/compose"
DEFAULT_ENV_FILE = ".env"

# ============================================
# Definição das 4 Stacks Modulares
# ============================================
STACKS: Dict[str, Dict[str, str]] = {
    "data": {
        "file": f"{COMPOSE_DIR}/data.yml",
        "project": "smart-core-data",
        "description": "PostgreSQL + Redis",
    },
    "app": {
        "file": f"{COMPOSE_DIR}/app.yml",
        "project": "smart-core-app",
        "description": "Django App + Migrate",
    },
    "workers": {
        "file": f"{COMPOSE_DIR}/workers.yml",
        "project": "smart-core-workers",
        "description": "Celery Worker + Beat",
    },
    "infra": {
        "file": f"{COMPOSE_DIR}/infra.yml",
        "project": "smart-core-infra",
        "description": "Cloudflared + Flower",
    },
}

# Ordem de inicialização (dependências respeitadas)
STARTUP_ORDER = ["data", "app", "workers", "infra"]
# Ordem de desligamento (inversa)
SHUTDOWN_ORDER = ["infra", "workers", "app", "data"]


def print_header(title: str) -> None:
    """Exibe cabeçalho formatado."""
    print("=" * 48)
    print(f"  SMART CORE - DOCKER MANAGER: {title.upper()}")
    print("=" * 48)
    print()


def load_env(env_path: Path) -> Dict[str, str]:
    """Carrega variáveis de ambiente de um arquivo."""
    env_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip("\"'")
    return env_vars


def resolve_env_path(env_file: str) -> Path:
    """Resolve caminho absoluto do arquivo de ambiente."""
    project_root = Path(__file__).parent.parent.parent
    env_path = Path(env_file)
    if not env_path.is_absolute():
        env_path = project_root / env_path
    return env_path


def get_docker_host(env_path: Path) -> Optional[str]:
    """Obtém o DOCKER_HOST configurado.

    Tenta ler:
    1. Variável de ambiente DOCKER_HOST
    2. Variável SMART_CORE_DOCKER_HOST no .env
    """
    file_vars = load_env(env_path)

    host = os.environ.get("DOCKER_HOST")
    if not host:
        host = file_vars.get("SMART_CORE_DOCKER_HOST")

    return host


def run_compose(
    stack: str,
    command: str,
    args: List[str],
    host: Optional[str] = None,
    env_path: Optional[Path] = None,
) -> int:
    """Executa comando docker compose."""
    if stack not in STACKS:
        print(
            f"ERRO: Stack '{stack}' desconhecida. "
            f"Use: {', '.join(STACKS.keys())}"
        )
        return 1

    config = STACKS[stack]
    file_path = config["file"]
    project_name = config["project"]

    # Monta o comando base
    cmd_list = [
        "docker",
        "compose",
        "-f",
        file_path,
        "-p",
        project_name,
        command,
    ] + args

    # Prepara ambiente - carrega arquivo de ambiente e adiciona ao ambiente
    env = os.environ.copy()

    resolved_env_path = env_path or resolve_env_path(DEFAULT_ENV_FILE)
    local_env_vars = load_env(resolved_env_path)

    # Adiciona variáveis do arquivo ao ambiente (sobrescreve se já existir)
    for key, value in local_env_vars.items():
        env[key] = value

    # Permite alternar o env_file dos compose files via variável de ambiente.
    # Exemplo: .env (dev-local) ou .env.prod (produção).
    env["SMARTCORE_ENV_FILE"] = resolved_env_path.name

    if host:
        print(f"--> Executando em: {host}")
        env["DOCKER_HOST"] = host
    else:
        print("--> AVISO: Executando localmente (sem DOCKER_HOST)")
    print(f"--> Arquivo de ambiente: {resolved_env_path}")

    print(f"CMD: {' '.join(cmd_list)}")
    print("-" * 48)

    try:
        result = subprocess.run(cmd_list, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\nOperação cancelada.")
        return 130
    except Exception as e:
        print(f"ERRO ao executar docker: {e}")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gerenciador Docker Smart Core (4 Stacks)"
    )
    parser.add_argument(
        "command",
        choices=[
            "up",
            "down",
            "restart",
            "logs",
            "build",
            "exec",
            "ps",
            "run",
        ],
        help="Comando Docker Compose",
    )
    parser.add_argument(
        "stack",
        choices=["data", "app", "workers", "infra", "all"],
        help="Stack alvo (data, app, workers, infra ou all)",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Usar host remoto configurado no .env",
    )
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help=(
            "Arquivo de ambiente para carregar variáveis "
            "(padrão: .env). Ex.: .env.prod"
        ),
    )
    parser.add_argument("--host", help="Sobrescrever DOCKER_HOST")
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Argumentos extras para o comando docker",
    )

    args = parser.parse_args()

    # Mapeamento de comandos simplificados
    docker_cmd = args.command
    docker_args = args.extra_args if args.extra_args else []

    # Correção: Se --remote caiu em extra_args, removemos
    if "--remote" in docker_args:
        docker_args.remove("--remote")
        args.remote = True

    # Remove separador -- se presente no início
    if docker_args and docker_args[0] == "--":
        docker_args = docker_args[1:]

    # Header
    if args.command == "ps":
        print_header(f"STATUS (PS) {args.stack}")
    else:
        print_header(f"{args.command} {args.stack}")

    # Determina o host
    env_path = resolve_env_path(args.env_file)

    host = args.host
    if not host and args.remote:
        host = get_docker_host(env_path)
        if not host:
            print(
                "ERRO: Flag --remote usada mas SMART_CORE_DOCKER_HOST "
                "não está configurado no arquivo de ambiente"
            )
            sys.exit(1)

    # Define stacks a processar
    if args.stack == "all":
        if args.command in ["down", "stop"]:
            stacks_to_run = SHUTDOWN_ORDER
        else:
            stacks_to_run = STARTUP_ORDER
    else:
        stacks_to_run = [args.stack]

    # Ajusta argumentos específicos por comando
    if args.command == "up":
        if "-d" not in docker_args:
            docker_args.append("-d")
    elif args.command == "restart":
        docker_cmd = "restart"
    elif args.command == "build":
        docker_cmd = "up"
        docker_args = ["-d", "--build"]
    elif args.command == "ps":
        if not docker_args:
            docker_args = ["-a"]
    elif args.command == "exec":
        default_services = {
            "app": "django_app",
            "workers": "celery_worker",
            "data": "postgres",
            "infra": "cloudflared",
        }
        service = default_services.get(args.stack, "django_app")
        docker_args = [service] + docker_args

    for stack in stacks_to_run:
        print(f"\n>>> Processando Stack: {stack.upper()} <<<")
        print(f"    ({STACKS[stack]['description']})")
        code = run_compose(
            stack, docker_cmd, docker_args, host, env_path=env_path
        )
        if code != 0:
            print(f"Falha ao executar {stack}. Código: {code}")
            sys.exit(code)

    print("\nSucesso!")


if __name__ == "__main__":
    main()
