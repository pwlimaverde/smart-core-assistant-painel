"""
Mapeador de dados para o modelo MensagemSync.

Este módulo foca em converter uma instância de Mensagem em um formato de
bloco de conteúdo para a API do Notion, para que possa ser anexado a uma
página de Atendimento.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.notion_sync.models import MensagemSync


class MensagemMapper:
    """
    Classe responsável por mapear e transformar dados da Mensagem.
    """

    @staticmethod
    def to_notion_block(sync_instance: "MensagemSync") -> dict:
        """
        Converte uma instância de MensagemSync para um bloco do tipo "callout"
        da API do Notion.

        Args:
            sync_instance: A instância do modelo de sincronização da mensagem.

        Returns:
            Um dicionário representando um bloco de conteúdo do Notion.
        """
        mensagem = sync_instance.mensagem
        remetente = mensagem.get_remetente_display()
        timestamp = mensagem.timestamp.strftime("%d/%m/%Y %H:%M")

        # Define ícone e cor com base no remetente
        if mensagem.remetente == "cliente":
            icon = {"emoji": "👤"}
            color = "gray_background"
            remetente_nome = sync_instance.atendimento_sync.atendimento.contato.nome_contato
        elif mensagem.remetente == "atendente":
            icon = {"emoji": "👩‍💼"}
            color = "blue_background"
            remetente_nome = sync_instance.atendimento_sync.atendimento.atendente_humano.nome
        else:  # Sistema ou Bot
            icon = {"emoji": "🤖"}
            color = "green_background"
            remetente_nome = "Sistema"

        header = f"{remetente_nome} ({remetente}) em {timestamp}:\n"

        block = {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": header},
                        "annotations": {"bold": True},
                    },
                    {
                        "type": "text",
                        "text": {"content": mensagem.conteudo},
                    },
                ],
                "icon": icon,
                "color": color,
            },
        }

        return block
