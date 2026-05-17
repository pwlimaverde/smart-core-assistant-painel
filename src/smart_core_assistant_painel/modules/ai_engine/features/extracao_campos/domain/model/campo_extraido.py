"""Modelo de domínio para campos extraídos pela IA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CampoExtraido:
    """Representa um campo personalizado extraído da conversa pelo LLM.

    Attributes:
        slug: Identificador do campo (chave em CampoPersonalizado).
        valor: Valor extraído (pode ser str, int, float, bool, list).
        confianca: Score de confiança retornado pelo LLM (0.0 – 1.0).
        encontrado: True se o LLM encontrou o valor na conversa.
    """

    slug: str
    valor: Any
    confianca: float
    encontrado: bool = True

    def __post_init__(self) -> None:
        self.confianca = max(0.0, min(1.0, float(self.confianca)))
