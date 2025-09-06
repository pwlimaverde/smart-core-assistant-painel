#!/usr/bin/env python3
"""Script para aplicar migrações no PostgreSQL remoto.

Este script replica a funcionalidade do migrar_remoto.bat,
carregando variáveis de ambiente, testando conectividade
e aplicando migrações Django no banco remoto.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict


def print_header() -> None:
    """Exibe o cabeçalho do script."""
    print("="*48)
    print("  SMART CORE ASSISTANT - MIGRAR (BANCO REMOTO)")
    print("="*48)
    print()


def load_env_file(env_path: Path) -> Dict[str, str]:
    """Carrega variáveis de ambiente de um arquivo .env.
    
    Args:
        env_path: Caminho para o arquivo .env
        
    Returns:
        Dicionário com as variáveis carregadas
    """
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars


def setup_environment() -> Dict[str, str]:
    """Configura as variáveis de ambiente necessárias.
    
    Returns:
        Dicionário com as variáveis de ambiente configuradas
    """
    # Valores padrão
    defaults = {
        'POSTGRES_HOST': '192.168.3.127',
        'POSTGRES_PORT': '5436',
        'POSTGRES_DB': 'smart_core_db',
        'POSTGRES_USER': 'postgres',
        'POSTGRES_PASSWORD': 'postgres123',
        'REDIS_HOST': '192.168.3.127',
        'REDIS_PORT': '6382'
    }
    
    # Carrega do sistema operacional primeiro
    env_vars = {key: os.environ.get(key, default) for key, default in defaults.items()}
    
    # Tenta carregar do .env na raiz do projeto
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    
    if not env_file.exists():
        # Fallback para .env na pasta scripts
        env_file = Path(__file__).parent / '.env'
    
    if env_file.exists():
        file_vars = load_env_file(env_file)
        env_vars.update(file_vars)
    
    # Define as variáveis no ambiente atual
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
    print(f"[2/3] Testando conectividade com o PostgreSQL remoto...")
    
    max_attempts = timeout // 3
    
    for attempt in range(max_attempts):
        try:
            with socket.create_connection((host, port), timeout=5):
                print("✓ Conectividade OK")
                print()
                return True
        except (socket.error, socket.timeout):
            if attempt < max_attempts - 1:
                time.sleep(3)
            continue
    
    print(f"ERRO: Conexão com {host}:{port} indisponível.")
    return False


def run_migrations() -> bool:
    """Executa as migrações Django.
    
    Returns:
        True se as migrações foram aplicadas com sucesso, False caso contrário
    """
    print("[3/3] Aplicando migrações no banco remoto...")
    
    # Muda para o diretório raiz do projeto
    project_root = Path(__file__).parent.parent
    original_cwd = os.getcwd()
    
    try:
        os.chdir(project_root)
        
        # Executa as migrações
        result = subprocess.run(
            ["uv", "run", "task", "migrate"],
            capture_output=False,
            text=True
        )
        
        if result.returncode != 0:
            print("ERRO: Falha ao executar migrações.")
            return False
        
        print()
        print("Conferindo pendências com showmigrations...")
        
        # Executa showmigrations para verificar o status
        show_result = subprocess.run(
            ["uv", "run", "python", "src/smart_core_assistant_painel/app/ui/manage.py", "showmigrations"],
            capture_output=False,
            text=True
        )
        
        if show_result.returncode != 0:
            print("AVISO: showmigrations retornou erro (verifique logs acima).")
        else:
            print("✓ Migrações aplicadas com sucesso.")
        
        return True
        
    finally:
        os.chdir(original_cwd)


def main() -> int:
    """Função principal do script.
    
    Returns:
        Código de saída (0 para sucesso, 1 para erro)
    """
    try:
        print_header()
        
        # Configura as variáveis de ambiente
        env_vars = setup_environment()
        
        postgres_host = env_vars['POSTGRES_HOST']
        postgres_port = int(env_vars['POSTGRES_PORT'])
        
        print(f"[1/3] Alvo do banco: {postgres_host}:{postgres_port}")
        
        # Testa conectividade
        if not test_connectivity(postgres_host, postgres_port):
            return 1
        
        # Executa migrações
        if not run_migrations():
            return 1
        
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