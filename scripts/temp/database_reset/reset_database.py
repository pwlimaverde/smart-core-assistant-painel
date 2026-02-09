#!/usr/bin/env python3
"""
Script principal para reset completo do banco de dados.

Este script:
1. Para e remove containers Docker
2. Remove volumes do PostgreSQL e Redis
3. Limpa migrações antigas
4. Recria estrutura do banco
5. Aplica migrações do zero
"""

import subprocess
import time
from pathlib import Path


def run_command(cmd):
    """Executa um comando e retorna o resultado."""
    print(f"🔄 Executando: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {e}")
        if e.stderr:
            print(f"Erro detalhado: {e.stderr}")
        return False


def main():
    """Função principal de reset do banco."""
    print("🚀 Iniciando reset completo do banco de dados")
    print("=" * 50)

    # 1. Parar containers
    print("\n🛑 Parando containers...")
    run_command("docker compose down")
    time.sleep(2)

    # 2. Remover volumes
    print("\n🗑️ Removendo volumes...")
    run_command("docker volume rm postgres_django_data 2>nul || true")
    run_command("docker volume rm redis_data 2>nul || true")
    run_command("docker volume prune -f")
    time.sleep(2)

    # 3. Remover migrações antigas
    print("\n🧹 Removendo migrações antigas...")
    base_path = Path(__file__).parent.parent

    # Configuração de apps e arquivos a preservar
    apps_clean = [
        (
            "src/smart_core_assistant_painel/app/clientes/migrations",
            ["__init__.py", "0001_initial.py", "0002_enable_pgvector_extension.py"],
        ),
        (
            "src/smart_core_assistant_painel/app/notion_sync/migrations",
            ["__init__.py", "0001_initial.py"],
        ),
        (
            "src/smart_core_assistant_painel/app/operacional/migrations",
            ["__init__.py"],
        ),
        (
            "src/smart_core_assistant_painel/app/atendimentos/migrations",
            ["__init__.py"],
        ),
        ("src/smart_core_assistant_painel/app/usuarios/migrations", ["__init__.py"]),
        (
            "src/smart_core_assistant_painel/app/treinamento/migrations",
            ["__init__.py"],
        ),
        ("src/smart_core_assistant_painel/app/core/migrations", ["__init__.py"]),
    ]

    total_removed = 0
    for path, preserve in apps_clean:
        full_path = base_path / path
        if full_path.exists():
            files = list(full_path.glob("*.py"))
            for f in files:
                if f.name not in preserve:
                    print(f"  🗑️ Removendo: {f.name}")
                    f.unlink()
                    total_removed += 1

    print(f"✅ {total_removed} migrações removidas")

    # 4. Iniciar containers
    print("\n🚀 Iniciando containers...")
    run_command("docker compose up -d")
    time.sleep(10)

    # 5. Aplicar migrações do zero
    print("\n🏗️ Aplicando migrações...")
    run_command("uv run task migrate --fake-initial")
    run_command("uv run task migrate")

    # 6. Criar superusuário
    print("\n👤 Criando superusuário...")
    run_command("uv run task createsuperuser")

    print("\n" + "=" * 50)
    print("🎉 Reset do banco concluído com sucesso!")
    print("\n📋 Próximos passos:")
    print("  1. Acesse o admin: http://localhost:8000/admin/")
    print("  2. Login com o superusuário criado")
    print("  3. Configure as senhas dos usuários")
    print("  4. Configure a integração com Notion se necessário")
    print("\n⚠️ Verifique se:")
    print("  - pgvector está habilitado no PostgreSQL")
    print("  - Todas as migrações foram aplicadas corretamente")
    print("  - Os serviços estão rodando sem erros")


if __name__ == "__main__":
    main()
