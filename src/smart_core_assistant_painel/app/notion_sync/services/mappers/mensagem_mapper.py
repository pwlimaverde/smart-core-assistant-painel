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

        # Comentários: incluir dados de IA (intenção e entidades) se existirem
        intent_text = ""
        if mensagem.intent_detectado:
            try:
                partes = []
                for item in mensagem.intent_detectado:
                    tipo = str(item.get("type", "")).strip()
                    valor = str(item.get("value", "")).strip()
                    if tipo or valor:
                        partes.append(f"{tipo}: {valor}".strip(": "))
                if partes:
                    intent_text = "\nIntenção: " + "; ".join(partes)
            except Exception:
                intent_text = ""

        entidades_text = ""
        if mensagem.entidades_extraidas:
            try:
                partes_ent = []
                for ent in mensagem.entidades_extraidas:
                    etipo = str(ent.get("type", "")).strip()
                    evalor = str(ent.get("value", "")).strip()
                    if etipo or evalor:
                        partes_ent.append(f"{etipo}: {evalor}".strip(": "))
                if partes_ent:
                    entidades_text = "\nEntidades: " + "; ".join(partes_ent)
            except Exception:
                entidades_text = ""

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
                    *(
                        [
                            {
                                "type": "text",
                                "text": {"content": intent_text},
                                "annotations": {"italic": True},
                            }
                        ]
                        if intent_text
                        else []
                    ),
                    *(
                        [
                            {
                                "type": "text",
                                "text": {"content": entidades_text},
                                "annotations": {"italic": True},
                            }
                        ]
                        if entidades_text
                        else []
                    ),
                ],
                "icon": icon,
                "color": color,
            },
        }

        return block
