"""
Funções de setup para criar databases do Notion e persistir referências.

Este módulo cria/atualiza os databases "Contatos - CRM" e "Clientes - CRM"
no Notion, garantindo que as propriedades esperadas existam, e persiste
os IDs e schemas no model Django NotionDatabaseConfig. Opcionalmente,
salva os IDs no .env como backup.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from datetime import date
import asyncio

from decouple import config
from loguru import logger
from notion_py_client.notion_client import NotionAsyncClient, APIResponseError

from ..exceptions import SyncConfigError, NotionSyncError
from ..models import NotionDatabaseConfig
from ..services.mappers import ContatoMapper, ClienteMapper
from asgiref.sync import sync_to_async


def _find_project_root(start: Path) -> Path:
    """Tenta encontrar o root do projeto (com pyproject.toml)."""
    cur = start.resolve()
    for parent in [cur] + list(cur.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".env").exists():
            return parent
    return start.resolve().parents[4]  # fallback razoável para repos com /src


def _write_env_backup(updates: Dict[str, str]) -> None:
    """Atualiza ou cria variáveis no .env na raiz do projeto."""
    root = _find_project_root(Path(__file__))
    env_path = root / ".env"

    lines: list[str] = []
    existing: dict[str, str] = {}

    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                lines.append(line)
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                existing[k.strip()] = v
                # mantemos a linha por enquanto; vamos reescrever no final
        # reconstruir após merge

    # merge
    existing.update(updates)

    # reconstruir conteúdo mantendo comentários e linhas vazias no topo
    new_lines: list[str] = []
    seen_keys: set[str] = set()
    for line in lines:
        new_lines.append(line)
    for key, value in existing.items():
        if key in seen_keys:
            continue
        new_lines.append(f"{key}={value}")
        seen_keys.add(key)

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    logger.info("Backup de IDs do Notion gravado em .env")


async def _ensure_properties(client: NotionAsyncClient, database_id: str, target_schema: Dict[str, Any]) -> None:
    try:
        db = await client.databases.retrieve(params={"database_id": database_id})
        existing_props: Dict[str, Any] = (getattr(db, "properties", None) or {})

        existing_title_name: str | None = None
        for prop_name, prop_def in existing_props.items():
            if prop_def.get("type") == "title":
                existing_title_name = prop_name
                break

        desired_title_name: str | None = None
        for name, definition in target_schema.items():
            if "title" in definition:
                desired_title_name = name
                break

        if existing_title_name and desired_title_name and existing_title_name != desired_title_name:
            try:
                logger.info(
                    f"Renomeando propriedade de título '{existing_title_name}' para '{desired_title_name}' em {database_id[:8]}..."
                )
                await client.databases.update(
                    params={
                        "database_id": database_id,
                        "properties": {existing_title_name: {"name": desired_title_name}},
                    },
                )
                existing_props[desired_title_name] = existing_props.pop(existing_title_name)
                existing_title_name = desired_title_name
                logger.success(
                    f"✅ Título renomeado para '{desired_title_name}' em {database_id[:8]}..."
                )
            except APIResponseError as e:
                logger.warning(
                    f"⚠️ Falha ao renomear título: {e.code} - {str(e)}. Continuando com adição das outras propriedades."
                )

        missing: Dict[str, Any] = {}
        for name, definition in target_schema.items():
            if name in existing_props:
                continue
            if "title" in definition and existing_title_name:
                continue
            missing[name] = definition

        if not missing:
            logger.info(f"Propriedades já estão completas em {database_id[:8]}...")
            return

        added_count = 0
        for name, definition in missing.items():
            try:
                await client.databases.update(
                    params={
                        "database_id": database_id,
                        "properties": {name: definition},
                    },
                )
                added_count += 1
                logger.info(
                    f"➕ Propriedade adicionada: '{name}' em {database_id[:8]}..."
                )
            except APIResponseError as e:
                logger.error(
                    f"❌ Erro ao adicionar propriedade '{name}': {e.code} - {str(e)}"
                )
                continue

        if added_count:
            logger.success(
                f"✅ Propriedades atualizadas para {database_id[:8]}... ({added_count} adicionadas)"
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma propriedade foi adicionada em {database_id[:8]}... verifique permissões e schema."
            )

    except APIResponseError as e:
        err = str(e)
        logger.error(f"Erro ao garantir propriedades: {e.code} - {err}")
        raise NotionSyncError(
            message=f"Erro ao atualizar propriedades do database: {err}",
            status_code=e.status,
            notion_error=e.code,
            details={"database_id": database_id},
        ) from e


async def _force_materialize_by_dummy_page(client: NotionAsyncClient, database_id: str, target_schema: Dict[str, Any]) -> None:
    try:
        title_name = next((n for n, d in target_schema.items() if "title" in d), "Nome")
        props = {
            title_name: {
                "title": [{"type": "text", "text": {"content": "Materialize"}}]
            }
        }

        page = await client.pages.create(
            parent={"type": "database_id", "database_id": database_id},
            properties=props,
        )
        logger.info(f"Criada página temporária para materialização: {page.get('id', '')[:8]}...")
        try:
            await client.pages.update(page_id=page["id"], archived=True)
            logger.info("Página temporária arquivada.")
        except Exception:
            logger.warning("Falha ao arquivar página temporária; prosseguindo.")
    except APIResponseError as e:
        logger.warning(f"Falha ao criar página temporária: {e.code} - {str(e)}")
    except Exception as e:
        logger.warning(f"Falha genérica ao materializar propriedades: {str(e)}")


async def _ensure_and_materialize(client: NotionAsyncClient, database_id: str, target_schema: Dict[str, Any]) -> None:
    await _ensure_properties(client, database_id, target_schema)
    try:
        db_after = await client.databases.retrieve(params={"database_id": database_id})
        props_after = (getattr(db_after, "properties", None) or {})
        expected = len(target_schema)
        current = len(props_after)
        if current < expected:
            logger.warning(
                f"Propriedades visíveis ({current}) abaixo do esperado ({expected}). Forçando materialização via página..."
            )
            await _force_materialize_by_dummy_page(client, database_id, target_schema)
            await _ensure_properties(client, database_id, target_schema)
            db_final = await client.databases.retrieve(params={"database_id": database_id})
            final_count = len(getattr(db_final, "properties", None) or {})
            if final_count >= expected:
                logger.success("Propriedades materializadas e visíveis no Notion.")
            else:
                logger.warning(
                    f"Ainda abaixo do esperado ({final_count}/{expected}). Verifique manualmente no Notion."
                )
    except Exception as e:
        logger.warning(f"Falha ao revalidar propriedades após materialização: {str(e)}")


async def _create_or_get_database(
    client: NotionAsyncClient,
    page_id: str,
    title_text: str,
    properties_schema: Dict[str, Any],
) -> str:
    try:
        logger.info(f"Criando database '{title_text}' no Notion...")
        response = await client.databases.create(
            params={
                "parent": {"type": "page_id", "page_id": page_id},
                "title": [{"type": "text", "text": {"content": title_text}}],
                "properties": properties_schema,
            },
        )
        db_id = response["id"]
        logger.success(f"✅ Database criado: {title_text} ({db_id[:8]}...)")
        await _ensure_and_materialize(client, db_id, properties_schema)
        return db_id

    except APIResponseError as e:
        logger.warning(
            f"Falha ao criar com propriedades ({e.code}). Tentando criação mínima..."
        )
        try:
            minimal = await client.databases.create(
                params={
                    "parent": {"type": "page_id", "page_id": page_id},
                    "title": [{"type": "text", "text": {"content": title_text}}],
                    "properties": {"Título": {"title": {}}},
                },
            )
            db_id = minimal["id"]
            logger.success(
                f"✅ Database criado minimamente: {title_text} ({db_id[:8]}...), completando propriedades"
            )
            await _ensure_and_materialize(client, db_id, properties_schema)
            return db_id
        except APIResponseError as e2:
            err2 = str(e2)
            logger.error(
                f"❌ Erro ao criar database '{title_text}': {e2.code} - {err2}"
            )
            raise NotionSyncError(
                message=f"Erro ao criar database no Notion: {err2}",
                status_code=e2.status,
                notion_error=e2.code,
                details={"title": title_text},
            ) from e2


async def _ensure_relation_property(client: NotionAsyncClient, database_id: str, prop_name: str, related_database_id: str) -> None:
    try:
        db = await client.databases.retrieve(params={"database_id": database_id})
        existing_props: Dict[str, Any] = (getattr(db, "properties", None) or {})
        need_update = False

        if prop_name in existing_props:
            prop_def = existing_props[prop_name]
            if prop_def.get("type") != "relation":
                need_update = True
            else:
                rel = prop_def.get("relation", {})
                if rel.get("database_id") != related_database_id:
                    need_update = True
        else:
            need_update = True

        if need_update:
            logger.info(
                f"Configurando relação '{prop_name}' → {related_database_id[:8]}... em {database_id[:8]}..."
            )
            await client.databases.update(
                params={
                    "database_id": database_id,
                    "properties": {prop_name: {"relation": {"database_id": related_database_id}}},
                },
            )
            logger.success(
                f"✅ Relação '{prop_name}' garantida em {database_id[:8]}..."
            )
        else:
            logger.info(
                f"Relação '{prop_name}' já configurada em {database_id[:8]}..."
            )
    except APIResponseError as e:
        logger.error(
            f"❌ Erro ao configurar relação '{prop_name}': {e.code} - {str(e)}"
        )
        raise NotionSyncError(
            message=f"Erro ao configurar relação '{prop_name}': {str(e)}",
            status_code=e.status,
            notion_error=e.code,
            details={"database_id": database_id, "related_database_id": related_database_id},
        ) from e


async def _ensure_relation_between_databases(client: NotionAsyncClient, contatos_db_id: str, clientes_db_id: str) -> None:
    await _ensure_relation_property(client, clientes_db_id, "Contatos", contatos_db_id)
    await _ensure_relation_property(client, contatos_db_id, "Cliente", clientes_db_id)


async def setup_notion_databases_async() -> dict[str, Any]:
    token = config("NOTION_TOKEN", default=None)
    if not token:
        raise SyncConfigError(
            message="NOTION_TOKEN não configurado no .env",
            config_key="NOTION_TOKEN",
        )

    contatos_env_id = config("NOTION_SOURCE_CONTATOS_ID", default=None)
    clientes_env_id = config("NOTION_SOURCE_CLIENTES_ID", default=None)

    page_id = config("NOTION_PAGE_ID", default=None)
    if not page_id and not (contatos_env_id or clientes_env_id):
        raise SyncConfigError(
            message="NOTION_PAGE_ID não configurado no .env (necessário apenas para criar databases)",
            config_key="NOTION_PAGE_ID",
        )

    client = NotionAsyncClient(auth=token)

    contato_schema = ContatoMapper.get_database_schema()
    cliente_schema = ClienteMapper.get_database_schema()

    results: dict[str, Any] = {
        "contato": {},
        "cliente": {},
    }

    try:
        existing_contato_id = await sync_to_async(NotionDatabaseConfig.get_database_id)("Contato")
        if existing_contato_id:
            logger.info(
                f"Database de Contatos já configurado: {existing_contato_id[:8]}..."
            )
            await _ensure_and_materialize(client, existing_contato_id, contato_schema)
            await sync_to_async(NotionDatabaseConfig.set_database)(
                model_name="Contato",
                database_id=existing_contato_id,
                database_name="Contatos - CRM",
                properties_schema=contato_schema,
            )
            results["contato"] = {
                "database_id": existing_contato_id,
                "created": False,
                "updated": True,
            }
        elif contatos_env_id:
            logger.info(
                f"Usando NOTION_SOURCE_CONTATOS_ID do .env: {contatos_env_id[:8]}..."
            )
            await _ensure_and_materialize(client, contatos_env_id, contato_schema)
            await sync_to_async(NotionDatabaseConfig.set_database)(
                model_name="Contato",
                database_id=contatos_env_id,
                database_name="Contatos - CRM",
                properties_schema=contato_schema,
            )
            results["contato"] = {
                "database_id": contatos_env_id,
                "created": False,
                "updated": True,
            }
        else:
            contato_id = await _create_or_get_database(
                client=client,
                page_id=page_id,
                title_text="Contatos - CRM",
                properties_schema=contato_schema,
            )
            await sync_to_async(NotionDatabaseConfig.set_database)(
                model_name="Contato",
                database_id=contato_id,
                database_name="Contatos - CRM",
                properties_schema=contato_schema,
            )
            results["contato"] = {
                "database_id": contato_id,
                "created": True,
                "updated": False,
            }
    except (SyncConfigError, NotionSyncError) as e:
        raise
    except Exception as e:
        raise NotionSyncError(
            message=f"Erro ao configurar database de Contatos: {str(e)}",
            details={"stage": "contatos"},
        ) from e

    try:
        existing_cliente_id = await sync_to_async(NotionDatabaseConfig.get_database_id)("Cliente")
        if existing_cliente_id:
            logger.info(
                f"Database de Clientes já configurado: {existing_cliente_id[:8]}..."
            )
            await _ensure_and_materialize(client, existing_cliente_id, cliente_schema)
            await sync_to_async(NotionDatabaseConfig.set_database)(
                model_name="Cliente",
                database_id=existing_cliente_id,
                database_name="Clientes - CRM",
                properties_schema=cliente_schema,
            )
            results["cliente"] = {
                "database_id": existing_cliente_id,
                "created": False,
                "updated": True,
            }
        elif clientes_env_id:
            logger.info(
                f"Usando NOTION_SOURCE_CLIENTES_ID do .env: {clientes_env_id[:8]}..."
            )
            await _ensure_and_materialize(client, clientes_env_id, cliente_schema)
            await sync_to_async(NotionDatabaseConfig.set_database)(
                model_name="Cliente",
                database_id=clientes_env_id,
                database_name="Clientes - CRM",
                properties_schema=cliente_schema,
            )
            results["cliente"] = {
                "database_id": clientes_env_id,
                "created": False,
                "updated": True,
            }
        else:
            cliente_id = await _create_or_get_database(
                client=client,
                page_id=page_id,
                title_text="Clientes - CRM",
                properties_schema=cliente_schema,
            )
            await sync_to_async(NotionDatabaseConfig.set_database)(
                model_name="Cliente",
                database_id=cliente_id,
                database_name="Clientes - CRM",
                properties_schema=cliente_schema,
            )
            results["cliente"] = {
                "database_id": cliente_id,
                "created": True,
                "updated": False,
            }
    except (SyncConfigError, NotionSyncError) as e:
        raise
    except Exception as e:
        raise NotionSyncError(
            message=f"Erro ao configurar database de Clientes: {str(e)}",
            details={"stage": "clientes"},
        ) from e

    try:
        contato_id = results.get("contato", {}).get("database_id")
        cliente_id = results.get("cliente", {}).get("database_id")
        if contato_id and cliente_id:
            await _ensure_relation_between_databases(client, contato_id, cliente_id)
    except Exception as e:
        logger.warning(f"Falha ao configurar relação entre databases: {str(e)}")

    logger.success("✅ Setup dos databases do Notion concluído!")
    return results


def setup_notion_databases() -> dict[str, Any]:
    return asyncio.run(setup_notion_databases_async())
