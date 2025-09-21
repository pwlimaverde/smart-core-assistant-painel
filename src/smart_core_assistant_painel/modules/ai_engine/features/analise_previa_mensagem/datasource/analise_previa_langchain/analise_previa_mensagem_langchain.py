"""Implementação da análise prévia de mensagem com LangChain.

Este módulo fornece uma implementação concreta da interface `AnalisePreviaMensagem`,
utilizando a biblioteca LangChain para realizar a análise.

Classes:
    AnalisePreviaMensagemLangchain: Implementação da análise com LangChain.
"""

from typing import Any, Optional

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.interface.analise_previa_mensagem import (
    AnalisePreviaMensagem,
)


class AnalisePreviaMensagemLangchain(AnalisePreviaMensagem):
    """Implementação da interface AnalisePreviaMensagem usando LangChain.

    Esta classe herda da interface `AnalisePreviaMensagem` e implementa
    a análise prévia de mensagens utilizando a tecnologia LangChain.
    """

    def __init__(
        self,
        intent: Optional[list[dict[str, Any]]] = None,
        entities: Optional[list[dict[str, Any]]] = None,
    ):
        """Inicializa a análise prévia da mensagem.

        Args:
            intent (Optional[list[dict[str, Any]]]): Lista de dicionários com
                as intenções detectadas.
            entities (Optional[list[dict[str, Any]]]): Lista de dicionários com
                as entidades extraídas.
        """
        super().__init__(intent=intent or [], entities=entities or [])
