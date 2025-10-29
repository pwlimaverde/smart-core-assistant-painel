"""
Mapeador de dados para o modelo AtendimentoSync.

Este módulo contém a lógica para converter dados entre o modelo Django
`AtendimentoSync` e o formato esperado pelas propriedades de uma página
do Notion.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.notion_sync.models import AtendimentoSync
    from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento


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
            # Assunto como título principal
            "Assunto": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Novo", "color": "blue"},
                        {"name": "Em Andamento", "color": "yellow"},
                        {"name": "Aguardando Cliente", "color": "purple"},
                        {"name": "Resolvido", "color": "green"},
                        {"name": "Cancelado", "color": "red"},
                    ]
                }
            },
            "Prioridade": {
                "select": {
                    "options": [
                        {"name": "Baixa", "color": "gray"},
                        {"name": "Normal", "color": "blue"},
                        {"name": "Alta", "color": "orange"},
                        {"name": "Urgente", "color": "red"},
                    ]
                }
            },
            "Canal": {
                "select": {
                    "options": [
                        {"name": "WhatsApp", "color": "green"},
                        {"name": "Email", "color": "blue"},
                        {"name": "Telefone", "color": "purple"},
                        {"name": "Chat", "color": "gray"},
                    ]
                }
            },
            # Novo campo para contexto da conversa
            "Contexto Conversa": {"rich_text": {}},
            "Tags": {"multi_select": {"options": []}}, # Options podem ser adicionadas dinamicamente
            "Data de Abertura": {"date": {}},
            "Última Mensagem": {"date": {}},
            "Data de Fechamento": {"date": {}},
            "Contato": {"relation": {"database_id": ""}}, # ID será preenchido no setup
            "Atendente": {"relation": {"database_id": ""}}, # ID será preenchido no setup
            "Departamento": {"relation": {"database_id": ""}}, # ID será preenchido no setup
        }

    @staticmethod
    def to_notion_properties(sync_instance: "AtendimentoSync") -> dict:
        """
        Converte uma instância de AtendimentoSync para o formato de
        propriedades da API do Notion, alinhando os nomes às chaves
        definidas em field_mappings da NotionDatabaseConfig.
        """
        atendimento = sync_instance.atendimento

        # Carrega mapeamento dinâmico de nomes das propriedades
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
        ultima_msg_key = key(
            "data_ultima_mensagem", "Data Última Mensagem"
        )
        contato_key = key("contato", "Contato")
        departamento_key = key("departamento", "Departamento")
        atendente_key = key("atendente_humano", "Atendente")

        # Usa valores dos enums (em minúsculo), para casar com opções
        status_value = str(getattr(atendimento, "status", "")).lower()
        prioridade_value = str(getattr(atendimento, "prioridade", "")).lower()
        canal_value = str(getattr(atendimento, "canal", "")).lower()

        properties: dict = {}

        # Título: Assunto
        properties[assunto_key] = {
            "title": [
                {
                    "text": {
                        "content": atendimento.assunto or f"Atendimento #{atendimento.id}"
                    }
                }
            ]
        }

        # Selects (usar valores minúsculos)
        if status_value:
            properties[status_key] = {"select": {"name": status_value}}
        if prioridade_value:
            properties[prioridade_key] = {
                "select": {"name": prioridade_value}
            }
        if canal_value:
            properties[canal_key] = {"select": {"name": canal_value}}

        # Contexto Conversa (rich text) e Tags (multi-select)
        properties[contexto_key] = {
            "rich_text": [
                {"text": {"content": getattr(atendimento, "contexto_conversa", "")}}
            ]
        }
        properties[tags_key] = {
            "multi_select": [{"name": tag} for tag in getattr(atendimento, "tags", [])]
        }

        # Datas: usar nomes corretos do schema
        properties[data_inicio_key] = {
            "date": {"start": atendimento.data_inicio.isoformat()}
        }

        if getattr(atendimento, "data_ultima_mensagem", None):
            properties[ultima_msg_key] = {
                "date": {
                    "start": atendimento.data_ultima_mensagem.isoformat()
                }
            }

        if getattr(atendimento, "data_fim", None):
            properties[data_fim_key] = {
                "date": {"start": atendimento.data_fim.isoformat()}
            }

        # Relações: só incluir se houver external_id
        if (
            getattr(sync_instance, "contato_sync", None)
            and sync_instance.contato_sync.external_id
        ):
            properties[contato_key] = {
                "relation": [
                    {"id": sync_instance.contato_sync.external_id}
                ]
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
                "relation": [
                    {"id": sync_instance.atendente_sync.external_id}
                ]
            }

        return properties

    @staticmethod
    def from_notion_properties(properties: dict) -> dict:
        """
        Converte propriedades do Notion para um dicionário de dados do Django.
        """
        status_map = {
            v: k for k, v in dict(Atendimento.StatusAtendimento.choices).items()
        }
        prioridade_map = {
            v: k for k, v in dict(Atendimento.Prioridade.choices).items()
        }

        status_name = properties.get("Status", {}).get("select", {}).get("name")
        prioridade_name = properties.get("Prioridade", {}).get("select", {}).get("name")

        django_data = {
            "assunto": properties.get("Assunto", {}).get("rich_text", [{}])[0].get("text", {}).get("content", ""),
            "tags": [tag["name"] for tag in properties.get("Tags", {}).get("multi_select", [])],
        }

        if status_name and status_name in status_map:
            django_data["status"] = status_map[status_name]

        if prioridade_name and prioridade_name in prioridade_map:
            django_data["prioridade"] = prioridade_map[prioridade_name]

        return django_data
