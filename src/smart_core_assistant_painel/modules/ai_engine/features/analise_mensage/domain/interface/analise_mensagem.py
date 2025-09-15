"""Interface abstrata para o resultado da análise prévia de mensagens.

Este módulo define a estrutura de dados que deve ser retornada por qualquer
implementação de análise prévia de mensagens.

Classes:
    AnalisePreviaMensagem: Uma classe base abstrata para os dados da análise.
"""

from abc import ABC
from dataclasses import dataclass


@dataclass
class AnaliseMensagem(ABC):
    """Interface para o resultado da análise de mensagens.

    Attributes:
        resposta_bot (str): A resposta do bot.
        confiabilidade (float): A confiabilidade da resposta do bot.
    """

    resposta_bot: str
    confiabilidade: float
