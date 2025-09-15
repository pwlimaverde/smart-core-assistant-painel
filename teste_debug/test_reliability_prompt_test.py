"""Teste manual de confiabilidade para o caso do horário de funcionamento.

Este script lê o arquivo de prompt de teste, extrai o bloco <contexto_rag>,
monta a pergunta e a resposta fornecidas e calcula a confiabilidade usando a
heurística atual. O resultado deve ser >= 0.8 para ser considerado aceitável.

Execute diretamente com Python (a partir da raiz do projeto):
    uv run python teste_debug/test_reliability_prompt_test.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

# Ajusta o sys.path para permitir import do pacote em src/
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from smart_core_assistant_painel.modules.ai_engine.features.analise_mensage.datasource.analise_mensage_datasource import (  # noqa: E501
    AnaliseMensageDatasource,
)


def read_text(file_path: Path) -> str:
    """Lê todo o conteúdo de um arquivo de texto como string."""
    return file_path.read_text(encoding="utf-8")


def extract_contexto_rag(prompt_text: str) -> str:
    """Extrai o conteúdo entre <contexto_rag> e </contexto_rag>.

    Retorna string vazia caso as tags não sejam encontradas.
    """
    m = re.search(r"<contexto_rag>(.*)</contexto_rag>", prompt_text,
                  flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def load_prompt_context(path: Optional[Path] = None) -> str:
    """Carrega o contexto RAG do arquivo prompt_test.txt.

    Caso um caminho não seja informado, tenta localizar em:
    1) Caminho absoluto passado no enunciado do teste;
    2) Arquivo na raiz do repositório (prompt_test.txt).
    """
    candidates = []
    if path:
        candidates.append(path)
    # Caminho absoluto informado no enunciado (normalizado com /)
    candidates.append(
        Path("c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/"
             "prompt_test.txt")
    )
    # Arquivo na raiz do repositório
    candidates.append(ROOT_DIR / "prompt_test.txt")

    for p in candidates:
        if p.exists():
            return extract_contexto_rag(read_text(p))

    raise FileNotFoundError(
        "Não foi possível localizar o arquivo prompt_test.txt."
    )


def main() -> None:
    """Executa o cálculo de confiabilidade para o cenário informado."""
    rag_context = load_prompt_context()

    user_question = (
        "Boa tarde, tudo bem?\nMeu nome é paulo\n"
        "Qual o horário de funcionamento de vocês?"
    )

    answer_ai = (
        "Olá Paulo, é um prazer conhecê-lo! Estou aqui para ajudá-lo com "
        "qualquer dúvida ou informação que precise.\n\n"
        "Para responder à sua pergunta, o horário de funcionamento da "
        "Fique Bela é:\n\n"
        "- Segunda a Sexta: 09:00 às 18:30\n"
        "- Sábado: 09:00 às 14:00\n"
        "- Domingo: Fechado\n\n"
        "Espero que isso tenha ajudado! Se tiver mais alguma pergunta ou "
        "precisar de mais informações, não hesite em perguntar. Estou aqui "
        "para ajudá-lo."
    )

    ds = AnaliseMensageDatasource()
    score = ds._compute_reliability(  # type: ignore[attr-defined]
        answer=answer_ai,
        rag_context=rag_context,
        user_question=user_question,
    )

    print(f"Confiabilidade calculada: {score:.4f}")

    threshold = 0.8
    assert score >= threshold, (
        f"Score abaixo do mínimo aceitável ({threshold}). "
        f"Obtido: {score:.4f}"
    )

    print("Teste OK: confiabilidade acima do mínimo aceitável.")


if __name__ == "__main__":
    main()