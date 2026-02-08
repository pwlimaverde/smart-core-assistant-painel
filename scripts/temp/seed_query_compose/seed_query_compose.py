# -*- coding: utf-8 -*-
"""
Script de seed para gerar o arquivo 'dados_query_compose_bd.json' na raiz do projeto
a partir do arquivo de definição 'docs_dev/informações_treinamento/querys_direcionadas.json'
e popular o banco (QueryCompose) com esses dados.

Uso:
  - Windows/PowerShell (na raiz do repositório):
      python scripts/seed_query_compose/seed_query_compose.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# --------------------------- Configurações de caminhos ---------------------------
THIS_FILE = Path(__file__).resolve()
# Ajuste para chegar à raiz: scripts/seed_query_compose/seed_query_compose.py -> raiz
PROJECT_ROOT = THIS_FILE.parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_JSON = PROJECT_ROOT / "dados_query_compose_bd.json"
INPUT_JSON = (
    PROJECT_ROOT
    / "docs_dev"
    / "informações_treinamento"
    / "querys_direcionadas.json"
)


def load_records() -> List[Dict[str, Any]]:
    if not INPUT_JSON.exists():
        print(f"Erro: Arquivo de entrada não encontrado: {INPUT_JSON}")
        return []

    try:
        data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        print(f"Erro ao ler JSON de entrada: {e}")
        return []


def main() -> None:
    records = load_records()
    if not records:
        print("Nenhum registro encontrado para processar.")
        return

    # 1) Salvar JSON na raiz do projeto (como lista de objetos prontos para inserção)
    OUTPUT_JSON.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Arquivo gerado (lista de registros): {OUTPUT_JSON}")

    # 2) Popular o banco (Django) sem alterar o model
    sys.path.insert(0, str(SRC_DIR))
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "smart_core_assistant_painel.app.core.settings",
    )
    try:
        import django  # type: ignore

        django.setup()
        from smart_core_assistant_painel.app.treinamento.models import (  # type: ignore
            QueryCompose,
        )
    except Exception as e:  # noqa: BLE001
        print(f"Falha ao inicializar Django: {e}")
        return

    total = 0
    for item in records:
        QueryCompose.objects.update_or_create(
            grupo=item["grupo"],
            tag=item["tag"],
            defaults={
                "descricao": item["descricao"],
                "exemplo": item["exemplo"],
                "comportamento": item["comportamento"],
            },
        )
        total += 1
    print(f"Registros QueryCompose afetados: {total}")


if __name__ == "__main__":
    main()
