"""Interface abstrata para o resultado da análise prévia de mensagens.

Este módulo define a estrutura de dados que deve ser retornada por qualquer
implementação de análise prévia de mensagens.

Classes:
    AnalisePreviaMensagem: Uma classe base abstrata para os dados da análise.
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass
class AnalisePreviaMensagem(ABC):
    """Interface para o resultado da análise prévia de mensagens.

    Attributes:
        intent (list[dict[str, Any]]): Uma lista de dicionários, onde cada
            item representa uma intenção detectada. Cada dicionário tem uma
            chave (o tipo da intenção) e um valor (o trecho da mensagem).
        entities (list[dict[str, Any]]): Uma lista de dicionários, onde cada
            item representa uma entidade extraída. Cada dicionário tem uma
            chave (o tipo da entidade) e um valor (o conteúdo extraído).
    """

    intent: list[dict[str, Any]]
    entities: list[dict[str, Any]]
