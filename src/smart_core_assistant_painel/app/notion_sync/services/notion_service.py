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
from .mappers import ClienteMapper, ContatoMapper


class NotionSyncService(ExternalSyncServiceInterface):
    """
    Implementação do serviço de sincronização com o Notion.

    Esta classe implementa todos os métodos da interface
    ExternalSyncServiceInterface para integração com a API do Notion.

    Attributes:
        client: Cliente da API do Notion (notion-client).
        token: Token de integração do Notion.
        database_ids: Mapeamento de models para database IDs do Notion.
    """

    def __init__(self) -> None:
        """
        Inicializa o serviço de sincronização com o Notion.

        Lê configurações do ambiente (.env) e do banco de dados Django
        (NotionDatabaseConfig) e inicializa o cliente da API.

        Prioridade de busca de database IDs:
        1. NotionDatabaseConfig (banco de dados Django)

        Raises:
            SyncConfigError: Se configurações necessárias estão ausentes.
        """
        # Lê token do .env
        self.token = config("NOTION_TOKEN", default=None)
        if not self.token:
            raise SyncConfigError(
                message="Token do Notion não encontrado",
                config_key="NOTION_TOKEN",
                details={"message": "Configure NOTION_TOKEN no arquivo .env"}
            )

        # Inicializa cliente do Notion
        try:
            self.client = NotionAsyncClient(auth=self.token)
            logger.info("Cliente do Notion inicializado com sucesso")
        except Exception as e:
            raise SyncConfigError(
                message=f"Erro ao inicializar cliente do Notion: {str(e)}",
                config_key="NOTION_TOKEN",
            ) from e

        # Busca database IDs do NotionDatabaseConfig (preferencial)
        self.database_ids: dict[str, str | None] = {}

        for model_name in ["Contato", "Cliente"]:
            db_id = NotionDatabaseConfig.get_database_id(model_name)
            self.database_ids[model_name] = db_id
            if db_id:
                logger.info(
                    f"Database ID para {model_name} carregado do NotionDatabaseConfig: {db_id[:8]}..."
                )
            else:
                logger.warning(
                    f"Database ID para {model_name} não encontrado no NotionDatabaseConfig"
                )

        # Mappers para conversão de dados
        self._mappers = {
            "Contato": ContatoMapper,
            "Cliente": ClienteMapper,
        }

    def _run(self, coro):
        return asyncio.run(coro)

    async def _request_async(self, method: str, path: str, body: dict[str, Any]):
        # Evita reuso de cliente assíncrono entre múltiplos asyncio.run
        client = NotionAsyncClient(auth=self.token)
        return await client.request(method=method, path=path, body=body)

    @override
    def create_record(
        self,
        model_name: str,
        django_id: int,
        data: dict[str, Any],
    ) -> str:
        """
        Cria um novo registro (página) no database do Notion.

        Args:
            model_name: Nome do modelo Django ("Cliente" ou "Contato").
            django_id: ID do registro no Django.
            data: Dados do registro (instância do model).

        Returns:
            ID da página criada no Notion (page_id).

        Raises:
            SyncConfigError: Se database ID não está configurado.
            NotionSyncError: Se houver erro na API do Notion.
            MappingError: Se houver erro no mapeamento de dados.
        """
        database_id = self.get_database_id(model_name)
        if not database_id:
            raise NotionSyncError(
                message=f"Database ID não configurado para {model_name}. Persista via NotionDatabaseConfig executando o setup.",
                details={"config_key": f"NotionDatabaseConfig[{model_name}]"},
            )

        try:
            # Obtém mapper apropriado
            mapper = self._mappers.get(model_name)
            if not mapper:
                raise MappingError(
                    message=f"Mapper não encontrado para {model_name}",
                    field_name="model_name",
                    source_value=model_name,
                )

            # Converte dados para formato Notion
            # data é a instância do model Django
            properties = mapper.to_notion_properties(data)

            # Cria página no Notion
            logger.info(f"Criando página no Notion para {model_name} #{django_id}")

            # Tentar usar método direto da API com dicionário simples
            try:
                page_data = {
                    "parent": {"database_id": database_id},
                    "properties": properties,
                }

                # Fazer chamada direta usando o método request do client
                response = self._run(
                    self._request_async(
                        method="post",
                        path="pages",
                        body=page_data
                    )
                )

                page_id = response.get("id")
                logger.success(
                    f"✅ Página criada no Notion: {page_id} "
                    f"para {model_name} #{django_id}"
                )

                return page_id

            except Exception as e:
                logger.error(f"❌ Erro ao criar página no Notion: {e}")
                raise SyncError(
                    message=f"Erro inesperado ao criar registro: {str(e)}",
                    details={"model_name": model_name, "django_id": django_id}
                ) from e

        except APIResponseError as e:
            error_msg = str(e)
            logger.error(
                f"❌ Erro da API do Notion ao criar {model_name} #{django_id}: "
                f"{e.code} - {error_msg}"
            )
            raise NotionSyncError(
                message=f"Erro ao criar página no Notion: {error_msg}",
                status_code=e.status,
                notion_error=e.code,
                details={
                    "model_name": model_name,
                    "django_id": django_id,
                    "response": error_msg,
                }
            ) from e

        except MappingError:
            raise

        except Exception as e:
            logger.error(
                f"❌ Erro inesperado ao criar {model_name} #{django_id}: {e}"
            )
            raise SyncError(
                message=f"Erro inesperado ao criar registro: {str(e)}",
                details={"model_name": model_name, "django_id": django_id}
            ) from e

    @override
    def update_record(
        self,
        model_name: str,
        external_id: str,
        django_id: int,
        data: dict[str, Any],
    ) -> bool:
        """
        Atualiza um registro (página) existente no Notion.

        Args:
            model_name: Nome do modelo Django ("Cliente" ou "Contato").
            external_id: ID da página no Notion (page_id).
            django_id: ID do registro no Django.
            data: Dados atualizados do registro (instância do model).

        Returns:
            True se atualização foi bem-sucedida.

        Raises:
            NotionSyncError: Se houver erro na API do Notion.
            MappingError: Se houver erro no mapeamento de dados.
        """
        try:
            # Obtém mapper apropriado
            mapper = self._mappers.get(model_name)
            if not mapper:
                raise MappingError(
                    message=f"Mapper não encontrado para {model_name}",
                    field_name="model_name",
                    source_value=model_name,
                )

            # Converte dados para formato Notion
            # data é a instância do model Django
            properties = mapper.to_notion_properties(data)

            # Atualiza página no Notion
            logger.info(f"Atualizando página {external_id} no Notion para {model_name} #{django_id}")

            # Prepara dados para atualização
            page_data = {
                "properties": properties,
            }

            # Faz chamada direta usando o método request do client
            response = self._run(
                self._request_async(
                    method="patch",
                    path=f"pages/{external_id}",
                    body=page_data
                )
            )

            page_id = response.get("id")
            logger.success(
                f"✅ Página atualizada no Notion: {page_id} "
                f"para {model_name} #{django_id}"
            )

            return True

        except APIResponseError as e:
            error_msg = str(e)
            logger.error(
                f"❌ Erro da API do Notion ao atualizar {model_name} #{django_id}: "
                f"{e.code} - {error_msg}"
            )
            raise NotionSyncError(
                message=f"Erro ao atualizar página no Notion: {error_msg}",
                status_code=e.status,
                notion_error=e.code,
                details={
                    "model_name": model_name,
                    "django_id": django_id,
                    "external_id": external_id,
                    "response": error_msg,
                }
            ) from e

        except MappingError:
            raise

        except Exception as e:
            logger.error(
                f"❌ Erro inesperado ao atualizar {model_name} #{django_id}: {e}"
            )
            raise SyncError(
                message=f"Erro inesperado ao atualizar registro: {str(e)}",
                details={
                    "model_name": model_name,
                    "django_id": django_id,
                    "external_id": external_id,
                }
            ) from e

    @override
    def delete_record(
        self,
        model_name: str,
        external_id: str,
    ) -> bool:
        """
        Arquiva (deleta) um registro no Notion.

        Nota: O Notion não permite deleção real de páginas, apenas arquivamento.

        Args:
            model_name: Nome do modelo Django ("Cliente" ou "Contato").
            external_id: ID da página no Notion (page_id).

        Returns:
            True se arquivamento foi bem-sucedido.

        Raises:
            NotionSyncError: Se houver erro na API do Notion.
        """
        try:
            logger.info(
                f"Arquivando página {external_id} no Notion "
                f"para {model_name}"
            )

            # Arquiva página (Notion não permite deleção real)
            page_data = {
                "archived": True,
            }

            # Faz chamada direta usando o método request do client
            response = self._run(
                self._request_async(
                    method="patch",
                    path=f"pages/{external_id}",
                    body=page_data
                )
            )

            page_id = response.get("id")
            logger.success(
                f"✅ Página arquivada no Notion: {page_id} "
                f"para {model_name}"
            )

            return True

        except APIResponseError as e:
            error_msg = str(e)
            logger.error(
                f"❌ Erro da API do Notion ao arquivar {model_name}: "
                f"{e.code} - {error_msg}"
            )
            raise NotionSyncError(
                message=f"Erro ao arquivar página no Notion: {error_msg}",
                status_code=e.status,
                notion_error=e.code,
                details={
                    "model_name": model_name,
                    "external_id": external_id,
                    "response": error_msg,
                }
            ) from e

        except Exception as e:
            logger.error(
                f"❌ Erro inesperado ao arquivar {model_name}: {e}"
            )
            raise SyncError(
                message=f"Erro inesperado ao arquivar registro: {str(e)}",
                details={"model_name": model_name, "external_id": external_id}
            ) from e

    @override
    def validate_connection(self) -> bool:
        """
        Valida se a conexão com o Notion está funcionando.

        Testa credenciais e verifica se os databases configurados existem.

        Returns:
            True se a conexão está válida e funcional.

        Raises:
            SyncConfigError: Se credenciais são inválidas.
            SyncError: Se houver erro na validação.
        """
        try:
            logger.info("Validando conexão com o Notion...")

            # Testa autenticação obtendo informações do bot
            try:
                bot_info = self._run(self.client.users.me())
                logger.info(f"✅ Autenticação OK - Bot: {bot_info.get('name', 'N/A')}")
            except APIResponseError as e:
                if e.status == 401:
                    raise Exception(
                        message="Token do Notion inválido ou expirado",
                        config_key="NOTION_TOKEN",
                        details={"error": str(e)}
                    )
                raise

            # Verifica databases configurados
            for model_name, database_id in self.database_ids.items():
                if database_id:
                    try:
                        db = self._run(self.client.databases.retrieve(database_id))
                        logger.info(
                            f"✅ Database '{model_name}' OK - "
                            f"Título: {db.get('title', [{}])[0].get('plain_text', 'N/A')}"
                        )
                    except APIResponseError as e:
                        logger.warning(
                            f"⚠️  Database '{model_name}' ({database_id}) "
                            f"não acessível: {str(e)}"
                        )
                else:
                    logger.warning(
                        f"⚠️  Database ID não configurado para '{model_name}'"
                    )

            logger.success("✅ Validação concluída - Conexão OK")
            return True

        except SyncConfigError:
            raise

        except Exception as e:
            logger.error(f"❌ Erro ao validar conexão: {e}")
            raise SyncError(
                message=f"Erro ao validar conexão com Notion: {str(e)}",
                details={"error": str(e)}
            ) from e

    @override
    def handle_webhook(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """
        Processa um webhook recebido do Notion.

        Nota: Esta é uma implementação básica. O Notion não tem webhooks
        nativos ainda (usa polling), mas este método está pronto para
        quando o recurso for disponibilizado.

        Args:
            payload: Corpo da requisição do webhook (JSON).
            headers: Cabeçalhos HTTP da requisição.

        Returns:
            Dicionário com dados normalizados para atualizar o Django.

        Raises:
            SyncError: Se houver erro no processamento.
        """
        try:
            logger.info("Processando webhook do Notion")

            # TODO: Implementar validação de assinatura quando disponível

            # Extrai dados do webhook
            page_id = payload.get("id")
            if not page_id:
                raise SyncError(
                    message="Webhook do Notion sem ID de página",
                    details={"payload": payload}
                )

            # Busca página no Notion para obter dados atualizados
            page = self._run(self.client.pages.retrieve(page_id=page_id))
            properties = page.get("properties", {})

            # Extrai Django ID para identificar o registro
            django_id_prop = properties.get("Django ID", {})
            django_id = django_id_prop.get("number")

            if not django_id:
                raise SyncError(
                    message="Página do Notion sem Django ID",
                    details={"page_id": page_id}
                )

            # TODO: Determinar model_name baseado no database
            # Por enquanto, retorna dados básicos
            return {
                "model_name": "Unknown",  # Precisa ser inferido do database
                "django_id": int(django_id),
                "external_id": page_id,
                "action": "update",
                "data": properties,
            }

        except Exception as e:
            logger.error(f"❌ Erro ao processar webhook: {e}")
            raise SyncError(
                message=f"Erro ao processar webhook do Notion: {str(e)}",
                details={"payload": payload}
            ) from e

    @override
    def sync_existing_records(
        self,
        model_name: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Sincroniza registros existentes em lote (batch).

        Args:
            model_name: Nome do modelo Django ("Cliente" ou "Contato").
            records: Lista de registros, cada um com django_id, external_id e data.

        Returns:
            Estatísticas da sincronização (total, created, updated, failed).

        Raises:
            SyncError: Se houver erro na sincronização em lote.
        """
        logger.info(f"Iniciando sincronização em lote de {len(records)} {model_name}(s)")

        stats = {
            "total": len(records),
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }

        for record in records:
            django_id = record["django_id"]
            external_id = record.get("external_id")
            data = record["data"]

            try:
                if external_id:
                    # Atualiza registro existente
                    self.update_record(model_name, external_id, django_id, data)
                    stats["updated"] += 1
                else:
                    # Cria novo registro
                    page_id = self.create_record(model_name, django_id, data)
                    stats["created"] += 1

            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append({
                    "django_id": django_id,
                    "error": str(e),
                })
                logger.error(
                    f"❌ Erro ao sincronizar {model_name} #{django_id}: {e}"
                )

        logger.info(
            f"Sincronização em lote concluída: "
            f"{stats['created']} criados, {stats['updated']} atualizados, "
            f"{stats['failed']} falhas"
        )

        return stats

    @override
    def get_database_id(self, model_name: str) -> str | None:
        """
        Retorna o ID do database no Notion para o modelo especificado.

        Busca primeiro no cache (self.database_ids) que foi populado na
        inicialização a partir do NotionDatabaseConfig.

        Em caso de atualização recente, tenta buscar novamente do
        NotionDatabaseConfig para preencher o cache.

        Args:
            model_name: Nome do modelo Django ("Cliente" ou "Contato").

        Returns:
            ID do database no Notion, ou None se não configurado.
        """
        # Primeiro tenta do cache
        db_id = self.database_ids.get(model_name)

        if db_id:
            return db_id

        # Busca dinâmica: tenta buscar novamente do NotionDatabaseConfig
        # (pode ter sido configurado após a inicialização do serviço)
        db_id = NotionDatabaseConfig.get_database_id(model_name)

        if db_id:
            # Atualiza o cache
            self.database_ids[model_name] = db_id
            logger.info(
                f"Database ID para {model_name} encontrado em busca "
                f"dinâmica: {db_id[:8]}..."
            )
            return db_id

        return None

    @override
    def health_check(self) -> dict[str, Any]:
        """
        Verifica o estado de saúde da integração com o Notion.

        Returns:
            Dicionário com informações de saúde da integração.
        """
        health = {
            "status": "unknown",
            "api_reachable": False,
            "rate_limit_remaining": None,
            "last_sync_timestamp": None,
            "errors_last_hour": 0,
            "message": None,
        }

        try:
            # Testa conectividade básica
            self._run(self.client.users.me())
            health["api_reachable"] = True
            health["status"] = "healthy"
            health["message"] = "Conexão com Notion OK"

        except APIResponseError as e:
            health["status"] = "down"
            health["message"] = f"Erro na API: {e.message}"

        except Exception as e:
            health["status"] = "down"
            health["message"] = f"Erro: {str(e)}"

        return health
