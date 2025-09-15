"""Teste manual de confiabilidade.

Este script lê o arquivo de prompt de teste, extrai o bloco <contexto_rag>,
monta cenários de pergunta e resposta e calcula a confiabilidade usando a
heurística atual.

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


def run_scenario(description: str, user_question: str, answer_ai: str, rag_context: str) -> float:
    """Executa um cenário e imprime o score calculado."""
    ds = AnaliseMensageDatasource()
    score = ds._compute_reliability(  # type: ignore[attr-defined]
        answer=answer_ai,
        rag_context=rag_context,
        user_question=user_question,
    )
    print(f"\n[{description}] Confiabilidade calculada: {score:.4f}")
    return score


def main() -> None:
    """Executa o cálculo de confiabilidade para dois cenários."""
    rag_context = load_prompt_context()

    # Cenário 1: Setor/ano com transferência injustificada => score esperado 0.0
    user_question_1 = (
        "Quais é o setor que a empresa atua?\n"
        "Qual foi o ano de fundação?"
    )
    answer_ai_1 = (
        "Boa tarde, Paulo!\n\n"
        "A Fique Bela é uma boutique de cosméticos, portanto, o setor que a empresa atua é o de beleza e cosméticos.\n\n"
        "A empresa foi fundada em março de 2025.\n\n"
        "Vou transferir seu atendimento para o setor responsável para que possam fornecer mais informações e atender às suas necessidades."
    )
    score1 = run_scenario(
        description="Setor/Ano com transferência injustificada",
        user_question=user_question_1,
        answer_ai=answer_ai_1,
        rag_context=rag_context,
    )
    assert score1 == 0.0, (
        f"Esperado score 0.0 para transferência injustificada; obtido {score1:.4f}"
    )

    # Cenário 2: Horário de funcionamento, sem contexto no RAG => score baixo
    user_question_2 = (
        "Boa tarde, tudo bem?\nMeu nome é paulo\n"
        "Qual o horário de funcionamento de vocês?"
    )
    answer_ai_2 = (
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
    score2 = run_scenario(
        description="Horário sem contexto explícito no RAG",
        user_question=user_question_2,
        answer_ai=answer_ai_2,
        rag_context=rag_context,
    )
    # Com a nova heurística, esperamos score baixo quando a resposta não está no contexto
    assert score2 < 0.5, (
        f"Esperado score baixo (<0.5) quando não há suporte no RAG; obtido {score2:.4f}"
    )

    print("\nTeste OK: cenários validados conforme política de confiabilidade.")


if __name__ == "__main__":
    main()