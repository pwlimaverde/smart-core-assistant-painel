"""
Script para testar construção de atendimentos usando manage.py shell.
"""

import os
import sys

# Adicionar path correto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Script para executar no Django shell
SCRIPT = """
import asyncio
from app.notion_sync.scripts.script_constructor_notion import run_construction_atendimentos

try:
    print('🧪 Iniciando teste de construção de atendimentos...')
    asyncio.run(run_construction_atendimentos())
    print('✅ Construção de atendimentos concluída com sucesso!')
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
"""

# Executar via manage.py shell
if __name__ == "__main__":
    import subprocess

    # Comando para executar o script
    cmd = [
        sys.executable,
        "manage.py",
        "shell",
        "--command",
        SCRIPT
    ]

    # Mudar para o diretório correto
    ui_dir = os.path.join(os.path.dirname(__file__), "src", "smart_core_assistant_painel", "app", "ui")

    try:
        result = subprocess.run(cmd, cwd=ui_dir, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Erros:")
            print(result.stderr)
        print(f"Exit code: {result.returncode}")
    except Exception as e:
        print(f"Erro ao executar: {e}")
