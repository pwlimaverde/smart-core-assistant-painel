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

from decouple import config
from loguru import logger
from notion_py_client import Client
from notion_py_client.errors import APIResponseError

from ..exceptions import SyncConfigError, NotionSyncError
from ..models import NotionDatabaseConfig
from ..services.mappers import ContatoMapper, ClienteMapper


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


def _ensure_properties(client: Client, database_id: str, target_schema: Dict[str, Any]) -> None:
    """Garante que todas as propriedades de target_schema existam no database.

    - Trata propriedade de título (só pode existir uma) renomeando a existente
      para o nome desejado, em vez de tentar adicionar uma nova.
    - Adiciona demais propriedades de forma incremental para evitar que uma
      falha bloqueie todas as outras.
    """
    try:
        db = client.databases.retrieve(database_id=database_id)
        existing_props: Dict[str, Any] = db.get("properties", {})

        # Descobre nomes de título (existente e desejado)
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

        # Renomeia o título, se necessário
        if existing_title_name and desired_title_name and existing_title_name != desired_title_name:
            try:
                logger.info(
                    f"Renomeando propriedade de título '{existing_title_name}' para '{desired_title_name}' em {database_id[:8]}..."
                )
                client.databases.update(
                    database_id=database_id,
                    properties={existing_title_name: {"name": desired_title_name}},
                )
                # Atualiza cache local
                existing_props[desired_title_name] = existing_props.pop(existing_title_name)
                existing_title_name = desired_title_name
                logger.success(
                    f"✅ Título renomeado para '{desired_title_name}' em {database_id[:8]}..."
                )
            except APIResponseError as e:
                logger.warning(
                    f"⚠️ Falha ao renomear título: {e.code} - {str(e)}. Continuando com adição das outras propriedades."
                )

        # Calcula propriedades faltantes (ignorando título se já existe)
        missing: Dict[str, Any] = {}
        for name, definition in target_schema.items():
            if name in existing_props:
                continue
            # Evita tentar adicionar uma segunda propriedade de título
            if "title" in definition and existing_title_name:
                continue
            missing[name] = definition

        if not missing:
            logger.info(f"Propriedades já estão completas em {database_id[:8]}...")
            return

        # Adiciona propriedades uma a uma para maior resiliência
        added_count = 0
        for name, definition in missing.items():
            try:
                client.databases.update(
                    database_id=database_id,
                    properties={name: definition},
                )
                added_count += 1
                logger.info(
                    f"➕ Propriedade adicionada: '{name}' em {database_id[:8]}..."
                )
            except APIResponseError as e:
                logger.error(
                    f"❌ Erro ao adicionar propriedade '{name}': {e.code} - {str(e)}"
                )
                # Continua tentando as demais propriedades
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


def _force_materialize_by_dummy_page(client: Client, database_id: str, target_schema: Dict[str, Any]) -> None:
    """Cria uma página temporária com apenas o título para materializar colunas.

    Alguns workspaces não mostram propriedades adicionadas via API em databases
    inline enquanto não há páginas. Para evitar erros de validação, definimos
    apenas o título na criação da página temporária e depois garantimos as
    propriedades novamente.
    """
    try:
        # Define somente o título
        title_name = next((n for n, d in target_schema.items() if "title" in d), "Nome")
        props = {
            title_name: {
                "title": [{"type": "text", "text": {"content": "Materialize"}}]
            }
        }

        page = client.pages.create(
            parent={"type": "database_id", "database_id": database_id},
            properties=props,
        )
        logger.info(f"Criada página temporária para materialização: {page.get('id', '')[:8]}...")
        # Arquiva a página para não sujar o database
        try:
            client.pages.update(page_id=page["id"], archived=True)
            logger.info("Página temporária arquivada.")
        except Exception:
            logger.warning("Falha ao arquivar página temporária; prosseguindo.")
    except APIResponseError as e:
        logger.warning(f"Falha ao criar página temporária: {e.code} - {str(e)}")
    except Exception as e:
        logger.warning(f"Falha genérica ao materializar propriedades: {str(e)}")


def _ensure_and_materialize(client: Client, database_id: str, target_schema: Dict[str, Any]) -> None:
    """Garante propriedades e força materialização se contagem estiver abaixo do esperado."""
    _ensure_properties(client, database_id, target_schema)
    try:
        db_after = client.databases.retrieve(database_id=database_id)
        props_after = db_after.get("properties", {})
        expected = len(target_schema)
        current = len(props_after)
        if current < expected:
            logger.warning(
                f"Propriedades visíveis ({current}) abaixo do esperado ({expected}). Forçando materialização via página..."
            )
            _force_materialize_by_dummy_page(client, database_id, target_schema)
            # garante novamente após existir ao menos uma página
            _ensure_properties(client, database_id, target_schema)
            # nova checagem
            db_final = client.databases.retrieve(database_id=database_id)
            final_count = len(db_final.get("properties", {}))
            if final_count >= expected:
                logger.success("Propriedades materializadas e visíveis no Notion.")
            else:
                logger.warning(
                    f"Ainda abaixo do esperado ({final_count}/{expected}). Verifique manualmente no Notion."
                )
    except Exception as e:
        logger.warning(f"Falha ao revalidar propriedades após materialização: {str(e)}")


def _create_or_get_database(
    client: Client,
    page_id: str,
    title_text: str,
    properties_schema: Dict[str, Any],
) -> str:
    """Cria o database no Notion sob page_id ou retorna existente.

    Tenta criar com propriedades; se a API recusar a criação de certas
    propriedades, cria minimalmente e depois completa via update.
    """
    try:
        # Criação direta com propriedades
        logger.info(f"Criando database '{title_text}' no Notion...")
        response = client.databases.create(
            parent={"type": "page_id", "page_id": page_id},
            title=[{"type": "text", "text": {"content": title_text}}],
            properties=properties_schema,
        )
        db_id = response["id"]
        logger.success(f"✅ Database criado: {title_text} ({db_id[:8]}...)")
        # Garante e materializa
        _ensure_and_materialize(client, db_id, properties_schema)
        return db_id

    except APIResponseError as e:
        msg = str(e)
        # Alguns workspaces permitem criar apenas com título; então criamos mínimo
        logger.warning(
            f"Falha ao criar com propriedades ({e.code}). Tentando criação mínima..."
        )
        try:
            minimal = client.databases.create(
                parent={"type": "page_id", "page_id": page_id},
                title=[{"type": "text", "text": {"content": title_text}}],
                properties={"Título": {"title": {}}},
            )
            db_id = minimal["id"]
            logger.success(
                f"✅ Database criado minimamente: {title_text} ({db_id[:8]}...), completando propriedades"
            )
            # completa propriedades faltantes + materialização
            _ensure_and_materialize(client, db_id, properties_schema)
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


def setup_notion_databases() -> dict[str, Any]:
    """
    Cria/valida os databases de Contatos e Clientes no Notion e persiste no Django.

    - Lê `NOTION_TOKEN` e `NOTION_PAGE_ID`
    - Cria ou atualiza os databases "Contatos - CRM" e "Clientes - CRM"
    - Garante propriedades via mappers
    - Persiste em `NotionDatabaseConfig`
    - IDs são persistidos apenas no Django (NotionDatabaseConfig)

    Returns:
        Resumo da operação com IDs e flags de criação/atualização.
    """
    token = config("NOTION_TOKEN", default=None)
    if not token:
        raise SyncConfigError(
            message="NOTION_TOKEN não configurado no .env",
            config_key="NOTION_TOKEN",
        )

    # IDs de databases existentes via .env (opcional)
    contatos_env_id = config("NOTION_SOURCE_CONTATOS_ID", default=None)
    clientes_env_id = config("NOTION_SOURCE_CLIENTES_ID", default=None)

    # PAGE_ID só é necessário quando precisamos criar um novo database
    page_id = config("NOTION_PAGE_ID", default=None)
    if not page_id and not (contatos_env_id or clientes_env_id):
        raise SyncConfigError(
            message="NOTION_PAGE_ID não configurado no .env (necessário apenas para criar databases)",
            config_key="NOTION_PAGE_ID",
        )

    client = Client(auth=token)

    # Schemas pelas classes mapper
    contato_schema = ContatoMapper.get_database_schema()
    cliente_schema = ClienteMapper.get_database_schema()

    results: dict[str, Any] = {
        "contato": {},
        "cliente": {},
    }

    # Contatos
    try:
        existing_contato_id = NotionDatabaseConfig.get_database_id("Contato")
        if existing_contato_id:
            logger.info(
                f"Database de Contatos já configurado: {existing_contato_id[:8]}..."
            )
            _ensure_and_materialize(client, existing_contato_id, contato_schema)
            NotionDatabaseConfig.set_database(
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
            _ensure_and_materialize(client, contatos_env_id, contato_schema)
            NotionDatabaseConfig.set_database(
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
            contato_id = _create_or_get_database(
                client=client,
                page_id=page_id,
                title_text="Contatos - CRM",
                properties_schema=contato_schema,
            )
            NotionDatabaseConfig.set_database(
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

    # Clientes
    try:
        existing_cliente_id = NotionDatabaseConfig.get_database_id("Cliente")
        if existing_cliente_id:
            logger.info(
                f"Database de Clientes já configurado: {existing_cliente_id[:8]}..."
            )
            _ensure_and_materialize(client, existing_cliente_id, cliente_schema)
            NotionDatabaseConfig.set_database(
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
            _ensure_and_materialize(client, clientes_env_id, cliente_schema)
            NotionDatabaseConfig.set_database(
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
            cliente_id = _create_or_get_database(
                client=client,
                page_id=page_id,
                title_text="Clientes - CRM",
                properties_schema=cliente_schema,
            )
            NotionDatabaseConfig.set_database(
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

    logger.success("✅ Setup dos databases do Notion concluído!")
    return results
