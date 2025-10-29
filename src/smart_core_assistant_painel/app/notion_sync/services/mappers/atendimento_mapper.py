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
            "Protocolo": {"title": {}},
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
            "Assunto": {"rich_text": {}},
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
        Converte uma instância de AtendimentoSync para o formato de propriedades
        da API do Notion.
        """
        atendimento = sync_instance.atendimento

        properties = {
            "Protocolo": {
                "title": [{"text": {"content": atendimento.protocolo or f"Atendimento #{atendimento.id}"}}]
            },
            "Status": {
                "select": {"name": atendimento.get_status_display()}
            },
            "Prioridade": {
                "select": {"name": atendimento.get_prioridade_display()}
            },
            "Canal": {
                "select": {"name": atendimento.get_canal_display()}
            },
            "Assunto": {
                "rich_text": [{"text": {"content": atendimento.assunto or ""}}]
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in atendimento.tags]
            },
            "Data de Abertura": {
                "date": {"start": atendimento.data_inicio.isoformat()}
            },
            "Última Mensagem": {
                "date": {"start": atendimento.data_ultima_mensagem.isoformat()}
                if atendimento.data_ultima_mensagem
                else None
            },
        }

        if atendimento.data_fim:
            properties["Data de Fechamento"] = {
                "date": {"start": atendimento.data_fim.isoformat()}
            }

        if sync_instance.contato_sync and sync_instance.contato_sync.external_id:
            properties["Contato"] = {
                "relation": [{"id": sync_instance.contato_sync.external_id}]
            }

        if sync_instance.departamento_sync and sync_instance.departamento_sync.external_id:
            properties["Departamento"] = {
                "relation": [{"id": sync_instance.departamento_sync.external_id}]
            }

        if sync_instance.atendente_sync and sync_instance.atendente_sync.external_id:
            properties["Atendente"] = {
                "relation": [{"id": sync_instance.atendente_sync.external_id}]
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
