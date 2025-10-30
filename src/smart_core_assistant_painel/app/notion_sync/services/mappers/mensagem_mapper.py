"""
Mapeador de dados para o modelo MensagemSync.

Este módulo converte uma instância de mensagem em estruturas compatíveis
com a API do Notion.

Observação: há suporte para dois formatos distintos:
1) Bloco (callout) – usado quando mensagens eram anexadas como filhos
   dentro da página do atendimento.
2) Propriedades de página – usado para criação na database "Mensagens CRM"
   com relacionamento para o atendimento.
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

    @staticmethod
    def to_notion_properties(sync_instance: "MensagemSync") -> dict:
        """
        Converte uma instância de MensagemSync para propriedades de página
        de uma database do Notion.

        Comentário:
        - A propriedade "Conteúdo" é do tipo title.
        - A relação "Atendimento Relacionado" liga a mensagem ao atendimento.
        - Campos de IA são enviados como rich_text por simplicidade.

        Args:
            sync_instance: Instância do modelo de sincronização da mensagem.

        Returns:
            Dicionário de propriedades para criação/atualização de página.
        """
        mensagem = sync_instance.mensagem

        # Conteúdo como title (limite de 2000 chars por segurança)
        conteudo: str = mensagem.conteudo or ""
        title = conteudo[:2000] if conteudo else "(Mensagem sem texto)"

        props: dict = {
            "Conteúdo": {
                "title": [{"text": {"content": title}}]
            }
        }

        # Relação com atendimento (se página pai já sincronizada)
        try:
            parent_id = (
                str(sync_instance.atendimento_sync.external_id)
                if sync_instance.atendimento_sync
                and sync_instance.atendimento_sync.external_id
                else None
            )
        except Exception:
            parent_id = None

        if parent_id:
            props["Atendimento Relacionado"] = {
                "relation": [{"id": parent_id}]
            }

        # Tipo da mensagem (select).
        # Comentário: converte códigos do WhatsApp (modelo Django)
        # para opções amigáveis definidas no Notion.
        if getattr(mensagem, "tipo", None):
            tipo_map: dict[str, str] = {
                "extendedTextMessage": "Texto",
                "imageMessage": "Imagem",
                "videoMessage": "Vídeo",
                "audioMessage": "Áudio",
                "documentMessage": "Documento",
            }
            tipo_notion: str = tipo_map.get(
                str(mensagem.tipo),
                "Texto",
            )
            props["Tipo"] = {"select": {"name": tipo_notion}}

        # Remetente (select)
        # Comentário: usa nomes exatamente como definidos no schema do Notion
        # para evitar duplicação de opções.
        if getattr(mensagem, "remetente", None):
            rem_val: str = str(mensagem.remetente)
            allowed_rem: set[str] = {
                "contato",
                "bot",
                "atendente_humano",
            }
            nome_rem: str = rem_val if rem_val in allowed_rem else "bot"
            props["Remetente"] = {"select": {"name": nome_rem}}

        # Timestamp
        if getattr(mensagem, "timestamp", None):
            props["Timestamp"] = {
                "date": {"start": mensagem.timestamp.isoformat()}
            }

        # IDs e metadados auxiliares
        if getattr(mensagem, "message_id_whatsapp", None):
            props["Message ID WhatsApp"] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": str(mensagem.message_id_whatsapp)
                        },
                    }
                ]
            }

        # Campos de IA (opcionais)
        try:
            if getattr(mensagem, "intent_detectado", None):
                intent_parts: list[str] = []
                for item in mensagem.intent_detectado:
                    tipo = str(item.get("type", "")).strip()
                    valor = str(item.get("value", "")).strip()
                    if tipo or valor:
                        intent_parts.append(f"{tipo}: {valor}".strip(": "))
                if intent_parts:
                    props["Intenção Detectada"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "; ".join(intent_parts)
                                },
                            }
                        ]
                    }
        except Exception:
            # Silencia falhas de parsing
            pass

        try:
            if getattr(mensagem, "entidades_extraidas", None):
                ent_parts: list[str] = []
                for ent in mensagem.entidades_extraidas:
                    etipo = str(ent.get("type", "")).strip()
                    evalor = str(ent.get("value", "")).strip()
                    if etipo or evalor:
                        ent_parts.append(f"{etipo}: {evalor}".strip(": "))
                if ent_parts:
                    props["Entidades Extraídas"] = {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "; ".join(ent_parts)
                                },
                            }
                        ]
                    }
        except Exception:
            pass

        # Metadados – serializa JSON como texto simples
        try:
            if getattr(mensagem, "metadados", None):
                meta_str = str(mensagem.metadados)[:2000]
                props["Metadados"] = {
                    "rich_text": [
                        {"type": "text", "text": {"content": meta_str}}
                    ]
                }
        except Exception:
            pass

        # Confiança Resposta – se existir um score
        try:
            confianca = None
            if hasattr(mensagem, "ia_confianca_resposta"):
                confianca = getattr(mensagem, "ia_confianca_resposta")
            if confianca is not None:
                props["Confiança Resposta"] = {"number": float(confianca)}
        except Exception:
            pass

        return props
