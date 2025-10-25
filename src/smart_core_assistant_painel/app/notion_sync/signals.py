"""
Signals para sincronização automática de models com plataformas externas.

Este módulo contém os signal receivers que capturam mudanças nos models
principais (Cliente, Contato) e disparam o processo de sincronização
com plataformas externas (Notion, Airtable, etc).
"""

from typing import Any

from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
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

        # Operações de delete são tratadas nos signals pre_delete
        # para evitar problemas com CASCADE do OneToOneField
        if operation == "delete":
            logger.warning(f"Operação de delete para {model_name} deve ser tratada em pre_delete signal")
            return

        # Obter o registro sync correspondente (para create/update)
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
                sync_record.mark_as_synced(external_id)
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


# Removido: on_contato_deleted - substituído por on_contato_pre_delete
# para evitar problemas com CASCADE do OneToOneField


# Usar pre_delete em vez de post_delete para capturar sync_record antes do CASCADE
@receiver(pre_delete, sender=Contato)
def on_contato_pre_delete(
    sender: Any,
    instance: "Contato",
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Contato.

    Este receiver é disparado ANTES de um Contato ser deletado
    para que possamos capturar o external_id antes do CASCADE.

    Args:
        sender: Classe do model que enviou o signal (Contato).
        instance: Instância do Contato que será deletada.
        **kwargs: Argumentos adicionais do signal.
    """
    try:
        # Busca o external_id antes do delete
        from .models import ContatoSync

        sync_record = ContatoSync.objects.filter(contato_id=instance.id).first()
        if sync_record and sync_record.external_id:
            # Executa sincronização de deleção imediatamente
            service = NotionSyncService()
            service.delete_record("Contato", sync_record.external_id)
            logger.info(f"Contato #{instance.id} arquivado no Notion (external_id: {sync_record.external_id})")
        else:
            logger.warning(f"Contato #{instance.id} não possui external_id para arquivar no Notion")

    except Exception as e:
        logger.error(f"Erro ao processar deleção de Contato #{instance.id}: {e}")


# Usar pre_delete em vez de post_delete para capturar sync_record antes do CASCADE
@receiver(pre_delete, sender=Cliente)
def on_cliente_pre_delete(
    sender: Any,
    instance: "Cliente",
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Cliente.

    Este receiver é disparado ANTES de um Cliente ser deletado
    para que possamos capturar o external_id antes do CASCADE.

    Args:
        sender: Classe do model que enviou o signal (Cliente).
        instance: Instância do Cliente que será deletada.
        **kwargs: Argumentos adicionais do signal.
    """
    try:
        # Busca o external_id antes do delete
        from .models import ClienteSync

        sync_record = ClienteSync.objects.filter(cliente_id=instance.id).first()
        if sync_record and sync_record.external_id:
            # Executa sincronização de deleção imediatamente
            service = NotionSyncService()
            service.delete_record("Cliente", sync_record.external_id)
            logger.info(f"Cliente #{instance.id} arquivado no Notion (external_id: {sync_record.external_id})")
        else:
            logger.warning(f"Cliente #{instance.id} não possui external_id para arquivar no Notion")

    except Exception as e:
        logger.error(f"Erro ao processar deleção de Cliente #{instance.id}: {e}")


@receiver(m2m_changed, sender=Contato.clientes.through)
def on_contato_clientes_changed(
    sender: Any,
    instance: "Contato",
    action: str,
    reverse: bool,
    model: "Cliente",
    pk_set: Any,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar mudanças no relacionamento Contato <-> Clientes.

    Este receiver é disparado quando um contato é associado/desassociado de clientes.
    Ele atualiza o campo de relacionamento no Notion.

    Args:
        sender: Classe do model through do relacionamento.
        instance: Instância do Contato que teve o relacionamento modificado.
        action: Tipo de ação ("post_add", "post_remove", "post_clear").
        reverse: Se a operação foi no sentido inverso.
        model: Model do outro lado do relacionamento (Cliente).
        pk_set: Set de primary keys adicionados/removidos.
        **kwargs: Argumentos adicionais do signal.
    """
    # Ignora se for operação reversa (será tratada no signal de Cliente)
    if reverse:
        return

    try:
        # Obtém o registro de sincronização
        from .models import ContatoSync

        sync_record = ContatoSync.objects.filter(contato_id=instance.id).first()
        if not sync_record or not sync_record.external_id:
            logger.warning(f"Contato #{instance.id} não possui sync_record para atualizar relacionamentos")
            return

        # Prepara dados atualizados para sincronização
        sync_record.prepare_notion_data()
        sync_record.save()

        # Executa sincronização de atualização
        service = NotionSyncService()
        success = service.update_record("Contato", sync_record.external_id, instance.id, sync_record)

        if success:
            sync_record.mark_as_synced()
            logger.info(f"Relacionamentos do Contato #{instance.id} atualizados no Notion (action: {action})")
        else:
            sync_record.mark_as_failed(f"Falha na atualização de relacionamentos (action: {action})")
            logger.error(f"Falha ao atualizar relacionamentos do Contato #{instance.id} (action: {action})")

    except Exception as e:
        logger.error(f"Erro ao processar mudança de relacionamento do Contato #{instance.id}: {e}")


@receiver(m2m_changed, sender=Cliente.contatos.through)
def on_cliente_contatos_changed(
    sender: Any,
    instance: "Cliente",
    action: str,
    reverse: bool,
    model: "Contato",
    pk_set: Any,
    **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar mudanças no relacionamento Cliente <-> Contatos.

    Este receiver é disparado quando um cliente tem contatos associados/desassociados.
    Ele atualiza o campo de relacionamento no Notion.

    Args:
        sender: Classe do model through do relacionamento.
        instance: Instância do Cliente que teve o relacionamento modificado.
        action: Tipo de ação ("post_add", "post_remove", "post_clear").
        reverse: Se a operação foi no sentido inverso.
        model: Model do outro lado do relacionamento (Contato).
        pk_set: Set de primary keys adicionados/removidos.
        **kwargs: Argumentos adicionais do signal.
    """
    # Ignora se for operação reversa (será tratada no signal de Contato)
    if reverse:
        return

    try:
        # Obtém o registro de sincronização
        from .models import ClienteSync

        sync_record = ClienteSync.objects.filter(cliente_id=instance.id).first()
        if not sync_record or not sync_record.external_id:
            logger.warning(f"Cliente #{instance.id} não possui sync_record para atualizar relacionamentos")
            return

        # Prepara dados atualizados para sincronização
        sync_record.prepare_notion_data()
        sync_record.save()

        # Executa sincronização de atualização
        service = NotionSyncService()
        success = service.update_record("Cliente", sync_record.external_id, instance.id, sync_record)

        if success:
            sync_record.mark_as_synced()
            logger.info(f"Relacionamentos do Cliente #{instance.id} atualizados no Notion (action: {action})")
        else:
            sync_record.mark_as_failed(f"Falha na atualização de relacionamentos (action: {action})")
            logger.error(f"Falha ao atualizar relacionamentos do Cliente #{instance.id} (action: {action})")

    except Exception as e:
        logger.error(f"Erro ao processar mudança de relacionamento do Cliente #{instance.id}: {e}")
