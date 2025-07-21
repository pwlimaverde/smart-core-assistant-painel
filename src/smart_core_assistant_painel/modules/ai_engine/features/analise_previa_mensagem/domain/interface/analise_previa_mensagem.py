from abc import ABC
from dataclasses import dataclass
from typing import Any

@dataclass
class AnalisePreviaMensagem(ABC):
    """Interface para análise prévia de mensagens.

    O formato esperado é:
    - intent: Lista de dicionários onde cada item tem uma chave (tipo da intenção)
      e valor (conteúdo extraído da mensagem)
    - entities: Lista de dicionários onde cada item tem uma chave (tipo da entidade)
      e valor (valor extraído da mensagem)
    """
    intent: list[dict[str, Any]]
    entities: list[dict[str, Any]]
