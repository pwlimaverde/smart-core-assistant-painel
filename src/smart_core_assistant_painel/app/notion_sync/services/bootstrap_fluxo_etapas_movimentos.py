"""Serviço de bootstrap para Etapas/Movimentos do Fluxo no Notion.

Cria databases mínimas para `Etapas do Fluxo` e `Movimentos do Fluxo`,
configura os relacionamentos essenciais e salva as configurações em
`NotionDatabaseConfig`. Mantém consistência com serviços já existentes
e evita importar scripts com efeitos colaterais no Django.

Comentários em Português e type hints completos conforme padrão.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from asgiref.sync import sync_to_async
from loguru import logger

from notion_py_client.notion_client import NotionAsyncClient

from smart_core_assistant_painel.app.notion_sync.models import (
    NotionDatabaseConfig,
)


class NotionFluxoEtapasMovimentosBootstrapService:
    """Bootstrap mínimo para Etapas e Movimentos do Fluxo.

    - Cria databases no Notion sem páginas de exemplo.
    - Configura relações com Fluxos (Etapas) e com Atendimentos/Etapas/
      Atendentes (Movimentos).
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

    async def _get_data_source_id(self, database_id: str) -> str | None:
        """Obtém o `data_source_id` de uma database existente no Notion.

        Args:
            database_id: ID da database no Notion.

        Returns:
            ID do data source ou None se não disponível.
        """
        try:
            info: Any = await self._client.request(
                method="get", path=f"databases/{database_id}"
            )
            ds = (info or {}).get("data_sources") or []
            ds_id: Optional[str] = (
                str(ds[0]["id"]) if ds and ds[0].get("id") else None
            )
            return ds_id
        except Exception as e:
            logger.warning(
                (
                    "Falha ao obter data_source_id para database {}: {}"
                ).format(database_id, e)
            )
            return None

    async def _create_etapas_database(self, fluxo_ds_id: str) -> Any:
        """Cria a database de Etapas com relação para Fluxos.

        Args:
            fluxo_ds_id: Data source ID da database de Fluxos.

        Returns:
            Objeto da database criada no Notion.
        """
        properties: dict[str, Any] = {
            "Nome": {"title": {}},
            "Descrição": {"rich_text": {}},
            "Ordem": {"number": {"format": "number"}},
            "Cor": {"select": {}},
            "Tipo de Etapa": {"select": {}},
            "Permite Atribuição": {"checkbox": {}},
            "Fluxo Relacionado": {
                # Define relação com Fluxos; `single_property` requerido
                # pelo Notion na criação via `initial_data_source`.
                "relation": {
                    "data_source_id": fluxo_ds_id,
                    "single_property": {},
                }
            },
            "Data Criação": {"date": {}},
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {
                    "type": "text",
                    "text": {"content": "🧱 Etapas do Fluxo CRM"},
                }
            ],
            "icon": {"type": "emoji", "emoji": "🧱"},
            "initial_data_source": {
                "name": "Etapas",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info(
            "Database Etapas criada: {}", getattr(created, "id", None)
        )
        return created

    async def _create_movimentos_database(
        self,
        atendimento_ds_id: str,
        etapa_ds_id: str,
        atendente_ds_id: str,
    ) -> Any:
        """Cria a database de Movimentos com relações necessárias.

        Args:
            atendimento_ds_id: Data source ID de Atendimentos.
            etapa_ds_id: Data source ID de Etapas.
            atendente_ds_id: Data source ID de Atendentes.

        Returns:
            Objeto da database criada no Notion.
        """
        properties: dict[str, Any] = {
            "Título": {"title": {}},
            "Motivo": {"rich_text": {}},
            "Dados Complementares": {"rich_text": {}},
            "Automático": {"checkbox": {}},
            "Data do Movimento": {"date": {}},
            "Duração (s)": {"number": {"format": "number"}},
            "Atendimento": {
                # `single_property` requerido na criação via initial_data_source
                "relation": {
                    "data_source_id": atendimento_ds_id,
                    "single_property": {},
                }
            },
            "Etapa Origem": {
                "relation": {
                    "data_source_id": etapa_ds_id,
                    "single_property": {},
                }
            },
            "Etapa Destino": {
                "relation": {
                    "data_source_id": etapa_ds_id,
                    "single_property": {},
                }
            },
            "Atendente Origem": {
                "relation": {
                    "data_source_id": atendente_ds_id,
                    "single_property": {},
                }
            },
            "Atendente Destino": {
                "relation": {
                    "data_source_id": atendente_ds_id,
                    "single_property": {},
                }
            },
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {
                    "type": "text",
                    "text": {"content": "🔀 Movimentos do Fluxo CRM"},
                }
            ],
            "icon": {"type": "emoji", "emoji": "🔀"},
            "initial_data_source": {
                "name": "Movimentos",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info(
            "Database Movimentos criada: {}", getattr(created, "id", None)
        )
        return created

    @sync_to_async
    def _save_etapas_config(self, etapa_db: Any) -> None:
        """Persiste configuração da database de Etapas em `NotionDatabaseConfig`.

        Args:
            etapa_db: Objeto database retornado pelo Notion.
        """
        etapa_ds = (
            etapa_db.data_sources[0]["id"]
            if getattr(etapa_db, "data_sources", None)
            else None
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_operacional_etapa_fluxo",
            defaults={
                "name": "🧱 Etapas do Fluxo CRM",
                "description": (
                    "Database para etapas do fluxo de atendimento"
                ),
                "notion_database_id": etapa_db.id,
                "data_source_id": etapa_ds,
                "django_model": "ui.operacional.EtapaFluxo",
                "django_app_label": "ui",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 7,
                "auto_sync": True,
            },
        )
        logger.info("Config de Etapas persistida em NotionDatabaseConfig")

    @sync_to_async
    def _save_movimentos_config(self, movimento_db: Any) -> None:
        """Persiste configuração da database de Movimentos em `NotionDatabaseConfig`.

        Args:
            movimento_db: Objeto database retornado pelo Notion.
        """
        mov_ds = (
            movimento_db.data_sources[0]["id"]
            if getattr(movimento_db, "data_sources", None)
            else None
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_operacional_movimento_fluxo",
            defaults={
                "name": "🔀 Movimentos do Fluxo CRM",
                "description": (
                    "Database para movimentos do fluxo de atendimento"
                ),
                "notion_database_id": movimento_db.id,
                "data_source_id": mov_ds,
                "django_model": "ui.operacional.MovimentoFluxo",
                "django_app_label": "ui",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 8,
                "auto_sync": True,
            },
        )
        logger.info("Config de Movimentos persistida em NotionDatabaseConfig")

    async def construct_minimal(self) -> None:
        """Orquestra a criação e configuração mínima (Etapas/Movimentos).

        Comentários:
        - Assume que Fluxos/Atendentes/Atendimentos já existem ou serão
          preparados pelo chamador antes desta construção.
        - Obtém `data_source_id` de bases existentes para montar relações.
        """
        # Obtém configs existentes para extrair IDs
        fluxo_cfg = await sync_to_async(
            NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_fluxo_atendimento"
            ).first
        )()
        atendente_cfg = await sync_to_async(
            NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_atendente"
            ).first
        )()
        atendimento_cfg = await sync_to_async(
            NotionDatabaseConfig.objects.filter(
                slug="ui_atendimentos_atendimento"
            ).first
        )()

        if not (fluxo_cfg and atendente_cfg and atendimento_cfg):
            raise ValueError(
                (
                    "Configs base ausentes: Fluxos/Atendentes/Atendimentos. "
                    "Garanta os bootstraps antes de construir Etapas/Movimentos."
                )
            )

        fluxo_ds_id = await self._get_data_source_id(
            str(fluxo_cfg.notion_database_id)
        )
        atendente_ds_id = await self._get_data_source_id(
            str(atendente_cfg.notion_database_id)
        )
        atendimento_ds_id = await self._get_data_source_id(
            str(atendimento_cfg.notion_database_id)
        )

        if not (fluxo_ds_id and atendente_ds_id and atendimento_ds_id):
            raise ValueError(
                (
                    "Data sources não encontrados para Fluxos/Atendentes/"
                    "Atendimentos"
                )
            )

        # Idempotência: se Etapas já existir, recuperar e atualizar config
        et_cfg = await sync_to_async(
            NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_etapa_fluxo"
            ).first
        )()
        if et_cfg and et_cfg.has_valid_database_id():
            etapa_db = await self._client.databases.retrieve(
                {"database_id": str(et_cfg.notion_database_id)}
            )
        else:
            etapa_db = await self._create_etapas_database(fluxo_ds_id)
        await self._save_etapas_config(etapa_db)

        # Cria Movimentos e salva configuração
        etapa_ds_id = await self._get_data_source_id(str(etapa_db.id))
        if not etapa_ds_id:
            raise ValueError("Data source de Etapas não encontrado")

        # Idempotência: se Movimentos já existir, recuperar e atualizar config
        mv_cfg = await sync_to_async(
            NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_movimento_fluxo"
            ).first
        )()
        if mv_cfg and mv_cfg.has_valid_database_id():
            movimento_db = await self._client.databases.retrieve(
                {"database_id": str(mv_cfg.notion_database_id)}
            )
        else:
            movimento_db = await self._create_movimentos_database(
                atendimento_ds_id, etapa_ds_id, atendente_ds_id
            )
        await self._save_movimentos_config(movimento_db)
        logger.info("Bootstrap de Etapas/Movimentos concluído com sucesso")