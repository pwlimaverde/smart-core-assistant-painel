#!/usr/bin/env python3
"""Script para gerenciar containers Docker (Data e App).

Permite executar comandos docker compose (up, down, logs, restart)
visando tanto o ambiente local quanto remoto (via DOCKER_HOST).
"""

import os
import subprocess
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Definição das Stacks
STACKS = {
    "data": {
        "file": "docker-compose-data.yml",
        "project": "smartcoreassistant-data",
    },
    "app": {
        "file": "docker-compose-app.yml",
        "project": "smartcoreassistant-app",
    },
}


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


def get_docker_host() -> Optional[str]:
    """Obtém o DOCKER_HOST configurado (se houver).

    Tenta ler:
    1. Argumento de linha de comando (não implementado aqui, focado em env)
    2. Variável de ambiente DOCKER_HOST
    3. Variável de ambiente SMART_CORE_DOCKER_HOST no .env
    """
    # Carrega .env para buscar configuração específica
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    file_vars = load_env(env_file)

    # Priority: Env Var > .env custom var
    host = os.environ.get("DOCKER_HOST")
    if not host:
        host = file_vars.get("SMART_CORE_DOCKER_HOST")

    return host


def run_compose(
    stack: str, command: str, args: List[str], host: Optional[str] = None
) -> int:
    """Executa comando docker compose."""
    if stack not in STACKS:
        print(
            f"ERRO: Stack '{stack}' desconhecida. Use: {', '.join(STACKS.keys())}"
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

    # Prepara ambiente
    env = os.environ.copy()
    if host:
        print(f"--> Executando em Host Remoto: {host}")
        env["DOCKER_HOST"] = host
    else:
        print("--> Executando Localmente")

    print(f"CMD: {' '.join(cmd_list)}")
    print("-" * 48)

    try:
        # Executa
        result = subprocess.run(cmd_list, env=env)
        return result.returncode
    except KeyboardInterrupt:
        print("\nOperação cancelada.")
        return 130
    except Exception as e:
        print(f"ERRO ao executar docker: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Gerenciador Docker Smart Core"
    )
    parser.add_argument(
        "command",
        choices=["up", "down", "restart", "logs", "build", "exec", "ps"],
        help="Comando Docker Compose",
    )
    parser.add_argument(
        "stack",
        choices=["data", "app", "all"],
        help="Stack alvo (data, app ou all)",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Forçar uso de host remoto configurado",
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

    # Correção robusta: Se --remote caiu em extra_args, removemos de lá e ativamos a flag
    # ISSO PRECISA SER FEITO ANTES DE CHECAR args.remote
    if "--remote" in docker_args:
        docker_args.remove("--remote")
        args.remote = True

    # Ajuste para visualização limpa no 'ps'
    if args.command == "ps":
        print_header(f"STATUS (PS) {args.stack}")
    else:
        print_header(f"{args.command} {args.stack}")

    # Determina o host
    host = args.host
    if not host and args.remote:
        host = get_docker_host()
        if not host:
            print(
                "AVISO: Flag --remote usada mas NENHUM host configurado (SMART_CORE_DOCKER_HOST ou DOCKER_HOST). Executando localmente."
            )

    stacks_to_run = []
    if args.stack == "all":
        stacks_to_run = ["data", "app"]
    else:
        stacks_to_run = [args.stack]

    # Mapeamento de comandos simplificados
    docker_cmd = args.command
    docker_args = args.extra_args if args.extra_args else []

    # Correção robusta: Se --remote caiu em extra_args, removemos de lá e ativamos a flag
    if "--remote" in docker_args:
        docker_args.remove("--remote")
        args.remote = True

    if args.command == "up":
        if "-d" not in docker_args:
            docker_args.append("-d")
    elif args.command == "restart":
        # Restart geralmente é para app, 'up -d --build' é melhor para rebuild
        # Mas 'restart' comando nativo apenas reinicia container
        docker_cmd = "restart"
    elif args.command == "build":
        docker_cmd = "up"
        docker_args = ["-d", "--build"]
    elif args.command == "ps":
        # Adiciona formatação se não tiver args
        if not docker_args:
            docker_args = ["-a"]
    elif args.command == "exec":
        # Exec precisa do nome do serviço antes dos argumentos
        # Se não houver serviço especificado, usa django_app como padrão
        if docker_args and docker_args[0] == "--":
            # Remove o "--" se for o primeiro argumento
            docker_args = docker_args[1:]
        # Adiciona django_app como serviço padrão
        docker_args = ["django_app"] + docker_args

    for stack in stacks_to_run:
        print(f"\n>>> Processando Stack: {stack.upper()} <<<")
        code = run_compose(stack, docker_cmd, docker_args, host)
        if code != 0:
            print(f"Falha ao executar {stack}. Código: {code}")
            sys.exit(code)

    print("\nSucesso!")


if __name__ == "__main__":
    main()
