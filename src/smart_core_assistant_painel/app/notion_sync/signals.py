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


@receiver(post_save, sender=Contato)
def on_contato_saved(
    sender: Any,
    instance: Contato,
    created: bool,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar Contato quando salvo.

    Este receiver é disparado sempre que um Contato é criado ou
    atualizado. Ele:
    1. Cria ou obtém o registro de tracking (ContatoSync)
    2. Marca o contato para sincronização
    3. Registra a operação nos logs

    Args:
        sender: Classe do model que enviou o signal (Contato).
        instance: Instância do Contato que foi salva.
        created: True se o registro foi criado, False se atualizado.
        **kwargs: Argumentos adicionais do signal.
    """
    # Verifica se existe flag para ignorar sincronização
    # (usado para evitar loops quando atualizamos via webhook)
    if kwargs.get("skip_sync", False):
        logger.debug(
            f"Sincronização ignorada para Contato #{instance.id} "
            f"(flag skip_sync=True)"
        )
        return

    try:
        # Obtém ou cria o registro de tracking
        sync_metadata, sync_created = ContatoSync.objects.get_or_create(
            contato=instance
        )

        operation = "create" if created else "update"

        # Log da operação
        logger.info(
            f"Contato #{instance.id} {'criado' if created else 'atualizado'}"
            f" - Preparando para sincronização"
        )

        # Marca como não sincronizado para disparar sincronização
        sync_metadata.is_synced = False
        sync_metadata.save()

        # Registra no log de sincronização
        SyncLog.log_operation(
            model_name="Contato",
            django_id=instance.id,
            external_id=sync_metadata.external_id,
            operation=operation,
            direction="django_to_external",
            status="pending",
        )

        # Sincroniza com o Notion (síncrono por enquanto)
        # TODO: Migrar para Celery Task assíncrono
        try:
            service = NotionSyncService()
            page_id = service.create_record(
                model_name="Contato",
                django_id=instance.id,
                data=instance  # Passa a instância completa
            )

            # Marca como sincronizado com sucesso
            sync_metadata.mark_as_synced(external_id=page_id)

            # Atualiza log para success
            SyncLog.log_operation(
                model_name="Contato",
                django_id=instance.id,
                external_id=page_id,
                operation=operation,
                direction="django_to_external",
                status="success",
            )

            logger.success(
                f"✅ Contato #{instance.id} sincronizado com Notion: {page_id}"
            )

        except (NotionSyncError, SyncConfigError, SyncError) as e:
            # Marca como falha
            sync_metadata.mark_as_failed(error_message=str(e))

            # Atualiza log para error
            SyncLog.log_operation(
                model_name="Contato",
                django_id=instance.id,
                external_id=sync_metadata.external_id,
                operation=operation,
                direction="django_to_external",
                status="error",
                error_message=str(e),
                error_details=e.details if hasattr(e, 'details') else {}
            )

            logger.error(
                f"❌ Erro ao sincronizar Contato #{instance.id}: {e}"
            )

    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Contato #{instance.id}: {e}"
        )
        # Registra erro no log
        SyncLog.log_operation(
            model_name="Contato",
            django_id=instance.id,
            external_id=None,
            operation="create" if created else "update",
            direction="django_to_external",
            status="error",
            error_message=str(e),
        )


@receiver(post_delete, sender=Contato)
def on_contato_deleted(
    sender: Any,
    instance: Contato,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Contato.

    Este receiver é disparado quando um Contato é deletado. Ele:
    1. Verifica se existe registro de tracking
    2. Registra a operação de deleção
    3. Dispara sincronização para arquivar/deletar na plataforma externa

    Args:
        sender: Classe do model que enviou o signal (Contato).
        instance: Instância do Contato que foi deletada.
        **kwargs: Argumentos adicionais do signal.
    """
    # Verifica se existe flag para ignorar sincronização
    if kwargs.get("skip_sync", False):
        logger.debug(
            f"Sincronização de deleção ignorada para Contato #{instance.id}"
        )
        return

    try:
        # Verifica se existe tracking (o OneToOne já foi deletado)
        # Então precisamos buscar antes da deleção
        logger.info(
            f"Contato #{instance.id} deletado - "
            f"Preparando sincronização de deleção"
        )

        # Registra no log de sincronização
        SyncLog.log_operation(
            model_name="Contato",
            django_id=instance.id,
            external_id=None,
            operation="delete",
            direction="django_to_external",
            status="pending",
        )

        # Sincroniza deleção com o Notion (se tinha external_id)
        # TODO: Migrar para Celery Task assíncrono
        try:
            # Busca external_id antes que o tracking seja deletado
            from .models import ContatoSync
            try:
                sync_meta = ContatoSync.objects.get(contato=instance)
                external_id = sync_meta.external_id

                if external_id:
                    service = NotionSyncService()
                    service.delete_record(
                        model_name="Contato",
                        external_id=external_id
                    )

                    logger.success(
                        f"✅ Contato #{instance.id} arquivado no Notion"
                    )
            except ContatoSync.DoesNotExist:
                logger.debug(f"Contato #{instance.id} não tinha tracking")

        except Exception as e:
            logger.error(
                f"❌ Erro ao arquivar Contato #{instance.id} no Notion: {e}"
            )

    except Exception as e:
        logger.error(
            f"Erro ao processar deleção de Contato #{instance.id}: {e}"
        )


@receiver(post_save, sender=Cliente)
def on_cliente_saved(
    sender: Any,
    instance: Cliente,
    created: bool,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar Cliente quando salvo.

    Este receiver é disparado sempre que um Cliente é criado ou
    atualizado. Ele:
    1. Cria ou obtém o registro de tracking (ClienteSync)
    2. Marca o cliente para sincronização
    3. Registra a operação nos logs

    Args:
        sender: Classe do model que enviou o signal (Cliente).
        instance: Instância do Cliente que foi salva.
        created: True se o registro foi criado, False se atualizado.
        **kwargs: Argumentos adicionais do signal.
    """
    # Verifica se existe flag para ignorar sincronização
    if kwargs.get("skip_sync", False):
        logger.debug(
            f"Sincronização ignorada para Cliente #{instance.id} "
            f"(flag skip_sync=True)"
        )
        return

    try:
        # Obtém ou cria o registro de tracking
        sync_metadata, sync_created = ClienteSync.objects.get_or_create(
            cliente=instance
        )

        operation = "create" if created else "update"

        # Log da operação
        logger.info(
            f"Cliente #{instance.id} {'criado' if created else 'atualizado'}"
            f" - Preparando para sincronização"
        )

        # Marca como não sincronizado para disparar sincronização
        sync_metadata.is_synced = False
        sync_metadata.save()

        # Registra no log de sincronização
        SyncLog.log_operation(
            model_name="Cliente",
            django_id=instance.id,
            external_id=sync_metadata.external_id,
            operation=operation,
            direction="django_to_external",
            status="pending",
        )

        # Sincroniza com o Notion (síncrono por enquanto)
        # TODO: Migrar para Celery Task assíncrono
        try:
            service = NotionSyncService()
            page_id = service.create_record(
                model_name="Cliente",
                django_id=instance.id,
                data=instance  # Passa a instância completa
            )

            # Marca como sincronizado com sucesso
            sync_metadata.mark_as_synced(external_id=page_id)

            # Atualiza log para success
            SyncLog.log_operation(
                model_name="Cliente",
                django_id=instance.id,
                external_id=page_id,
                operation=operation,
                direction="django_to_external",
                status="success",
            )

            logger.success(
                f"✅ Cliente #{instance.id} sincronizado com Notion: {page_id}"
            )

        except (NotionSyncError, SyncConfigError, SyncError) as e:
            # Marca como falha
            sync_metadata.mark_as_failed(error_message=str(e))

            # Atualiza log para error
            SyncLog.log_operation(
                model_name="Cliente",
                django_id=instance.id,
                external_id=sync_metadata.external_id,
                operation=operation,
                direction="django_to_external",
                status="error",
                error_message=str(e),
                error_details=e.details if hasattr(e, 'details') else {}
            )

            logger.error(
                f"❌ Erro ao sincronizar Cliente #{instance.id}: {e}"
            )

    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Cliente #{instance.id}: {e}"
        )
        # Registra erro no log
        SyncLog.log_operation(
            model_name="Cliente",
            django_id=instance.id,
            external_id=None,
            operation="create" if created else "update",
            direction="django_to_external",
            status="error",
            error_message=str(e),
        )


@receiver(post_delete, sender=Cliente)
def on_cliente_deleted(
    sender: Any,
    instance: Cliente,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Cliente.

    Este receiver é disparado quando um Cliente é deletado. Ele:
    1. Verifica se existe registro de tracking
    2. Registra a operação de deleção
    3. Dispara sincronização para arquivar/deletar na plataforma externa

    Args:
        sender: Classe do model que enviou o signal (Cliente).
        instance: Instância do Cliente que foi deletada.
        **kwargs: Argumentos adicionais do signal.
    """
    # Verifica se existe flag para ignorar sincronização
    if kwargs.get("skip_sync", False):
        logger.debug(
            f"Sincronização de deleção ignorada para Cliente #{instance.id}"
        )
        return

    try:
        logger.info(
            f"Cliente #{instance.id} deletado - "
            f"Preparando sincronização de deleção"
        )

        # Registra no log de sincronização
        SyncLog.log_operation(
            model_name="Cliente",
            django_id=instance.id,
            external_id=None,
            operation="delete",
            direction="django_to_external",
            status="pending",
        )

        # Sincroniza deleção com o Notion (se tinha external_id)
        # TODO: Migrar para Celery Task assíncrono
        try:
            # Busca external_id antes que o tracking seja deletado
            from .models import ClienteSync
            try:
                sync_meta = ClienteSync.objects.get(cliente=instance)
                external_id = sync_meta.external_id

                if external_id:
                    service = NotionSyncService()
                    service.delete_record(
                        model_name="Cliente",
                        external_id=external_id
                    )

                    logger.success(
                        f"✅ Cliente #{instance.id} arquivado no Notion"
                    )
            except ClienteSync.DoesNotExist:
                logger.debug(f"Cliente #{instance.id} não tinha tracking")

        except Exception as e:
            logger.error(
                f"❌ Erro ao arquivar Cliente #{instance.id} no Notion: {e}"
            )

    except Exception as e:
        logger.error(
            f"Erro ao processar deleção de Cliente #{instance.id}: {e}"
        )
