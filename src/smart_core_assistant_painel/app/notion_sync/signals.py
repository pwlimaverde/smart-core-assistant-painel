"""
Signals para sincronização automática de models com plataformas externas.

Este módulo contém os signal receivers que capturam mudanças nos models
principais (Cliente, Contato) e disparam o processo de sincronização
com plataformas externas (Notion, Airtable, etc).
"""

from typing import Any

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from loguru import logger

from ..ui.clientes.models import Cliente, Contato
from .exceptions import NotionSyncError, SyncConfigError, SyncError
from .models import ClienteSync, ContatoSync, SyncLog
from .services import NotionSyncService


def get_or_create_contato_sync(contato_id: int) -> ContatoSync:
    """
    Obtém ou cria registro ContatoSync para um contato.

    Esta é uma função auxiliar que será usada pelos signals
    quando forem reabilitados.

    Args:
        contato_id: ID do contato no Django.

    Returns:
        Instância do ContatoSync.
    """
    from .models import ContatoSync, NotionDatabaseConfig

    # Obter configuração do Notion para Contatos
    config = NotionDatabaseConfig.objects.get(slug="ui_clientes_contato")

    sync, created = ContatoSync.objects.get_or_create(
        contato_id=contato_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config
        }
    )
    return sync


def get_or_create_cliente_sync(cliente_id: int) -> ClienteSync:
    """
    Obtém ou cria registro ClienteSync para um cliente.

    Esta é uma função auxiliar que será usada pelos signals
    quando forem reabilitados.

    Args:
        cliente_id: ID do cliente no Django.

    Returns:
        Instância do ClienteSync.
    """
    from .models import ClienteSync, NotionDatabaseConfig

    # Obter configuração do Notion para Clientes
    config = NotionDatabaseConfig.objects.get(slug="ui_clientes_cliente")

    sync, created = ClienteSync.objects.get_or_create(
        cliente_id=cliente_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config
        }
    )
    return sync


def schedule_sync_operation(
    model_name: str,
    instance_id: int,
    operation: str
) -> None:
    """
    Agenda uma operação de sincronização.

    Esta função centraliza a lógica de agendamento de sincronizações
    e será usada pelos signals quando forem reabilitados.

    Args:
        model_name: Nome do modelo (ex: "Contato", "Cliente").
        instance_id: ID da instância.
        operation: Tipo de operação ("create", "update", "delete").
    """
    from .services import NotionSyncService
    from .models import ContatoSync, ClienteSync

    try:
        service = NotionSyncService()

        # Obter o registro sync correspondente
        if model_name == "Contato":
            sync_record = ContatoSync.objects.get(contato_id=instance_id)
        elif model_name == "Cliente":
            sync_record = ClienteSync.objects.get(cliente_id=instance_id)
        else:
            logger.warning(f"Modelo não suportado: {model_name}")
            return

        # Para simplificar, executamos sincronização síncrona por enquanto
        # Em produção, isso deve ser assíncrono (Celery, Django Q, etc)
        logger.info(f"Executando sincronização: {model_name} #{instance_id} - {operation}")
        logger.debug(f"Sync record: {sync_record}")

        if operation == "create":
            external_id = service.create_record(model_name, instance_id, sync_record)
            sync_record.mark_as_synced(external_id)

        elif operation == "update":
            if sync_record.external_id:
                success = service.update_record(model_name, sync_record.external_id, instance_id, sync_record)
                if success:
                    sync_record.mark_as_synced()
                else:
                    sync_record.mark_as_failed("Falha na atualização")
            else:
                # Se não tem external_id, tenta criar
                external_id = service.create_record(model_name, instance_id, sync_record)
                sync_record.external_id = external_id
                sync_record.sync_status = "synced"
                sync_record.mark_as_synced()
        elif operation == "delete":
            if sync_record.external_id:
                service.delete_record(model_name, sync_record.external_id)

        logger.info(f"Sincronização executada com sucesso: {model_name} #{instance_id} - {operation}")

    except Exception as e:
        logger.error(f"Erro ao executar sincronização: {e}")
        logger.exception("Stack trace completo do erro:")
        # Tentar marcar como falha se tiver o sync_record
        try:
            if model_name == "Contato":
                sync_record = ContatoSync.objects.get(contato_id=instance_id)
            elif model_name == "Cliente":
                sync_record = ClienteSync.objects.get(cliente_id=instance_id)
            logger.info(f"Marcando sync_record como falha: {model_name} #{instance_id}")
            sync_record.mark_as_failed(str(e))
        except Exception as mark_error:
            logger.error(f"Erro ao marcar como falha: {mark_error}")
            logger.exception("Stack trace do erro de marcação:")


@receiver(post_save, sender=Contato)
def on_contato_saved(
    sender: Any,
    instance: "Contato",
    created: bool,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar Contato quando salvo.

    Este receiver é disparado sempre que um Contato é criado ou
    atualizado. Ele:
    1. Cria ou obtém o registro de tracking (ContatoSync)
    2. Prepara os dados para sincronização
    3. Agenda a sincronização assíncrona

    Args:
        sender: Classe do model que enviou o signal (Contato).
        instance: Instância do Contato que foi salva.
        created: True se o registro foi criado, False se atualizado.
        **kwargs: Argumentos adicionais do signal.
    """
    # Verifica se existe flag para ignorar sincronização
    if kwargs.get("skip_sync", False):
        logger.debug(f"Sincronização ignorada para Contato #{instance.id}")
        return

    try:
        # Obtém ou cria o registro de tracking
        sync_metadata = get_or_create_contato_sync(instance.id)

        operation = "create" if created else "update"

        # Prepara os dados para sincronização
        sync_metadata.prepare_notion_data()
        sync_metadata.save()

        # Agenda sincronização assíncrona
        schedule_sync_operation(
            model_name="Contato",
            instance_id=instance.id,
            operation=operation
        )

        logger.info(
            f"Contato #{instance.id} {'criado' if created else 'atualizado'}"
            f" - Sincronização agendada"
        )

    except Exception as e:
        logger.error(f"Erro ao processar signal de Contato #{instance.id}: {e}")


@receiver(post_save, sender=Cliente)
def on_cliente_saved(
    sender: Any,
    instance: "Cliente",
    created: bool,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar Cliente quando salvo.

    Este receiver é disparado sempre que um Cliente é criado ou
    atualizado. Ele:
    1. Cria ou obtém o registro de tracking (ClienteSync)
    2. Prepara os dados para sincronização
    3. Agenda a sincronização assíncrona

    Args:
        sender: Classe do model que enviou o signal (Cliente).
        instance: Instância do Cliente que foi salva.
        created: True se o registro foi criado, False se atualizado.
        **kwargs: Argumentos adicionais do signal.
    """
    # Verifica se existe flag para ignorar sincronização
    if kwargs.get("skip_sync", False):
        logger.debug(f"Sincronização ignorada para Cliente #{instance.id}")
        return

    try:
        # Obtém ou cria o registro de tracking
        sync_metadata = get_or_create_cliente_sync(instance.id)

        operation = "create" if created else "update"

        # Prepara os dados para sincronização
        sync_metadata.prepare_notion_data()
        sync_metadata.save()

        # Agenda sincronização assíncrona
        schedule_sync_operation(
            model_name="Cliente",
            instance_id=instance.id,
            operation=operation
        )

        logger.info(
            f"Cliente #{instance.id} {'criado' if created else 'atualizado'}"
            f" - Sincronização agendada"
        )

    except Exception as e:
        logger.error(f"Erro ao processar signal de Cliente #{instance.id}: {e}")


@receiver(post_delete, sender=Contato)
def on_contato_deleted(
    sender: Any,
    instance: "Contato",
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Contato.

    Este receiver é disparado quando um Contato é deletado.
    Ele agenda a sincronização de deleção para as plataformas externas.

    Args:
        sender: Classe do model que enviou o signal (Contato).
        instance: Instância do Contato que foi deletada.
        **kwargs: Argumentos adicionais do signal.
    """
    try:
        # Agenda sincronização de deleção
        schedule_sync_operation(
            model_name="Contato",
            instance_id=instance.id,
            operation="delete"
        )

        logger.info(f"Contato #{instance.id} deletado - Sincronização agendada")

    except Exception as e:
        logger.error(f"Erro ao processar deleção de Contato #{instance.id}: {e}")


@receiver(post_delete, sender=Cliente)
def on_cliente_deleted(
    sender: Any,
    instance: "Cliente",
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Cliente.

    Este receiver é disparado quando um Cliente é deletado.
    Ele agenda a sincronização de deleção para as plataformas externas.

    Args:
        sender: Classe do model que enviou o signal (Cliente).
        instance: Instância do Cliente que foi deletada.
        **kwargs: Argumentos adicionais do signal.
    """
    try:
        # Agenda sincronização de deleção
        schedule_sync_operation(
            model_name="Cliente",
            instance_id=instance.id,
            operation="delete"
        )

        logger.info(f"Cliente #{instance.id} deletado - Sincronização agendada")

    except Exception as e:
        logger.error(f"Erro ao processar deleção de Cliente #{instance.id}: {e}")
