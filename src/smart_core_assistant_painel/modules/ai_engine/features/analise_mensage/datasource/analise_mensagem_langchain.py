"""Implementação da análise prévia de mensagem com LangChain.

Este módulo fornece uma implementação concreta da interface `AnalisePreviaMensagem`,
utilizando a biblioteca LangChain para realizar a análise.

Classes:
    AnalisePreviaMensagemLangchain: Implementação da análise com LangChain.
"""

from ai_engine.features.analise_mensage.domain.interface.analise_mensagem import (
    AnaliseMensagem,
)


class AnaliseMensagemLangchain(AnaliseMensagem):
    """Implementação da interface AnaliseMensagem usando LangChain.

    Esta classe herda da interface `AnaliseMensagem` e implementa
    a análise de mensagens utilizando a tecnologia LangChain.
    """

    def __init__(
        self,
        resposta_bot: str,
        confiabilidade: float,
    ):
        """Inicializa a análise de mensagem.

        Args:
            resposta_bot (str): Resposta do bot.
            confiabilidade (float): Confiabilidade da resposta do bot.
        """
        super().__init__(resposta_bot=resposta_bot or "", confiabilidade=confiabilidade or 0.0)
