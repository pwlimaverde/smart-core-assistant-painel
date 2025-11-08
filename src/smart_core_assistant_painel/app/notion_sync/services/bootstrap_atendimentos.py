"""Serviço de bootstrap para Atendimentos/Mensagens no Notion.

Cria databases mínimas, configura os relacionamentos essenciais e salva as
configurações em `NotionDatabaseConfig`. Mantém consistência com os serviços
existentes (Clientes/Operacional) e evita importar scripts com efeitos
colaterais.

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


class NotionAtendimentosBootstrapService:
    """Bootstrap mínimo para Atendimentos e Mensagens.

    - Cria databases no Notion (sem páginas de exemplo).
    - Configura relações entre Mensagens → Atendimentos e
      Atendimentos ↔ Contatos/Departamentos/Atendentes/Mensagens.
    - Persiste `NotionDatabaseConfig` com slugs de atendimentos.
    """

    def __init__(self) -> None:
        self._token: Optional[str] = os.getenv("NOTION_TOKEN")
        self._root_page_id: Optional[str] = os.getenv("NOTION_PAGE_ID")
        if not self._token or not self._root_page_id:
            raise ValueError(
                "NOTION_TOKEN e NOTION_PAGE_ID devem estar definidos no .env"
            )
        self._client = NotionAsyncClient(auth=self._token)

    async def _create_atendimento_database(self) -> Any:
        """Cria ou reutiliza a database de Atendimentos.

        Idempotência:
        - Se existir config `ui_atendimentos_atendimento`, tenta recuperar a
          database e reutiliza.
        - Caso a config aponte para um ID inexistente, faz fallback de busca
          por título ("Atendimentos CRM").
        - Se não encontrar, cria uma nova.
        """
        # Tentativa de reutilizar via NotionDatabaseConfig
        try:
            cfg = await sync_to_async(
                NotionDatabaseConfig.objects.filter(
                    slug="ui_atendimentos_atendimento"
                ).first
            )()
        except Exception:
            cfg = None

        if cfg and getattr(cfg, "notion_database_id", None):
            try:
                reused = await self._client.databases.retrieve(
                    {"database_id": str(cfg.notion_database_id)}
                )
                logger.info(
                    "Reutilizando database Atendimentos: {}",
                    getattr(reused, "id", None),
                )
                return reused
            except Exception as exc:
                logger.warning(
                    (
                        "Config aponta DB de Atendimentos ausente; "
                        "tentando busca por título ({})."
                    ),
                    exc,
                )
                try:
                    res = await self._client.request(
                        method="post",
                        path="search",
                        body={
                            "query": "Atendimentos CRM",
                            "filter": {
                                "value": "database",
                                "property": "object",
                            },
                        },
                    )
                    results = (
                        res.get("results")
                        if isinstance(res, dict)
                        else getattr(res, "results", None)
                    )
                    if results:
                        candidate = results[0]
                        cand_id = (
                            str(candidate.get("id"))
                            if isinstance(candidate, dict)
                            else getattr(candidate, "id", "")
                        )
                        reused = await self._client.databases.retrieve(
                            {"database_id": cand_id}
                        )
                        logger.info(
                            "Reutilizando via busca: {}",
                            getattr(reused, "id", None),
                        )
                        return reused
                except Exception:
                    # prossegue para criação
                    pass
        properties: dict[str, Any] = {
            "Assunto": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "fila", "color": "gray"},
                        {"name": "em_atendimento", "color": "blue"},
                        {
                            "name": "pendencia",
                            "color": "yellow",
                        },
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
            "Contexto Conversa": {"rich_text": {}},
            "Data Início": {"date": {}},
            "Data Fim": {"date": {}},
            "Data Última Mensagem": {"date": {}},
            "Canal": {
                "select": {
                    "options": [
                        {"name": "whatsapp", "color": "green"},
                        {"name": "email", "color": "blue"},
                        {"name": "telefone", "color": "orange"},
                        {"name": "web", "color": "purple"},
                    ]
                }
            },
            "Tags": {"multi_select": {"options": []}},
            "Avaliação": {"number": {"format": "number"}},
            "Feedback": {"rich_text": {}},
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {"type": "text", "text": {"content": "🎯 Atendimentos CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "🎯"},
            "initial_data_source": {
                "name": "Atendimentos",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info(
            "Database Atendimentos criada: {}",
            getattr(created, "id", None),
        )
        return created

    async def _create_mensagem_database(self, atendimento_db: Any) -> Any:
        """Cria ou reutiliza a database de Mensagens com relação para
        Atendimentos.

        Idempotência:
        - Se existir config `ui_atendimentos_mensagem`, tenta recuperar a
          database e reutiliza.
        - Garante que a relação "Atendimento Relacionado" exista e a reversa
          "Mensagens Relacionadas" seja configurada.
        - Caso não exista, cria uma nova.
        """
        if not getattr(atendimento_db, "data_sources", None):
            raise ValueError("Database de atendimentos sem data_source")

        atendimento_ds_id: str = atendimento_db.data_sources[0]["id"]

        # Tentativa de reutilizar via NotionDatabaseConfig
        try:
            cfg = await sync_to_async(
                NotionDatabaseConfig.objects.filter(
                    slug="ui_atendimentos_mensagem"
                ).first
            )()
        except Exception:
            cfg = None

        if cfg and getattr(cfg, "notion_database_id", None):
            try:
                reused = await self._client.databases.retrieve(
                    {"database_id": str(cfg.notion_database_id)}
                )
                # Verificar se a relação existe; se não, adicionar.
                mensagem_ds_id: Optional[str] = (
                    reused.data_sources[0]["id"]
                    if getattr(reused, "data_sources", None)
                    else None
                )
                try:
                    info = await self._client.request(
                        method="get", path=f"databases/{reused.id}"
                    )
                except Exception:
                    info = {}

                def _has_prop(db_info: dict[str, Any], name: str) -> bool:
                    try:
                        for ds in db_info.get("data_sources") or []:
                            props_ds: dict[str, Any] = ds.get("properties", {})
                            if name in props_ds:
                                return True
                        props_root: dict[str, Any] = db_info.get(
                            "properties", {}
                        )
                        return name in props_root
                    except Exception:
                        return False

                has_relation = _has_prop(
                    info if isinstance(info, dict) else {},
                    "Atendimento Relacionado",
                )

                if not has_relation and mensagem_ds_id:
                    update_msg: dict[str, Any] = {
                        "properties": {
                            "Atendimento Relacionado": {
                                "type": "relation",
                                "relation": {
                                    "data_source_id": atendimento_ds_id,
                                    "single_property": {},
                                    "dual_property": {
                                        "synced_property_name": (
                                            "Mensagens Relacionadas"
                                        ),
                                    },
                                },
                            }
                        }
                    }
                    await self._client.request(
                        method="patch",
                        path=f"data_sources/{mensagem_ds_id}",
                        body=update_msg,
                    )
                    logger.info("Relação adicionada na Mensagens reutilizada")
                else:
                    logger.info(
                        "Reutilizando database Mensagens: {}",
                        getattr(reused, "id", None),
                    )
                return reused
            except Exception as exc:
                logger.warning(
                    (
                        "Config aponta DB de Mensagens ausente; "
                        "tentando busca por título ({})."
                    ),
                    exc,
                )
                try:
                    res = await self._client.request(
                        method="post",
                        path="search",
                        body={
                            "query": "Mensagens CRM",
                            "filter": {
                                "value": "database",
                                "property": "object",
                            },
                        },
                    )
                    results = (
                        res.get("results")
                        if isinstance(res, dict)
                        else getattr(res, "results", None)
                    )
                    if results:
                        candidate = results[0]
                        cand_id = (
                            str(candidate.get("id"))
                            if isinstance(candidate, dict)
                            else getattr(candidate, "id", "")
                        )
                        reused = await self._client.databases.retrieve(
                            {"database_id": cand_id}
                        )
                        # Tentar garantir relação se possível
                        try:
                            info = await self._client.request(
                                method="get",
                                path=f"databases/{reused.id}",
                            )
                            msg_ds_id: Optional[str] = (
                                reused.data_sources[0]["id"]
                                if getattr(reused, "data_sources", None)
                                else None
                            )
                            if msg_ds_id:
                                update_msg = {
                                    "properties": {
                                        "Atendimento Relacionado": {
                                            "type": "relation",
                                            "relation": {
                                                "data_source_id": (
                                                    atendimento_ds_id
                                                ),
                                                "single_property": {},
                                                "dual_property": {
                                                    "synced_property_name": (
                                                        "Mensagens "
                                                        "Relacionadas"
                                                    ),
                                                },
                                            },
                                        }
                                    }
                                }
                                await self._client.request(
                                    method="patch",
                                    path=f"data_sources/{msg_ds_id}",
                                    body=update_msg,
                                )
                        except Exception:
                            pass
                        logger.info(
                            "Reutilizando via busca: {}",
                            getattr(reused, "id", None),
                        )
                        return reused
                except Exception:
                    # prossegue para criação
                    pass

        properties: dict[str, Any] = {
            "Conteúdo": {"title": {}},
            "Atendimento Relacionado": {
                "relation": {
                    "data_source_id": atendimento_ds_id,
                    "single_property": {},
                    "dual_property": {
                        "synced_property_name": "Mensagens Relacionadas",
                    },
                }
            },
            "Intenção Detectada": {"rich_text": {}},
            "Entidades Extraídas": {"rich_text": {}},
            "Tipo": {
                "select": {
                    "options": [
                        {"name": "Texto", "color": "blue"},
                        {"name": "Imagem", "color": "green"},
                        {"name": "Vídeo", "color": "purple"},
                        {"name": "Áudio", "color": "orange"},
                        {"name": "Documento", "color": "gray"},
                        {"name": "Sticker", "color": "pink"},
                        {"name": "Localização", "color": "red"},
                        {"name": "Contato", "color": "blue"},
                        {"name": "Lista", "color": "yellow"},
                        {"name": "Botões", "color": "purple"},
                        {"name": "Enquete", "color": "green"},
                        {"name": "Reação", "color": "pink"},
                    ]
                }
            },
            "Remetente": {
                "select": {
                    "options": [
                        {"name": "contato", "color": "blue"},
                        {"name": "bot", "color": "gray"},
                        {
                            "name": "atendente_humano",
                            "color": "green",
                        },
                    ]
                }
            },
            "Timestamp": {"date": {}},
            "Message ID WhatsApp": {"rich_text": {}},
            "Respondida": {"checkbox": {}},
            "Resposta Bot": {"rich_text": {}},
            "Confiança Resposta": {"number": {"format": "percent"}},
            "Metadados": {"rich_text": {}},
        }

        params: dict[str, Any] = {
            "parent": {"type": "page_id", "page_id": self._root_page_id},
            "title": [
                {"type": "text", "text": {"content": "💬 Mensagens CRM"}}
            ],
            "icon": {"type": "emoji", "emoji": "💬"},
            "initial_data_source": {
                "name": "Mensagens",
                "properties": properties,
            },
        }
        created = await self._client.databases.create(params)
        logger.info(
            "Database Mensagens criada: {}",
            getattr(created, "id", None),
        )
        return created

    async def _add_relations_to_atendimentos(
        self, mensagem_db: Any, atendimento_db: Any
    ) -> None:
        """Adiciona relações em Atendimentos e reversos nas demais bases.

        Comentários:
        - Usa atualização idempotente via endpoint de `data_sources`.
        - Depende das configs de Clientes/Operacional já existentes.
        """
        # Buscar configs necessárias
        try:
            contato_cfg = await sync_to_async(
                NotionDatabaseConfig.objects.get
            )(slug="ui_clientes_contato")
            dep_cfg = await sync_to_async(NotionDatabaseConfig.objects.get)(
                slug="ui_operacional_departamento"
            )
            at_cfg = await sync_to_async(NotionDatabaseConfig.objects.get)(
                slug="ui_operacional_atendente"
            )
        except NotionDatabaseConfig.DoesNotExist as exc:
            logger.error("Configuração ausente para relação: {}", exc)
            raise ValueError(
                "Execute primeiro bootstrap de clientes e operacional"
            )

        # Recuperar databases para obter data_source_ids
        contato_db = await self._client.databases.retrieve(
            {"database_id": str(contato_cfg.notion_database_id)}
        )
        departamento_db = await self._client.databases.retrieve(
            {"database_id": str(dep_cfg.notion_database_id)}
        )
        atendente_db = await self._client.databases.retrieve(
            {"database_id": str(at_cfg.notion_database_id)}
        )

        contato_ds_id: Optional[str] = (
            contato_db.data_sources[0]["id"]
            if getattr(contato_db, "data_sources", None)
            else None
        )
        departamento_ds_id: Optional[str] = (
            departamento_db.data_sources[0]["id"]
            if getattr(departamento_db, "data_sources", None)
            else None
        )
        atendente_ds_id: Optional[str] = (
            atendente_db.data_sources[0]["id"]
            if getattr(atendente_db, "data_sources", None)
            else None
        )
        mensagem_ds_id: Optional[str] = (
            mensagem_db.data_sources[0]["id"]
            if getattr(mensagem_db, "data_sources", None)
            else None
        )
        atendimento_ds_id: Optional[str] = (
            atendimento_db.data_sources[0]["id"]
            if getattr(atendimento_db, "data_sources", None)
            else None
        )

        if not all(
            [
                contato_ds_id,
                departamento_ds_id,
                atendente_ds_id,
                mensagem_ds_id,
                atendimento_ds_id,
            ]
        ):
            raise ValueError("Uma ou mais databases sem data_source")

        # Atualizar relações principais em Atendimentos
        update_atendimento: dict[str, Any] = {
            "properties": {
                "Contato": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": contato_ds_id,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Atendimentos Relacionados",
                        },
                    },
                },
                "Departamento": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": departamento_ds_id,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Atendimentos Relacionados",
                        },
                    },
                },
                "Atendente": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": atendente_ds_id,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Atendimentos Relacionados",
                        },
                    },
                },
                "Mensagens Relacionadas": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": mensagem_ds_id,
                        "single_property": {},
                        "dual_property": {
                            "synced_property_name": "Atendimento Relacionado",
                        },
                    },
                },
            }
        }

        await self._client.request(
            method="patch",
            path=f"data_sources/{atendimento_ds_id}",
            body=update_atendimento,
        )
        logger.info("Relações principais adicionadas em Atendimentos")

        # Auxiliar para obter ID de propriedade por nome
        def _prop_id(db_info: dict[str, Any], name: str) -> Optional[str]:
            try:
                for ds in db_info.get("data_sources") or []:
                    props_ds: dict[str, Any] = ds.get("properties", {})
                    prop_ds = props_ds.get(name)
                    if prop_ds:
                        pid = prop_ds.get("id")
                        return str(pid) if isinstance(pid, str) else None
                props_root: dict[str, Any] = db_info.get("properties", {})
                prop_root = props_root.get(name)
                if not prop_root:
                    return None
                pid = prop_root.get("id")
                return str(pid) if isinstance(pid, str) else None
            except Exception:
                return None

        # IDs em Atendimentos para configurar reversos
        atendimento_info = await self._client.request(
            method="get", path=f"databases/{atendimento_db.id}"
        )
        contato_prop_id = _prop_id(atendimento_info, "Contato")
        departamento_prop_id = _prop_id(atendimento_info, "Departamento")
        atendente_prop_id = _prop_id(atendimento_info, "Atendente")

        # Reversos em Contatos/Departamentos/Atendentes
        update_contato: dict[str, Any] = {
            "properties": {
                "Atendimentos Relacionados": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": atendimento_ds_id,
                        "single_property": {},
                        "dual_property": (
                            {"synced_property_id": contato_prop_id}
                            if contato_prop_id
                            else {
                                "synced_property_name": "Contato",
                            }
                        ),
                    },
                }
            }
        }
        await self._client.request(
            method="patch",
            path=f"data_sources/{contato_ds_id}",
            body=update_contato,
        )

        update_departamento: dict[str, Any] = {
            "properties": {
                "Atendimentos Relacionados": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": atendimento_ds_id,
                        "single_property": {},
                        "dual_property": (
                            {"synced_property_id": departamento_prop_id}
                            if departamento_prop_id
                            else {
                                "synced_property_name": "Departamento",
                            }
                        ),
                    },
                }
            }
        }
        await self._client.request(
            method="patch",
            path=f"data_sources/{departamento_ds_id}",
            body=update_departamento,
        )

        update_atendente: dict[str, Any] = {
            "properties": {
                "Atendimentos Relacionados": {
                    "type": "relation",
                    "relation": {
                        "data_source_id": atendimento_ds_id,
                        "single_property": {},
                        "dual_property": (
                            {"synced_property_id": atendente_prop_id}
                            if atendente_prop_id
                            else {
                                "synced_property_name": "Atendente",
                            }
                        ),
                    },
                }
            }
        }
        await self._client.request(
            method="patch",
            path=f"data_sources/{atendente_ds_id}",
            body=update_atendente,
        )
        logger.info(
            "Relações reversas adicionadas em Contatos, Departamentos e Atendentes"
        )

    @sync_to_async
    def _save_configs(self, atendimento_db: Any, mensagem_db: Any) -> None:
        """Persiste configurações em `NotionDatabaseConfig`."""
        atendimento_ds = (
            atendimento_db.data_sources[0]["id"]
            if getattr(atendimento_db, "data_sources", None)
            else None
        )
        mensagem_ds = (
            mensagem_db.data_sources[0]["id"]
            if getattr(mensagem_db, "data_sources", None)
            else None
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_atendimentos_atendimento",
            defaults={
                "name": "🎯 Atendimentos CRM",
                "description": (
                    "Database para sincronização de atendimentos do sistema"
                ),
                "notion_database_id": atendimento_db.id,
                "data_source_id": atendimento_ds,
                "django_model": "ui.atendimentos.Atendimento",
                "django_app_label": "ui",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 8,
                "auto_sync": True,
            },
        )

        NotionDatabaseConfig.objects.update_or_create(
            slug="ui_atendimentos_mensagem",
            defaults={
                "name": "💬 Mensagens CRM",
                "description": (
                    "Database para sincronização de mensagens do sistema"
                ),
                "notion_database_id": mensagem_db.id,
                "data_source_id": mensagem_ds,
                "django_model": "ui.atendimentos.Mensagem",
                "django_app_label": "ui",
                "sync_enabled": True,
                "sync_direction": "bidirectional",
                "sync_priority": 9,
                "auto_sync": True,
            },
        )
        logger.info(
            "Configs de atendimentos/mensagens persistidas em NotionDatabaseConfig"
        )

    async def construct_minimal(self) -> None:
        """Orquestra criação e configuração mínima de atendimentos."""
        atendimento_db = await self._create_atendimento_database()
        mensagem_db = await self._create_mensagem_database(atendimento_db)
        await self._add_relations_to_atendimentos(mensagem_db, atendimento_db)
        await self._save_configs(atendimento_db, mensagem_db)
        logger.info("Bootstrap atendimentos concluído com sucesso")
