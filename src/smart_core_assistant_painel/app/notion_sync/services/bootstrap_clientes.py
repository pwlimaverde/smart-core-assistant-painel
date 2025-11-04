"""Serviço de bootstrap para databases de Clientes/Contatos no Notion.

Cria databases vazias (sem páginas de exemplo) e registra as
configurações em `NotionDatabaseConfig`. Mantém o relacionamento
bidirecional entre as duas databases.

Comentários em Português e type hints completos conforme padrão.
"""

from __future__ import annotations

import os
from typing import Any

from asgiref.sync import sync_to_async
from loguru import logger

from notion_py_client.notion_client import NotionAsyncClient

from smart_core_assistant_painel.app.notion_sync.models import (
    NotionDatabaseConfig,
)


class NotionClientesBootstrapService:
    """Bootstrap mínimo para databases de Clientes/Contatos.

    - Cria databases vazias no Notion.
    - Configura relação bidirecional entre elas.
    - Salva `NotionDatabaseConfig` com labels corretos (app `clientes`).
    """

    def __init__(self) -> None:
        self._token: str | None = os.getenv("NOTION_TOKEN")
        self._root_page_id: str | None = os.getenv("NOTION_PAGE_ID")
        if not self._token or not self._root_page_id:
            raise ValueError(
                "NOTION_TOKEN e NOTION_PAGE_ID devem estar definidos no .env"
            )
        self._client = NotionAsyncClient(auth=self._token)

    async def _create_cliente_database(self) -> Any:
        """Cria a database de Clientes (sem páginas de exemplo)."""
        properties: dict[str, Any] = {
            "Nome Fantasia": {"title": {}},
            "Razão Social": {"rich_text": {}},
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "fisica", "color": "blue"},
                        {"name": "juridica", "color": "green"},
                    ]
                }
            },
            "CNPJ": {"rich_text": {}},
            "CPF": {"rich_text": {}},
            "Telefone": {"phone_number": {}},
            "Site": {"url": {}},
            "Ramo Atividade": {"rich_text": {}},
            "Observações": {"rich_text": {}},
            "CEP": {"rich_text": {}},
            "Logradouro": {"rich_text": {}},
            "Número": {"rich_text": {}},
            "Bairro": {"rich_text": {}},
            "Cidade": {"rich_text": {}},
            "UF": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {"type": "text", "text": {"content": "🏢 Clientes CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "🏢"},
            "initial_data_source": {
                "name": "Clientes",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info("Database Clientes criada: {}", getattr(created, "id", None))
        return created

    async def _create_contato_database(self, cliente_db: Any) -> Any:
        """Cria a database de Contatos com relação a Clientes."""
        ds_id: str | None = None
        if getattr(cliente_db, "data_sources", None):
            ds_id = cliente_db.data_sources[0]["id"]
        if not ds_id:
            raise ValueError(
                "Database de Clientes não possui data_source inicial"
            )

        properties: dict[str, Any] = {
            "Nome Contato": {"title": {}},
            "Telefone": {"phone_number": {}},
            "Email": {"email": {}},
            "Nome Perfil WhatsApp": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Data Cadastro": {"date": {}},
            "Última Interação": {"date": {}},
            "Clientes Relacionados": {
                "relation": {"data_source_id": ds_id, "single_property": {}}
            },
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {"type": "text", "text": {"content": "👥 Contatos CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "👥"},
            "initial_data_source": {
                "name": "Contatos",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info("Database Contatos criada: {}", getattr(created, "id", None))
        return created

    async def _add_relation_to_clientes(self, contato_db: Any, cliente_db: Any) -> None:
        """Adiciona propriedade espelhada em Clientes (bidirecional)."""
        contato_ds: str | None = None
        if getattr(contato_db, "data_sources", None):
            contato_ds = contato_db.data_sources[0]["id"]
        if not contato_ds:
            raise ValueError("Database de Contatos não possui data_source")

        # A API async `databases.update` aceita um único parâmetro contendo
        # `database_id` e `properties`. A chamada anterior com dois parâmetros
        # causava o erro: "_DatabasesAPI.update() takes 2 positional arguments
        # but 3 were given". Ajustamos para o formato correto.
        params: dict[str, Any] = {
            "database_id": cliente_db.id,
            "properties": {
                "Contatos Relacionados": {
                    "relation": {
                        "data_source_id": contato_ds,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Clientes Relacionados",
                        },
                    }
                }
            },
        }
        await self._client.databases.update(params)
        logger.info("Relação bidirecional adicionada em Clientes.")

    @sync_to_async
    def _save_configs(self, contato_db: Any, cliente_db: Any) -> None:
        """Persiste configurações em `NotionDatabaseConfig`."""
        contato_ds = (
            contato_db.data_sources[0]["id"]
            if getattr(contato_db, "data_sources", None)
            else None
        )
        cliente_ds = (
            cliente_db.data_sources[0]["id"]
            if getattr(cliente_db, "data_sources", None)
            else None
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_clientes_cliente",
            defaults={
                "name": "🏢 Clientes CRM",
                "description": (
                    "Database para sincronização de clientes do sistema"
                ),
                "notion_database_id": cliente_db.id,
                "data_source_id": cliente_ds,
                "django_model": "clientes.Cliente",
                "django_app_label": "clientes",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 9,
                "auto_sync": True,
            },
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_clientes_contato",
            defaults={
                "name": "👥 Contatos CRM",
                "description": (
                    "Database para sincronização de contatos do sistema"
                ),
                "notion_database_id": contato_db.id,
                "data_source_id": contato_ds,
                "django_model": "clientes.Contato",
                "django_app_label": "clientes",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 10,
                "auto_sync": True,
            },
        )
        logger.info("Configurações persistidas em NotionDatabaseConfig.")

    async def construct_minimal(self) -> None:
        """Cria databases e relação, e salva configs (sem exemplos)."""
        cliente_db = await self._create_cliente_database()
        contato_db = await self._create_contato_database(cliente_db)
        await self._add_relation_to_clientes(contato_db, cliente_db)
        await self._save_configs(contato_db, cliente_db)
        logger.info("Bootstrap mínimo concluído.")