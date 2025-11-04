"""Adapter do Notion para UnifiedDataService.

Este módulo implementa um adapter que conecta o UnifiedDataService
com a API do Notion, permitindo operações de criação e manipulação
de databases, páginas e propriedades no Notion através da interface
unificada.
"""

import asyncio
import os
from typing import Any, Dict, Optional
from uuid import uuid4

from decouple import config
from loguru import logger
from notion_py_client.notion_client import NotionAsyncClient, APIResponseError

from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)
# Importação de modelos Django será realizada de forma lazy
# dentro dos métodos para evitar erros quando o Django ainda
# não está configurado (INSTALLED_APPS indisponível).


class NotionUnifiedDataService(UnifiedDataService):
    """Implementação do UnifiedDataService para Notion.
    
    Esta classe adapta as operações do UnifiedDataService para a API do Notion,
    gerenciando databases, páginas e propriedades através da interface unificada.
    """

    def __init__(self, params: UnifieldDataServicesParameters) -> None:
        """Inicializa o adapter do Notion.
        
        Args:
            params: Parâmetros de configuração do serviço.
        """
        self._params = params
        self._observability = params.enable_observability
        self._default_data_source_id = params.data_source_id
        
        # Inicializa cliente do Notion
        notion_token = config("NOTION_TOKEN", default="")
        if not notion_token:
            raise ValueError("NOTION_TOKEN não configurado")
            
        # Política de event loop para Windows
        try:
            if os.name == "nt":
                asyncio.set_event_loop_policy(
                    asyncio.WindowsSelectorEventLoopPolicy()
                )
        except Exception:
            # Silencia caso a política não esteja disponível
            pass

        self._client = NotionAsyncClient(auth=notion_token)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        if self._observability:
            logger.info("NotionUnifiedDataService inicializado")

    def _run(self, coro) -> Any:
        """Executa uma corrotina no loop de eventos."""
        return self._loop.run_until_complete(coro)

    def create_container(self, name: str) -> str:
        """Cria um container (página raiz) no Notion.
        
        Args:
            name: Nome do container.
            
        Returns:
            ID do container criado.
        """
        # Para o Notion, um container é uma página raiz
        # Por simplicidade, vamos usar o workspace como container padrão
        container_id = str(uuid4())
        
        if self._observability:
            logger.info(f"Container '{name}' criado com ID: {container_id}")
            
        return container_id

    def add_data_source(self, container_id: str, data_source_id: str) -> str:
        """Adiciona uma fonte de dados (database) ao container.
        
        Args:
            container_id: ID do container.
            data_source_id: ID da fonte de dados.
            
        Returns:
            ID do vínculo criado.
        """
        # No Notion, isso seria associar uma database a uma página
        # Por simplicidade, retornamos o próprio data_source_id
        if self._observability:
            logger.info(f"Data source {data_source_id} adicionada ao container {container_id}")
            
        return data_source_id

    def update_schema(self, data_source_id: str, schema: Dict[str, Any]) -> str:
        """Atualiza o schema de uma database no Notion.
        
        Args:
            data_source_id: ID da fonte de dados.
            schema: Schema das propriedades.
            
        Returns:
            ID da versão do schema.
        """
        try:
            # Import lazy para evitar acesso antes de Django estar pronto
            from smart_core_assistant_painel.app.notion_sync.models import (
                NotionDatabaseConfig,
            )
            # Busca a configuração da database
            config = NotionDatabaseConfig.objects.filter(
                data_source_id=data_source_id,
                sync_enabled=True
            ).first()
            
            if not config:
                raise ValueError(f"Configuração não encontrada para data_source_id: {data_source_id}")
            
            # Atualiza o schema na configuração
            config.notion_schema = schema
            config.save()
            
            version_id = str(uuid4())
            
            if self._observability:
                logger.info(f"Schema atualizado para data_source_id {data_source_id}, versão: {version_id}")
                
            return version_id
            
        except Exception as e:
            logger.error(f"Erro ao atualizar schema: {e}")
            raise

    def _filter_properties_by_schema(
        self,
        database_id: str,
        config: Any,
        props: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Remove propriedades que não existem no schema da database alvo.

        Tenta primeiro obter o schema ao vivo via API do Notion; caso falhe,
        usa o schema armazenado em NotionDatabaseConfig. Se nenhum schema
        estiver disponível, retorna o payload original.
        """
        try:
            allowed: set[str] = set()

            try:
                db_info = self._run(
                    self._client.request(
                        method="get",
                        path=f"databases/{database_id}",
                        body={},
                    )
                )
                live_props = db_info.get("properties", {}) or {}
                if not live_props:
                    data_sources = db_info.get("data_sources") or []
                    if data_sources and isinstance(data_sources, list):
                        schema = data_sources[0].get("schema") or {}
                        live_props = schema.get("properties", {}) or {}
                allowed = set(live_props.keys())
            except Exception as exc:
                logger.warning(
                    "Falha ao recuperar schema ao vivo do Notion: {}",
                    str(exc),
                )

            if not allowed and getattr(config, "notion_schema", None):
                try:
                    allowed = set(config.notion_schema.keys())
                except Exception:
                    allowed = set()

            if not allowed:
                return props

            filtered: Dict[str, Any] = {}
            for key, value in props.items():
                if key in allowed:
                    filtered[key] = value
                else:
                    logger.warning(
                        "Propriedade '{}' ausente no schema; removida.",
                        key,
                    )
            return filtered
        except Exception as e:
            logger.warning(
                "Falha ao validar propriedades contra schema: {}",
                str(e),
            )
            return props

    def create_item(self, data_source_id: str, payload: Dict[str, Any]) -> str:
        """Cria um item (página) na database do Notion.
        
        Args:
            data_source_id: ID da fonte de dados.
            payload: Dados do item.
            
        Returns:
            ID do item criado.
        """
        try:
            # Import lazy para evitar acesso antes de Django estar pronto
            from smart_core_assistant_painel.app.notion_sync.models import (
                NotionDatabaseConfig,
            )
            # Busca a configuração da database
            config = NotionDatabaseConfig.objects.filter(
                data_source_id=data_source_id,
                sync_enabled=True
            ).first()
            
            if not config:
                raise ValueError(f"Configuração não encontrada para data_source_id: {data_source_id}")
            
            # Identifica IDs
            database_id = str(config.notion_database_id)
            data_source_id_str = (
                str(config.data_source_id)
                if config.data_source_id
                else ""
            )
            
            # Filtra propriedades pelo schema da database
            filtered_props = self._filter_properties_by_schema(
                database_id, config, payload
            )

            # Prepara os dados da página: preferir parent via data_source_id
            # para garantir que o Notion reconheça propriedades do schema
            # da data source (como relações). Fallback para database_id.
            # Notion API (Upgrade 2025-09-03): não envie o campo `type`.
            parent: Dict[str, Any]
            # Para Data Sources, informe explicitamente o tipo do parent
            # para evitar interpretação incorreta do ID como database.
            if data_source_id_str:
                parent = {
                    "type": "data_source_id",
                    "data_source_id": data_source_id_str,
                }
            else:
                parent = {"database_id": database_id}

            page_data = {
                "parent": parent,
                "properties": filtered_props,
            }
            
            # Cria a página no Notion com fallback: tenta com
            # data_source_id e, se falhar por não encontrar base,
            # refaz com database_id.
            try:
                response = self._run(
                    self._client.request(
                        method="post",
                        path="pages",
                        body=page_data,
                    )
                )
            except APIResponseError as first_err:
                msg = str(first_err)
                if data_source_id_str and data_source_id_str in msg:
                    if self._observability:
                        logger.warning(
                            (
                                "Falha ao criar item com data_source_id {}. "
                                "Aplicando fallback para database_id."
                            ).format(data_source_id_str)
                        )
                    page_data["parent"] = {"database_id": database_id}
                    response = self._run(
                        self._client.request(
                            method="post",
                            path="pages",
                            body=page_data,
                        )
                    )
                elif "is not a property that exists" in msg:
                    # Fallback: remover propriedade ausente e tentar novamente
                    try:
                        missing_prop: str = msg.split(" is not a property")[0]
                    except Exception:
                        missing_prop = ""
                    if missing_prop and missing_prop in filtered_props:
                        if self._observability:
                            logger.warning(
                                (
                                    "Propriedade '{}' ausente no Notion; "
                                    "removida do payload e reenvio."
                                ).format(missing_prop)
                            )
                        filtered_props.pop(missing_prop, None)
                        if self._observability:
                            logger.debug(
                                "Propriedades após remoção: {}",
                                list(filtered_props.keys()),
                            )
                        page_data["properties"] = filtered_props
                        response = self._run(
                            self._client.request(
                                method="post",
                                path="pages",
                                body=page_data,
                            )
                        )
                    else:
                        raise
                else:
                    raise
            
            page_id = response.get("id", "")
            
            if self._observability:
                logger.info(f"Item criado no Notion com ID: {page_id}")
                
            return page_id
            
        except APIResponseError as e:
            logger.error(f"Erro da API do Notion ao criar item: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar item: {e}")
            raise

    def update_item(
        self, data_source_id: str, item_id: str, payload: Dict[str, Any]
    ) -> str:
        """Atualiza um item existente no Notion.
        
        Args:
            data_source_id: ID da fonte de dados.
            item_id: ID do item.
            payload: Dados atualizados.
            
        Returns:
            ID da operação de atualização.
        """
        try:
            # Prepara os dados de atualização
            update_data = {
                "properties": payload
            }
            
            # Atualiza a página no Notion
            response = self._run(
                self._client.request(
                    method="patch",
                    path=f"pages/{item_id}",
                    body=update_data,
                )
            )
            
            operation_id = str(uuid4())
            
            if self._observability:
                logger.info(f"Item {item_id} atualizado, operação: {operation_id}")
                
            return operation_id
            
        except APIResponseError as e:
            logger.error(f"Erro da API do Notion ao atualizar item: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar item: {e}")
            raise

    def add_relation_property(
        self, data_source_id: str, property_name: str, target_id: str
    ) -> str:
        """Adiciona uma propriedade de relação à database.
        
        Args:
            data_source_id: ID da fonte de dados.
            property_name: Nome da propriedade.
            target_id: ID da database alvo.
            
        Returns:
            ID da propriedade criada.
        """
        try:
            # Import lazy para evitar acesso antes de Django estar pronto
            from smart_core_assistant_painel.app.notion_sync.models import (
                NotionDatabaseConfig,
            )
            # Busca a configuração da database
            config = NotionDatabaseConfig.objects.filter(
                data_source_id=data_source_id,
                sync_enabled=True
            ).first()
            
            if not config:
                raise ValueError(f"Configuração não encontrada para data_source_id: {data_source_id}")
            
            database_id = str(config.notion_database_id)
            
            # Prepara a propriedade de relação
            relation_property = {
                property_name: {
                    "relation": {
                        "database_id": target_id
                    }
                }
            }
            
            # Atualiza a database com a nova propriedade
            response = self._run(
                self._client.request(
                    method="patch",
                    path=f"databases/{database_id}",
                    body={"properties": relation_property},
                )
            )
            
            property_id = str(uuid4())
            
            if self._observability:
                logger.info(f"Propriedade de relação '{property_name}' criada com ID: {property_id}")
                
            return property_id
            
        except APIResponseError as e:
            logger.error(f"Erro da API do Notion ao criar propriedade de relação: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar propriedade de relação: {e}")
            raise

    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do container."""
        # Implementação simplificada
        return {"id": container_id, "type": "container"}

    def get_data_source(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados da fonte de dados."""
        try:
            # Import lazy para evitar acesso antes de Django estar pronto
            from smart_core_assistant_painel.app.notion_sync.models import (
                NotionDatabaseConfig,
            )
            config = NotionDatabaseConfig.objects.filter(
                data_source_id=data_source_id,
                sync_enabled=True
            ).first()
            
            if not config:
                return None
                
            return {
                "id": data_source_id,
                "database_id": str(config.notion_database_id),
                "name": config.name,
                "schema": config.notion_schema
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter data source: {e}")
            return None

    def get_item(
        self, data_source_id: str, item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém dados de um item."""
        try:
            # Busca a página no Notion
            response = self._run(
                self._client.request(
                    method="get",
                    path=f"pages/{item_id}",
                    body={},
                )
            )
            
            return response
            
        except APIResponseError as e:
            logger.error(f"Erro da API do Notion ao obter item: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter item: {e}")
            return None

    def append_block(self, container_id: str, block: Dict[str, Any]) -> str:
        """Adiciona um bloco ao container."""
        try:
            # Adiciona bloco à página
            response = self._run(
                self._client.request(
                    method="patch",
                    path=f"blocks/{container_id}/children",
                    body={"children": [block]},
                )
            )
            
            block_id = str(uuid4())
            
            if self._observability:
                logger.info(f"Bloco adicionado ao container {container_id} com ID: {block_id}")
                
            return block_id
            
        except APIResponseError as e:
            logger.error(f"Erro da API do Notion ao adicionar bloco: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao adicionar bloco: {e}")
            raise