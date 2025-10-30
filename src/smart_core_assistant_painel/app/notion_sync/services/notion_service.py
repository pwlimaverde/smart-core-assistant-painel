"""
Serviço de sincronização com a API do Notion.

Este módulo contém a implementação concreta do serviço de sincronização
com o Notion, implementando a interface ExternalSyncServiceInterface.
"""

import os
from datetime import datetime
from typing import Any, override

from decouple import config
from loguru import logger
import asyncio
from notion_py_client.notion_client import NotionAsyncClient, APIResponseError

from ..exceptions import (
    MappingError,
    NotionSyncError,
    SyncError,
)
from ..interfaces import ExternalSyncServiceInterface
from ..models import NotionDatabaseConfig
from .mappers import (
    AtendenteMapper,
    AtendimentoMapper,
    ClienteMapper,
    ContatoMapper,
    DepartamentoMapper,
    MensagemMapper,
)


class NotionSyncService(ExternalSyncServiceInterface):
    """
    Implementação do serviço de sincronização com o Notion.
    """

    def __init__(self) -> None:
        """
        Inicializa o serviço de sincronização com o Notion.
        """
        self.token = config("NOTION_TOKEN", default=None)
        if not self.token:
            raise SyncError(
                message="Token do Notion não encontrado",
                details={
                    "config_key": "NOTION_TOKEN",
                    "hint": "Configure NOTION_TOKEN no arquivo .env",
                },
            )

        try:
            # Inicializa cliente Notion (versão API padrão do cliente)
            self.client = NotionAsyncClient(auth=self.token)
            logger.info("Cliente do Notion inicializado com sucesso")
        except Exception as e:
            raise SyncError(
                message=f"Erro ao inicializar cliente do Notion: {str(e)}",
                details={"config_key": "NOTION_TOKEN"},
            ) from e

        self.database_ids: dict[str, str | None] = {}
        self.data_source_ids: dict[str, str | None] = {}

        # Inicializa cache de IDs com base no mapeamento padronizado
        for simple_name in (
            "Contato",
            "Cliente",
            "Departamento",
            "Atendente",
            "Atendimento",
            "Mensagem",
        ):
            full_name = self._resolve_full_name(simple_name)
            db_id = NotionDatabaseConfig.get_database_id(full_name)
            self.database_ids[simple_name] = db_id
            if db_id:
                logger.info(
                    (
                        "Database ID para {} carregado: {}..."
                    ).format(simple_name, db_id[:8])
                )
            else:
                logger.warning(
                    (
                        "Database ID para {} não encontrado"
                    ).format(simple_name)
                )

            # Carrega data_source_id quando disponível
            cfg = self._get_config(simple_name, only_enabled=True)
            ds_id = str(cfg.data_source_id) if cfg and cfg.data_source_id else None
            self.data_source_ids[simple_name] = ds_id
            if ds_id:
                logger.info(
                    (
                        "Data Source ID para {} carregado: {}..."
                    ).format(simple_name, ds_id[:8])
                )
            else:
                logger.warning(
                    (
                        "Data Source ID para {} não encontrado"
                    ).format(simple_name)
                )
            # Loga prontidão de configuração de forma clara
            if cfg:
                ready = cfg.is_ready_for_sync()
                logger.debug(
                    (
                        "Prontidão config {}: ready={} sync_enabled={} db_id_set={} ds_id_set={}"
                    ).format(
                        simple_name,
                        ready,
                        cfg.sync_enabled,
                        bool(cfg.notion_database_id),
                        bool(cfg.data_source_id),
                    )
                )

        self._mappers = {
            "Contato": ContatoMapper,
            "Cliente": ClienteMapper,
            "Departamento": DepartamentoMapper,
            "Atendente": AtendenteMapper,
            "Atendimento": AtendimentoMapper,
            "Mensagem": MensagemMapper,
        }

    def _run(self, coro):
        return asyncio.run(coro)

    async def _request_async(
        self, method: str, path: str, body: dict[str, Any]
    ):
        """
        Executa requisições com o cliente atual mantendo a versão da API.
        """
        return await self.client.request(method=method, path=path, body=body)

    def _filter_properties_by_schema(
        self, model_name: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Remove do payload quaisquer propriedades que não existam no schema
        da database do Notion correspondente.

        Observação: usa primeiro o schema ao vivo via API do Notion; se falhar,
        faz fallback para o schema salvo em NotionDatabaseConfig.
        """
        try:
            # Localiza configuração pelo nome do modelo usando helper unificado
            config = self._get_config(model_name, only_enabled=True)

            allowed: set[str] = set()

            # Tenta obter schema ao vivo da database
            if config and config.notion_database_id:
                try:
                    db_info = self._run(
                        self.client.databases.retrieve(
                            str(config.notion_database_id)
                        )
                    )
                    live_props = db_info.get("properties", {}) or {}
                    allowed = set(live_props.keys())
                except Exception as e:
                    logger.warning(
                        "Falha ao recuperar schema ao vivo do Notion: {}",
                        str(e),
                    )

            # Fallback para schema armazenado na configuração
            if not allowed and config and config.notion_schema:
                allowed = set(config.notion_schema.keys())

            # Sem schema disponível: retorna como está
            if not allowed:
                return properties

            # Filtra propriedades desconhecidas
            filtered: dict[str, Any] = {}
            for key, value in properties.items():
                if key in allowed:
                    filtered[key] = value
                else:
                    logger.warning(
                        "Propriedade '{}' ausente no schema; removida do payload.",
                        key,
                    )

            return filtered
        except Exception as e:
            logger.warning(
                "Falha ao validar propriedades contra schema: {}", str(e)
            )
            return properties

    @override
    def create_record(
        self,
        model_name: str,
        django_id: int,
        data: Any,
    ) -> str:
        """
        Cria um novo registro (página ou bloco) no Notion.
        """
        mapper = self._mappers.get(model_name)
        if not mapper:
            raise MappingError(f"Mapper não encontrado para {model_name}")

        # Mensagens passam a ser criadas como páginas na database de mensagens.

        # Lógica padrão para criar páginas
        database_id = self.get_database_id(model_name)
        if not database_id:
            raise NotionSyncError(
                (
                    "Database ID não configurado para {}."
                ).format(model_name)
            )

        try:
            properties = mapper.to_notion_properties(data)
            properties = self._filter_properties_by_schema(
                model_name, properties
            )
            logger.debug(
                "Propriedades finais para {}: {}",
                model_name,
                list(properties.keys()),
            )
            # Usa data_source_id como parent quando disponível (API 2025-09-03)
            ds_id = self.get_data_source_id(model_name)
            if ds_id:
                parent: dict[str, Any] = {
                    "type": "data_source_id",
                    "data_source_id": ds_id,
                }
            else:
                parent = {"database_id": database_id}

            page_data = {"parent": parent, "properties": properties}

            response = self._run(
                self._request_async(method="post", path="pages", body=page_data)
            )

            page_id = response.get("id")
            logger.success(
                (
                    "✅ Página criada no Notion: {} para {} #{}"
                ).format(page_id, model_name, django_id)
            )
            return page_id

        except APIResponseError as e:
            logger.error(
                (
                    "❌ Erro da API do Notion ao criar {} #{}: {} - {}"
                ).format(model_name, django_id, e.code, e)
            )
            raise NotionSyncError(
                f"Erro ao criar página no Notion: {e}"
            ) from e
        except Exception as e:
            logger.error(
                (
                    "❌ Erro inesperado ao criar {} #{}: {}"
                ).format(model_name, django_id, e)
            )
            raise SyncError(
                f"Erro inesperado ao criar registro: {e}"
            ) from e

    @override
    def update_record(
        self,
        model_name: str,
        external_id: str,
        django_id: int,
        data: Any,
    ) -> bool:
        """
        Atualiza um registro (página) existente no Notion.
        """
        # Atualizações de Mensagens como páginas são suportadas.

        try:
            mapper = self._mappers.get(model_name)
            if not mapper:
                raise MappingError(f"Mapper não encontrado para {model_name}")

            properties = mapper.to_notion_properties(data)
            properties = self._filter_properties_by_schema(
                model_name, properties
            )
            logger.debug(
                "Propriedades finais para {} (update): {}",
                model_name,
                list(properties.keys()),
            )
            page_data = {"properties": properties}

            response = self._run(
                self._request_async(
                    method="patch",
                    path=f"pages/{external_id}",
                    body=page_data,
                )
            )

            logger.success(
                (
                    "✅ Página atualizada no Notion: {} para {} #{}"
                ).format(response.get("id"), model_name, django_id)
            )
            return True

        except APIResponseError as e:
            logger.error(
                (
                    "❌ Erro da API do Notion ao atualizar {} #{}: {} - {}"
                ).format(model_name, django_id, e.code, e)
            )
            raise NotionSyncError(
                f"Erro ao atualizar página no Notion: {e}"
            ) from e
        except Exception as e:
            logger.error(
                (
                    "❌ Erro inesperado ao atualizar {} #{}: {}"
                ).format(model_name, django_id, e)
            )
            raise SyncError(
                f"Erro inesperado ao atualizar registro: {e}"
            ) from e

    @override
    def delete_record(
        self,
        model_name: str,
        external_id: str,
    ) -> bool:
        """
        Arquiva uma página ou deleta um bloco no Notion.
        """
        try:
            # Arquiva página
            page_data = {"archived": True}
            response = self._run(
                self._request_async(
                    method="patch",
                    path=f"pages/{external_id}",
                    body=page_data,
                )
            )
            logger.success(
                (
                    "✅ Página arquivada no Notion: {} para {}"
                ).format(response.get("id"), model_name)
            )
            return True

        except APIResponseError as e:
            logger.error(f"❌ Erro da API do Notion ao deletar/arquivar {model_name}: {e.code} - {e}")
            raise NotionSyncError(f"Erro ao deletar/arquivar no Notion: {e}") from e
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao deletar/arquivar {model_name}: {e}")
            raise SyncError(f"Erro inesperado ao deletar/arquivar registro: {e}") from e

    # ... (restante dos métodos como validate_connection, handle_webhook, etc. permanecem os mesmos)
    @override
    def validate_connection(self) -> bool:
        """
        Valida se a conexão com o Notion está funcionando.
        """
        try:
            logger.info("Validando conexão com o Notion...")
            bot_info = self._run(self.client.users.me())
            logger.info(
                (
                    "✅ Autenticação OK - Bot: {}"
                ).format(bot_info.get("name", "N/A"))
            )
            return True
        except Exception as e:
            logger.error(("❌ Erro ao validar conexão: {}" ).format(e))
            raise SyncError(
                f"Erro ao validar conexão com Notion: {e}"
            ) from e

    @override
    def handle_webhook(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        raise NotImplementedError("Webhook handler não implementado.")

    @override
    def sync_existing_records(
        self,
        model_name: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        raise NotImplementedError("Sincronização em lote não implementada.")

    @override
    def get_database_id(self, model_name: str) -> str | None:
        db_id = self.database_ids.get(model_name)
        if db_id:
            return db_id

        full_name = self._resolve_full_name(model_name)
        db_id = NotionDatabaseConfig.get_database_id(full_name)

        if db_id:
            self.database_ids[model_name] = db_id
            return db_id
        return None

    def get_data_source_id(self, model_name: str) -> str | None:
        """
        Obtém o data_source_id para uso como parent ao criar páginas.

        Args:
            model_name: Nome simples do modelo (ex.: "Contato").

        Returns:
            Data Source ID do Notion ou None se não encontrado.
        """
        ds_id = self.data_source_ids.get(model_name)
        if ds_id:
            return ds_id

        try:
            config = self._get_config(model_name, only_enabled=True)
            if config and config.data_source_id:
                ds_id_str = str(config.data_source_id)
                self.data_source_ids[model_name] = ds_id_str
                return ds_id_str
        except Exception:
            # Silencia erros de acesso à base; retorna None
            pass
        return None

    @override
    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError("Health check não implementado.")

    # Helpers internos
    def _resolve_full_name(self, model_name: str) -> str:
        """
        Resolve o nome completo "app.Model" armazenado em NotionDatabaseConfig
        a partir do nome simples do modelo.

        Comentário: o projeto armazena "clientes.Contato", "operacional.Atendente",
        etc., sem o prefixo do app principal (ex.: "ui.").
        """
        mapping: dict[str, str] = {
            "Contato": "clientes.Contato",
            "Cliente": "clientes.Cliente",
            "Departamento": "operacional.Departamento",
            "Atendente": "operacional.Atendente",
            "Atendimento": "atendimentos.Atendimento",
            "Mensagem": "atendimentos.Mensagem",
        }
        return mapping.get(model_name, model_name)

    def _get_config(
        self, model_name: str, *, only_enabled: bool = True
    ) -> NotionDatabaseConfig | None:
        """
        Localiza a configuração NotionDatabaseConfig para um modelo.

        Args:
            model_name: Nome simples do modelo (ex.: "Contato").
            only_enabled: Se True, retorna apenas configurações com sync_enabled.

        Returns:
            Instância de NotionDatabaseConfig ou None.
        """
        full_name = self._resolve_full_name(model_name)
        qs = NotionDatabaseConfig.objects.filter(
            django_model__icontains=full_name
        )
        if only_enabled:
            qs = qs.filter(sync_enabled=True)
        return qs.first()
