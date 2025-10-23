"""
Scripts utilitários para gerenciamento da integração com Notion.

Este módulo contém scripts para:
- Criar databases no Notion
- Validar estrutura dos databases
- Sincronizar dados existentes
- Limpar dados de teste
"""

from .setup_notion_databases import setup_notion_databases

__all__ = [
    "setup_notion_databases",
]
