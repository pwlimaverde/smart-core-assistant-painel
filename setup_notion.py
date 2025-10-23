"""
Script para configurar databases no Notion com persistência no Django.

Este script cria automaticamente os databases de Contatos e Clientes
no Notion com todas as propriedades necessárias e salva os IDs no
model NotionDatabaseConfig para persistência permanente.

O script realiza as seguintes operações:
1. Valida configurações do ambiente (.env)
2. Cria database de Contatos no Notion com todas as propriedades
3. Cria database de Clientes no Notion com todas as propriedades
4. Salva IDs e schemas no NotionDatabaseConfig (banco Django)
5. Salva IDs no .env como backup (opcional)
6. Valida que tudo foi configurado corretamente

Para executar:
    python setup_notion.py

Requisitos:
    - NOTION_TOKEN configurado no .env
    - NOTION_PAGE_ID configurado no .env
    - Django configurado e migrations aplicadas
    - Integração Notion com permissões adequadas

Após a execução:
    Execute validate_notion_setup.py para confirmar que tudo está OK:
    python validate_notion_setup.py
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório src ao path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Configura o Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)

import django

django.setup()

# Importa e executa o setup
from smart_core_assistant_painel.app.notion_sync.scripts import (
    setup_notion_databases,
)


def main() -> None:
    """
    Função principal que executa o setup dos databases no Notion.

    Esta função:
    - Chama o setup_notion_databases que cria os databases
    - Persiste as configurações no NotionDatabaseConfig
    - Salva IDs no .env como backup
    - Exibe resumo das operações realizadas

    Raises:
        SystemExit: Se houver erro na configuração ou execução.
    """
    try:
        # Executa o setup completo
        result = setup_notion_databases()

        # Se chegou aqui, deu tudo certo
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(0)

    except Exception as e:
        print(f"\n\nErro ao executar setup: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
