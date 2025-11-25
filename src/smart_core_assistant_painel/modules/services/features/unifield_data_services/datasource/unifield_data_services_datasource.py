"""Datasource para construir uma instância de UnifiedDataService.

Este módulo implementa uma fonte de dados que retorna uma instância
concreta de `UnifiedDataService`. Neste momento, a implementação é
in-memory e serve como adapter neutro, permitindo evolução futura para
provedores reais (ex.: NotionGuideV2) sem acoplamento direto.
"""

from typing import Any, Dict, Optional
from uuid import uuid4

from loguru import logger

from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)
from smart_core_assistant_painel.modules.services.utils.types import UDSData

from .clicup_adapter import ClicupUnifiedDataService
from .trello_adapter import TrelloUnifiedDataService

# Desabilitado temporariamente: adapter Notion.
# Comentado para evitar conflitos com o app `notion_sync` desativado.
# from .notion_adapter import NotionUnifiedDataService


class _InMemoryUnifiedDataService(UnifiedDataService):
    """Implementação in-memory de `UnifiedDataService`.

    Comentários em Português: esta implementação mantém dados em
    estruturas de dicionário, gerando IDs com `uuid4`. É útil para
    validação de fluxo, testes iniciais e como base para o adapter real.
    """

    def __init__(self, params: UnifieldDataServicesParameters) -> None:
        self._containers: Dict[str, Dict[str, Any]] = {}
        self._data_sources: Dict[str, Dict[str, Any]] = {}
        self._items: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._blocks: Dict[str, Dict[str, Any]] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._observability: bool = params.enable_observability
        self._default_data_source_id: str = params.data_source_id

    def _gen_id(self) -> str:
        return str(uuid4())

    def _log(self, message: str) -> None:
        if self._observability:
            logger.info(message)

    def create_container(self, name: str) -> str:
        container_id = self._gen_id()
        self._containers[container_id] = {
            "name": name,
            "data_sources": [],
            "blocks": [],
        }
        self._log(f"container criado: {name} -> {container_id}")
        return container_id

    def add_data_source(
        self,
        container_id: str,
        data_source_id: str,
        position: Optional[float] = None,
    ) -> str:
        link_id = self._gen_id()
        container = self._containers.get(container_id)
        if container is None:
            # Cria container implicito, caso não exista.
            container = {
                "name": "implicit",
                "data_sources": [],
                "blocks": [],
            }
            self._containers[container_id] = container
        container["data_sources"].append(
            {
                "data_source_id": data_source_id,
                "link_id": link_id,
                # Comentário: `position` armazenado somente para fins
                # de compatibilidade; não altera ordem real no in-memory.
                "position": position,
            }
        )
        self._data_sources.setdefault(
            data_source_id,
            {
                "container_id": container_id,
                "pos": position,
            },
        )
        self._log(
            "data source vinculada: "
            f"{data_source_id} em {container_id} (link {link_id})"
        )
        return link_id

    def update_schema(
        self, data_source_id: str, schema: Dict[str, Any]
    ) -> str:
        version_id = self._gen_id()
        self._schemas[data_source_id] = {
            "schema": schema,
            "version_id": version_id,
            "relations": self._schemas.get(data_source_id, {}).get(
                "relations", []
            ),
        }
        self._log(
            f"schema atualizado para {data_source_id} (versao {version_id})"
        )
        return version_id

    def create_item(self, data_source_id: str, payload: Dict[str, Any]) -> str:
        ds_id = data_source_id or self._default_data_source_id
        item_id = self._gen_id()
        self._items.setdefault(ds_id, {})
        self._items[ds_id][item_id] = payload
        self._log(f"item criado: {ds_id} -> {item_id}")
        return item_id

    def update_item(
        self, data_source_id: str, item_id: str, payload: Dict[str, Any]
    ) -> str:
        ds_id = data_source_id or self._default_data_source_id
        items = self._items.setdefault(ds_id, {})
        # Atualiza ou cria caso não exista, para simplicidade.
        items[item_id] = payload
        version_id = self._gen_id()
        self._log(
            f"item atualizado: {ds_id} -> {item_id} (versao {version_id})"
        )
        return version_id

    def add_relation_property(
        self, data_source_id: str, property_name: str, target_id: str
    ) -> str:
        ds_id = data_source_id or self._default_data_source_id
        property_id = self._gen_id()
        schema = self._schemas.setdefault(
            ds_id,
            {
                "schema": {},
                "version_id": self._gen_id(),
                "relations": [],
            },
        )
        schema["relations"].append(
            {
                "id": property_id,
                "name": property_name,
                "target": target_id,
            }
        )
        self._log(
            "propriedade de relação criada: "
            f"{property_name} em {ds_id} -> {property_id}"
        )
        return property_id

    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        return self._containers.get(container_id)

    def get_data_source(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        return self._data_sources.get(data_source_id)

    def get_item(
        self, data_source_id: str, item_id: str
    ) -> Optional[Dict[str, Any]]:
        ds_id = data_source_id or self._default_data_source_id
        return self._items.get(ds_id, {}).get(item_id)

    def append_block(self, container_id: str, block: Dict[str, Any]) -> str:
        block_id = self._gen_id()
        self._blocks[block_id] = block
        container = self._containers.get(container_id)
        if container is not None:
            container["blocks"].append({"id": block_id, "block": block})
        self._log(f"bloco anexado: {container_id} -> {block_id}")
        return block_id


class UnifieldDataServicesDatasource(UDSData):
    """Datasource que fornece uma instância de `UnifiedDataService`.

    Neste estágio, retorna a implementação in-memory para testes e
    estrutura base. Futuramente, esta classe selecionará o adapter
    conforme `parameters.provider` (ex.: "notion").
    """

    def __call__(
        self, parameters: UnifieldDataServicesParameters
    ) -> UnifiedDataService:
        provider = (parameters.provider or "").lower()
        if provider == "trello":
            service = TrelloUnifiedDataService(params=parameters)
            if parameters.enable_observability:
                logger.info(
                    "UnifiedDataService Trello inicializado para "
                    f"provider={parameters.provider}"
                )
            return service
        if provider in {"clickup", "clicup"}:
            service = ClicupUnifiedDataService(params=parameters)
            if parameters.enable_observability:
                logger.info(
                    "UnifiedDataService ClickUp inicializado para "
                    f"provider={parameters.provider}"
                )
            return service
        # Desabilitado temporariamente: branch Notion.
        # Comentado para evitar import/uso do adapter enquanto o app
        # `notion_sync` está fora de `INSTALLED_APPS`.
        # elif provider == "notion":
        #     service = NotionUnifiedDataService(params=parameters)
        #     if parameters.enable_observability:
        #         logger.info(
        #             "UnifiedDataService Notion inicializado para "
        #             f"provider={parameters.provider}"
        #         )
        #     return service

        # Fallback para in-memory quando provider desconhecido
        service = _InMemoryUnifiedDataService(params=parameters)
        if parameters.enable_observability:
            logger.info(
                "UnifiedDataService in-memory inicializado "
                f"para provider={parameters.provider}"
            )
        return service
