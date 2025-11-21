import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.notion_sync.models import (
        AtendimentoSync,
    )
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Atendimento,
    )


class AtendimentoMapper:
    """
    Classe responsável por mapear e transformar dados do Atendimento.
    """

    @staticmethod
    def get_notion_schema() -> dict:
        """
        Retorna o schema da database de Atendimentos para o Notion.
        """
        return {
            "Assunto": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "fila", "color": "gray"},
                        {"name": "em_atendimento", "color": "blue"},
                        {"name": "pendencia", "color": "yellow"},
                        {"name": "resolvido", "color": "green"},
                        {"name": "cancelado", "color": "red"},
                    ]
                }
            },
            "Prioridade": {
                "select": {
                    "options": [
                        {"name": "baixa", "color": "gray"},
                        {"name": "normal", "color": "blue"},
                        {"name": "alta", "color": "orange"},
                        {"name": "urgente", "color": "red"},
                    ]
                }
            },
            "Canal": {
                "select": {
                    "options": [
                        {"name": "whatsapp", "color": "green"},
                        {"name": "email", "color": "blue"},
                        {"name": "telefone", "color": "purple"},
                        {"name": "web", "color": "gray"},
                    ]
                }
            },
            "Contexto Conversa": {"rich_text": {}},
            "Tags": {"multi_select": {"options": []}},
            "Data Início": {"date": {}},
            "Data Última Mensagem": {"date": {}},
            "Data Fim": {"date": {}},
            "Avaliação": {"number": {"format": "number"}},
            "Feedback": {"rich_text": {}},
            "Contato": {"relation": {"database_id": ""}},
            "Atendente": {"relation": {"database_id": ""}},
            "Departamento": {"relation": {"database_id": ""}},
            "Mensagens Relacionadas": {"relation": {}},
        }

    @staticmethod
    def to_notion_properties(sync_instance: "AtendimentoSync") -> dict:
        """
        Converte uma instância de AtendimentoSync para o formato de
        propriedades da API do Notion.
        """
        atendimento = sync_instance.atendimento

        config = getattr(sync_instance, "config", None)
        field_mappings: dict = {}
        if config and getattr(config, "field_mappings", None):
            field_mappings = config.field_mappings or {}

        def key(django_field: str, default: str) -> str:
            return field_mappings.get(django_field, default)

        status_key = key("status", "Status")
        prioridade_key = key("prioridade", "Prioridade")
        canal_key = key("canal", "Canal")
        assunto_key = key("assunto", "Assunto")
        contexto_key = key("contexto_conversa", "Contexto Conversa")
        tags_key = key("tags", "Tags")
        data_inicio_key = key("data_inicio", "Data Início")
        data_fim_key = key("data_fim", "Data Fim")
        ultima_msg_key = key("data_ultima_mensagem", "Data Última Mensagem")
        contato_key = key("contato", "Contato")
        departamento_key = key("departamento", "Departamento")
        atendente_key = key("atendente_humano", "Atendente")
        mensagens_key = key("mensagens_relacionadas", "Mensagens Relacionadas")

        status_value = str(getattr(atendimento, "status", "")).lower()
        prioridade_value = str(getattr(atendimento, "prioridade", "")).lower()
        canal_value = str(getattr(atendimento, "canal", "")).lower()

        properties: dict = {}

        properties[assunto_key] = {
            "title": [
                {
                    "text": {
                        "content": atendimento.assunto
                        or f"Atendimento #{atendimento.id}"
                    }
                }
            ]
        }

        if status_value:
            properties[status_key] = {"select": {"name": status_value}}
        if prioridade_value:
            properties[prioridade_key] = {"select": {"name": prioridade_value}}
        if canal_value:
            properties[canal_key] = {"select": {"name": canal_value}}

        def _fmt_json(val: object) -> str:
            try:
                import json

                if isinstance(val, (dict, list)):
                    txt = json.dumps(val, ensure_ascii=False, indent=2)
                else:
                    txt = str(val)
            except Exception:
                txt = str(val)
            return txt[:2000]

        def _formatar_contexto_conversa(contexto: dict) -> str:
            """Formata o contexto da conversa de forma legível para o Notion."""
            if not contexto:
                return "Sem contexto disponível"

            linhas: list[str] = ["📋 CONTEXTO DA CONVERSA\n"]

            # Ordena as chaves para melhor organização
            chaves_ordenadas = sorted(contexto.keys())

            for chave in chaves_ordenadas:
                valor = contexto[chave]

                # Formatação especial para diferentes tipos de dados
                if chave == "canal":
                    linhas.append(f"📱 Canal: {str(valor).upper()}")
                elif chave == "primeira_interacao" and valor:
                    linhas.append("🆕 Primeira interação: Sim")
                elif chave == "sessao_iniciada":
                    linhas.append(f"⏰ Sessão iniciada: {str(valor)}")
                elif isinstance(valor, bool):
                    linhas.append(
                        f"✅ {chave.replace('_', ' ').title()}: {'Sim' if valor else 'Não'}"
                    )
                elif isinstance(valor, str):
                    # Para strings simples, exibe como valor normal
                    if chave == "cliente_status":
                        linhas.append(f"👤 Cliente Status: {valor}")
                    else:
                        linhas.append(
                            f"• {chave.replace('_', ' ').title()}: {valor}"
                        )
                elif isinstance(valor, list):
                    if valor:
                        linhas.append(f"📝 {chave.replace('_', ' ').title()}:")
                        for item in valor:
                            linhas.append(f"   • {str(item)}")
                    else:
                        linhas.append(
                            f"📝 {chave.replace('_', ' ').title()}: (vazio)"
                        )
                elif isinstance(valor, dict):
                    if valor:
                        linhas.append(f"📊 {chave.replace('_', ' ').title()}:")
                        for sub_chave, sub_valor in valor.items():
                            linhas.append(
                                f"   • {sub_chave}: {str(sub_valor)}"
                            )
                    else:
                        linhas.append(
                            f"📊 {chave.replace('_', ' ').title()}: (vazio)"
                        )
                else:
                    linhas.append(
                        f"• {chave.replace('_', ' ').title()}: {str(valor)}"
                    )

            # Adiciona informações adicionais úteis
            if "mensagens_trocadas" in contexto and isinstance(
                contexto["mensagens_trocadas"], int
            ):
                linhas.append(
                    f"\n💬 Total de mensagens trocadas: {contexto['mensagens_trocadas']}"
                )

            return "\n".join(linhas)

        properties[contexto_key] = {
            "rich_text": [
                {
                    "text": {
                        "content": _formatar_contexto_conversa(
                            getattr(atendimento, "contexto_conversa", {})
                        )
                    }
                }
            ]
        }

        tags_list = getattr(atendimento, "tags", [])
        formatted_tags = []

        for tag in tags_list:
            if isinstance(tag, str):
                formatted_tags.append({"name": tag})
            elif isinstance(tag, dict):
                tag_str = str(
                    tag.get("status", "") or tag.get("nome", "") or tag
                )
                if tag_str:
                    formatted_tags.append({"name": tag_str})
                else:
                    formatted_tags.append(
                        {"name": json.dumps(tag, ensure_ascii=False)[:100]}
                    )
            else:
                formatted_tags.append({"name": str(tag)})

        properties[tags_key] = {"multi_select": formatted_tags}

        properties[data_inicio_key] = {
            "date": {"start": atendimento.data_inicio.isoformat()}
        }

        if getattr(atendimento, "data_ultima_mensagem", None):
            properties[ultima_msg_key] = {
                "date": {"start": atendimento.data_ultima_mensagem.isoformat()}
            }

        if getattr(atendimento, "data_fim", None):
            properties[data_fim_key] = {
                "date": {"start": atendimento.data_fim.isoformat()}
            }

        avaliacao_key = key("avaliacao", "Avaliação")
        feedback_key = key("feedback", "Feedback")

        if getattr(atendimento, "avaliacao", None) is not None:
            try:
                properties[avaliacao_key] = {
                    "number": float(atendimento.avaliacao)
                }
            except Exception:
                pass

        fb_val = getattr(atendimento, "feedback", None)
        if fb_val:
            fb_txt = str(fb_val)[:2000]
            properties[feedback_key] = {
                "rich_text": [{"text": {"content": fb_txt}}]
            }

        if (
            getattr(sync_instance, "contato_sync", None)
            and sync_instance.contato_sync.external_id
        ):
            properties[contato_key] = {
                "relation": [{"id": sync_instance.contato_sync.external_id}]
            }

        if (
            getattr(sync_instance, "departamento_sync", None)
            and sync_instance.departamento_sync.external_id
        ):
            properties[departamento_key] = {
                "relation": [
                    {"id": sync_instance.departamento_sync.external_id}
                ]
            }

        if (
            getattr(sync_instance, "atendente_sync", None)
            and sync_instance.atendente_sync.external_id
        ):
            properties[atendente_key] = {
                "relation": [{"id": sync_instance.atendente_sync.external_id}]
            }

        # Adicionar mensagens relacionadas
        mensagens_relacionadas = []
        if hasattr(sync_instance, "mensagens_sync"):
            try:
                from loguru import logger

                logger.info(
                    f"[MSG_DEBUG] Processando mensagens relacionadas para atendimento #{sync_instance.atendimento.id}"
                )

                for msg_sync in sync_instance.mensagens_sync.all():
                    if msg_sync.external_id:
                        mensagens_relacionadas.append(
                            {"id": msg_sync.external_id}
                        )
                        logger.info(
                            f"[MSG_DEBUG] Mensagem #{msg_sync.mensagem.id} com external_id {msg_sync.external_id} adicionada"
                        )
                    else:
                        logger.warning(
                            f"[MSG_DEBUG] Mensagem #{msg_sync.mensagem.id} sem external_id"
                        )

                logger.info(
                    f"[MSG_DEBUG] Total de mensagens relacionadas: {len(mensagens_relacionadas)}"
                )

                if mensagens_relacionadas:
                    properties[mensagens_key] = {
                        "relation": mensagens_relacionadas
                    }
                    logger.info(
                        f"[MSG_DEBUG] Campo '{mensagens_key}' adicionado com {len(mensagens_relacionadas)} mensagens"
                    )
                else:
                    logger.info(
                        f"[MSG_DEBUG] Nenhuma mensagem relacionada para adicionar"
                    )

            except Exception as e:
                logger.error(
                    f"[MSG_DEBUG] Erro ao processar mensagens relacionadas: {e}",
                    exc_info=True,
                )

        return properties

    @staticmethod
    def from_notion_properties(properties: dict) -> dict:
        return {}
