"""
Script de reparo para garantir relacionamento bidirecional entre Contatos e Clientes no Notion.

Este script:
- Verifica se as databases do Notion estão configuradas (NotionDatabaseConfig)
- Recria páginas ausentes (sem `external_id`) tanto para Contatos quanto para Clientes
- Reenvia as propriedades (incluindo os campos `relation`) para atualizar o vínculo
- Gera estatísticas e logs do processo

Uso:
    python src/smart_core_assistant_painel/app/notion_sync/scripts/repair_bidirectional_relations.py
"""
import os
import sys
import logging
from typing import Any

from dotenv import load_dotenv

# Carregar variáveis de ambiente (NOTION_TOKEN/NOTION_PAGE_ID, etc.)
load_dotenv()

# Adicionar o path do projeto ao sys.path para importar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.ui.core.settings")
import django
django.setup()

from loguru import logger
from smart_core_assistant_painel.app.notion_sync.models import (
    NotionDatabaseConfig,
    ClienteSync,
    ContatoSync,
)
from smart_core_assistant_painel.app.notion_sync.services.notion_service import NotionSyncService


def _ensure_configs_ready() -> bool:
    """Confere se ambas as configs do Notion estão prontas para sincronização."""
    try:
        contato_cfg = NotionDatabaseConfig.objects.get(slug="ui_clientes_contato")
        cliente_cfg = NotionDatabaseConfig.objects.get(slug="ui_clientes_cliente")
        ready = contato_cfg.is_ready_for_sync() and cliente_cfg.is_ready_for_sync()
        if not ready:
            logger.error("Configurações do Notion não estão prontas para sync.")
            logger.error(
                f"Contatos ready={contato_cfg.is_ready_for_sync()} | Clientes ready={cliente_cfg.is_ready_for_sync()}"
            )
        else:
            logger.info("✅ Configurações do Notion conferidas: prontas para sincronização.")
        return ready
    except Exception as e:
        logger.error(f"❌ Erro ao validar configurações do Notion: {e}")
        return False


def _sync_contatos(service: NotionSyncService) -> dict[str, Any]:
    stats = {"total": 0, "created": 0, "updated": 0, "failed": 0}
    contatos = ContatoSync.objects.select_related("contato").all()
    stats["total"] = contatos.count()

    for sync in contatos:
        try:
            # Preparar dados
            sync.prepare_notion_data()
            sync.save()

            if not sync.external_id:
                page_id = service.create_record("Contato", sync.contato_id, sync)
                sync.external_id = page_id
                sync.mark_as_synced(page_id)
                stats["created"] += 1
                logger.info(f"👥 Contato #{sync.contato_id} criado no Notion: {page_id}")
            else:
                ok = service.update_record("Contato", sync.external_id, sync.contato_id, sync)
                if ok:
                    sync.mark_as_synced()
                    stats["updated"] += 1
                    logger.info(f"🔄 Contato #{sync.contato_id} atualizado no Notion")
                else:
                    sync.mark_as_failed("Falha na atualização")
                    stats["failed"] += 1
                    logger.error(f"❌ Falha ao atualizar Contato #{sync.contato_id}")
        except Exception as e:
            stats["failed"] += 1
            try:
                sync.mark_as_failed(str(e))
            except Exception:
                pass
            logger.error(f"❌ Erro ao sincronizar Contato #{getattr(sync, 'contato_id', '?')}: {e}")

    return stats


def _sync_clientes(service: NotionSyncService) -> dict[str, Any]:
    stats = {"total": 0, "created": 0, "updated": 0, "failed": 0}
    clientes = ClienteSync.objects.select_related("cliente").all()
    stats["total"] = clientes.count()

    for sync in clientes:
        try:
            # Preparar dados
            sync.prepare_notion_data()
            sync.save()

            if not sync.external_id:
                page_id = service.create_record("Cliente", sync.cliente_id, sync)
                sync.external_id = page_id
                sync.mark_as_synced(page_id)
                stats["created"] += 1
                logger.info(f"🏢 Cliente #{sync.cliente_id} criado no Notion: {page_id}")
            else:
                ok = service.update_record("Cliente", sync.external_id, sync.cliente_id, sync)
                if ok:
                    sync.mark_as_synced()
                    stats["updated"] += 1
                    logger.info(f"🔄 Cliente #{sync.cliente_id} atualizado no Notion")
                else:
                    sync.mark_as_failed("Falha na atualização")
                    stats["failed"] += 1
                    logger.error(f"❌ Falha ao atualizar Cliente #{sync.cliente_id}")
        except Exception as e:
            stats["failed"] += 1
            try:
                sync.mark_as_failed(str(e))
            except Exception:
                pass
            logger.error(f"❌ Erro ao sincronizar Cliente #{getattr(sync, 'cliente_id', '?')}: {e}")

    return stats


def main() -> None:
    logger.info("🚀 Iniciando reparo de relacionamento bidirecional Notion ↔ Django")

    if not _ensure_configs_ready():
        logger.error("Abortando: configs do Notion não prontas.")
        return

    service = NotionSyncService()

    # 1) Atualizar primeiro Contatos, depois Clientes para reforçar relação inversa
    c_stats = _sync_contatos(service)
    k_stats = _sync_clientes(service)

    logger.info("\n📊 Resultado do Reparo:")
    logger.info(f"   Contatos: total={c_stats['total']} created={c_stats['created']} updated={c_stats['updated']} failed={c_stats['failed']}")
    logger.info(f"   Clientes: total={k_stats['total']} created={k_stats['created']} updated={k_stats['updated']} failed={k_stats['failed']}")

    logger.info("✅ Reparo concluído.")


if __name__ == "__main__":
    main()