"""Serviço de bootstrap para Departamentos/Atendentes no Notion.

Cria databases mínimas, configura a relação bidirecional e salva as
configurações em `NotionDatabaseConfig`. Evita importar scripts com
efeitos colaterais no Django.

Comentários em Português e type hints completos conforme padrão.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

from asgiref.sync import sync_to_async
from loguru import logger

from notion_py_client.notion_client import NotionAsyncClient

from smart_core_assistant_painel.app.notion_sync.models import (
    NotionDatabaseConfig,
)


class NotionOperacionalBootstrapService:
    """Bootstrap mínimo para Departamentos e Atendentes.

    - Cria databases no Notion sem páginas de exemplo.
    - Mantém relação bidirecional entre Departamentos e Atendentes.
    - Persiste `NotionDatabaseConfig` com slugs operacionais.
    """

    def __init__(self) -> None:
        self._token: Optional[str] = os.getenv("NOTION_TOKEN")
        self._root_page_id: Optional[str] = os.getenv("NOTION_PAGE_ID")
        if not self._token or not self._root_page_id:
            raise ValueError(
                "NOTION_TOKEN e NOTION_PAGE_ID devem estar definidos no .env"
            )
        self._client = NotionAsyncClient(auth=self._token)

    async def _create_departamento_database(self) -> Any:
        """Cria a database de Departamentos (sem páginas de exemplo)."""
        properties: dict[str, Any] = {
            "Nome": {"title": {}},
            "Descrição": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Data Criação": {"date": {}},
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {"type": "text", "text": {"content": "🏛️ Departamentos CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "🏛️"},
            "initial_data_source": {
                "name": "Departamentos",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info(
            "Database Departamentos criada: {}",
            getattr(created, "id", None),
        )
        return created

    async def _create_atendente_database(self, departamento_db: Any) -> Any:
        """Cria a database de Atendentes com relação para Departamentos."""
        if not getattr(departamento_db, "data_sources", None):
            raise ValueError("Database de departamentos sem data_source")

        dep_ds_id: str = departamento_db.data_sources[0]["id"]

        properties: dict[str, Any] = {
            "Nome": {"title": {}},
            "Email": {"email": {}},
            "Telefone": {"phone_number": {}},
            "Cargo": {"rich_text": {}},
            "Ativo": {"checkbox": {}},
            "Disponível": {"checkbox": {}},
            "Capacidade Máxima": {"number": {"format": "number"}},
            "Horário Trabalho": {"rich_text": {}},
            "Departamentos Relacionados": {
                "relation": {
                    "data_source_id": dep_ds_id,
                    "single_property": {},
                    "dual_property": {
                        "synced_property_name": "Atendentes Relacionados",
                    },
                }
            },
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {"type": "text", "text": {"content": "👨‍💼 Atendentes CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "👨‍💼"},
            "initial_data_source": {
                "name": "Atendentes",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info(
            "Database Atendentes criada: {}",
            getattr(created, "id", None),
        )
        return created

    async def _add_relation_to_departamento(
        self, atendente_db: Any, departamento_db: Any
    ) -> None:
        """Garante a propriedade inversa em Departamentos."""
        if not getattr(atendente_db, "data_sources", None):
            raise ValueError("Atendentes sem data_source")
        if not getattr(departamento_db, "data_sources", None):
            raise ValueError("Departamentos sem data_source")

        atendente_ds_id: str = atendente_db.data_sources[0]["id"]
        departamento_ds_id: str = departamento_db.data_sources[0]["id"]

        # Busca ID da propriedade "Departamentos Relacionados" em Atendentes
        info: Any = await self._client.request(
            method="get", path=f"databases/{atendente_db.id}"
        )

        def _prop_id(obj: Any, name: str) -> str | None:
            """Obtém ID de propriedade por nome de forma segura."""
            try:
                props = obj.get("properties", {})
                pid = props.get(name, {}).get("id")
                return str(pid) if pid else None
            except Exception:
                return None

        dep_rel_prop_id: Optional[str] = _prop_id(
            info, "Departamentos Relacionados"
        )

        update: dict[str, Any] = {
            "properties": {
                "Atendentes Relacionados": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": atendente_ds_id,
                        "single_property": {},
                        "dual_property": (
                            {"synced_property_id": dep_rel_prop_id}
                            if dep_rel_prop_id
                            else {
                                "synced_property_name": "Departamentos Relacionados",
                            }
                        ),
                    },
                }
            }
        }

        await self._client.request(
            method="patch",
            path=f"data_sources/{departamento_ds_id}",
            body=update,
        )
        logger.info("Relação inversa garantida em Departamentos")

    @sync_to_async
    def _save_configs(self, atendente_db: Any, departamento_db: Any) -> None:
        """Persiste configurações em `NotionDatabaseConfig`."""
        atendente_ds = (
            atendente_db.data_sources[0]["id"]
            if getattr(atendente_db, "data_sources", None)
            else None
        )
        departamento_ds = (
            departamento_db.data_sources[0]["id"]
            if getattr(departamento_db, "data_sources", None)
            else None
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_operacional_departamento",
            defaults={
                "name": "🏛️ Departamentos CRM",
                "description": (
                    "Database para sincronização de departamentos do sistema"
                ),
                "notion_database_id": departamento_db.id,
                "data_source_id": departamento_ds,
                "django_model": "ui.operacional.Departamento",
                "django_app_label": "ui",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 7,
                "auto_sync": True,
            },
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_operacional_atendente",
            defaults={
                "name": "👨‍💼 Atendentes CRM",
                "description": (
                    "Database para sincronização de atendentes do sistema"
                ),
                "notion_database_id": atendente_db.id,
                "data_source_id": atendente_ds,
                "django_model": "ui.operacional.Atendente",
                "django_app_label": "ui",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 8,
                "auto_sync": True,
            },
        )
        logger.info("Configs operacionais persistidas em NotionDatabaseConfig")

    async def construct_minimal(self) -> None:
        """Orquestra a criação e configuração mínima operacional."""
        dep_db = await self._create_departamento_database()
        at_db = await self._create_atendente_database(dep_db)
        await asyncio.sleep(1)
        await self._add_relation_to_departamento(at_db, dep_db)
        await self._save_configs(at_db, dep_db)
        logger.info("Bootstrap operacional concluído com sucesso")