#!/usr/bin/env python3
"""Script para carregar fixtures no PostgreSQL remoto.

Este script carrega variáveis de ambiente, testa a conectividade
com o PostgreSQL e executa "manage.py loaddata" para as fixtures
no diretório fixtures/dev.

Padrões replicados do migrar_remoto.py.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


def print_header() -> None:
    """Exibe o cabeçalho do script."""
    print("=" * 48)
    print("  SMART CORE ASSISTANT - LOADDATA (BANCO REMOTO)")
    print("=" * 48)
    print()


def load_env_file(env_path: Path) -> Dict[str, str]:
    """Carrega variáveis de ambiente de um arquivo .env.

    Args:
        env_path: Caminho para o arquivo .env

    Returns:
        Dicionário com as variáveis carregadas
    """
    env_vars: Dict[str, str] = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip("\"'" )
    return env_vars


def setup_environment() -> Dict[str, str]:
    """Configura as variáveis de ambiente necessárias.

    Returns:
        Dicionário com as variáveis de ambiente configuradas
    """
    defaults: Dict[str, str] = {
        "POSTGRES_HOST": "192.168.3.127",
        "POSTGRES_PORT": "5436",
        "POSTGRES_DB": "smart_core_db",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres123",
        "REDIS_HOST": "192.168.3.127",
        "REDIS_PORT": "6382",
    }

    env_vars: Dict[str, str] = {
        key: os.environ.get(key, default) for key, default in defaults.items()
    }

    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if not env_file.exists():
        env_file = Path(__file__).parent / ".env"

    if env_file.exists():
        file_vars = load_env_file(env_file)
        env_vars.update(file_vars)

    for key, value in env_vars.items():
        os.environ[key] = value

    return env_vars


def test_connectivity(host: str, port: int, timeout: int = 120) -> bool:
    """Testa a conectividade TCP com o servidor PostgreSQL.

    Args:
        host: Endereço do servidor
        port: Porta do servidor
        timeout: Timeout total em segundos

    Returns:
        True se a conexão for bem-sucedida, False caso contrário
    """
    print("[2/4] Testando conectividade com o PostgreSQL remoto...")

    max_attempts = timeout // 3

    for attempt in range(max_attempts):
        try:
            with socket.create_connection((host, port), timeout=5):
                print("\u2713 Conectividade OK")
                print()
                return True
        except (socket.error, socket.timeout):
            if attempt < max_attempts - 1:
                time.sleep(3)
            continue

    print(f"ERRO: Conexão com {host}:{port} indisponível.")
    return False


def build_fixture_paths(project_root: Path) -> List[Path]:
    """Monta a lista de caminhos das fixtures a carregar."""
    fixtures_dir = project_root / "fixtures" / "dev"
    return [
        fixtures_dir / "departamentos.json",
        fixtures_dir / "atendentes.json",
        fixtures_dir / "contatos.json",
        fixtures_dir / "atendimentos.json",
    ]


def run_loaddata(fixtures: List[Path]) -> Tuple[bool, List[Path]]:
    """Executa loaddata para cada fixture.

    Args:
        fixtures: Lista de caminhos das fixtures

    Returns:
        Tuple de (sucesso_global, fixtures_falhas)
    """
    print("[3/4] Carregando fixtures no banco remoto...")

    project_root = Path(__file__).parent.parent
    original_cwd = os.getcwd()

    failures: List[Path] = []

    try:
        os.chdir(project_root)

        manage_path = (
            project_root
            / "src"
            / "smart_core_assistant_painel"
            / "app"
            / "ui"
            / "manage.py"
        )

        for fixture in fixtures:
            if not fixture.exists():
                print(f"AVISO: Fixture não encontrada: {fixture}")
                failures.append(fixture)
                continue

            print(f" - Carregando: {fixture.name}")
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    str(manage_path),
                    "loaddata",
                    str(fixture),
                ],
                capture_output=False,
                text=True,
            )

            if result.returncode != 0:
                print(f"ERRO ao carregar {fixture.name}")
                failures.append(fixture)
            else:
                print(f"\u2713 Fixture carregada: {fixture.name}")

        success = len(failures) == 0
        return success, failures

    finally:
        os.chdir(original_cwd)


def show_counts() -> None:
    """Exibe contagem de registros após carga para conferência rápida."""
    project_root = Path(__file__).parent.parent
    manage_path = (
        project_root
        / "src"
        / "smart_core_assistant_painel"
        / "app"
        / "ui"
        / "manage.py"
    )

    print()
    print("[4/4] Conferindo contagens pós-carga...")
    subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(manage_path),
            "shell",
            "-c",
            (
                "from smart_core_assistant_painel.app.ui.operacional.models "
                "import Departamento, Atendente; "
                "from smart_core_assistant_painel.app.ui.clientes.models "
                "import Contato; "
                "from smart_core_assistant_painel.app.ui.atendimentos.models "
                "import Atendimento; "
                "print('Departamentos:', Departamento.objects.count()); "
                "print('Atendentes:', Atendente.objects.count()); "
                "print('Contatos:', Contato.objects.count()); "
                "print('Atendimentos:', Atendimento.objects.count());"
            ),
        ],
        capture_output=False,
        text=True,
    )


def main() -> int:
    """Função principal do script.

    Returns:
        Código de saída (0 para sucesso, 1 para erro)
    """
    try:
        print_header()

        env_vars = setup_environment()
        host = env_vars["POSTGRES_HOST"]
        port = int(env_vars["POSTGRES_PORT"])
        print(f"[1/4] Alvo do banco: {host}:{port}")

        if not test_connectivity(host, port):
            return 1

        project_root = Path(__file__).parent.parent
        fixtures = build_fixture_paths(project_root)
        success, failures = run_loaddata(fixtures)

        if not success:
            print()
            print("Algumas fixtures falharam:")
            for fx in failures:
                print(f" - {fx}")
            return 1

        show_counts()
        print()
        print("Concluído.")
        return 0

    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        return 1
    except Exception as e:
        print(f"ERRO: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
