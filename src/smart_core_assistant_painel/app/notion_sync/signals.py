"""
Signals para sincronização automática de models com plataformas externas.

Este módulo contém os signal receivers que capturam mudanças nos models
principais (Cliente, Contato, Departamento, Atendente) e disparam
o processo de sincronização com plataformas externas (Notion, Airtable, etc).
"""

from typing import Any

from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.dispatch import receiver
from loguru import logger

from ..ui.atendimentos.models import Atendimento, Mensagem
from ..ui.clientes.models import Cliente, Contato
from ..ui.operacional.models import Atendente, Departamento
from .exceptions import NotionSyncError, SyncError
from .models import (
    AtendenteSync,
    AtendimentoSync,
    ClienteSync,
    ContatoSync,
    DepartamentoSync,
    MensagemSync,
)
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
            "config": config,
        },
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
            "config": config,
        },
    )
    return sync


def get_or_create_departamento_sync(departamento_id: int) -> DepartamentoSync:
    """
    Obtém ou cria registro DepartamentoSync para um departamento.

    Esta é uma função auxiliar para os signals de Departamento.

    Args:
        departamento_id: ID do departamento no Django.

    Returns:
        Instância do DepartamentoSync.
    """
    from .models import DepartamentoSync, NotionDatabaseConfig

    # Obter configuração do Notion para Departamentos
    try:
        config = NotionDatabaseConfig.objects.get(
            slug="ui_operacional_departamento"
        )
    except NotionDatabaseConfig.DoesNotExist:
        # Criar configuração padrão se não existir
        config = NotionDatabaseConfig.objects.create(
            slug="ui_operacional_departamento",
            name="Departamentos",
            django_model="operacional.Departamento",
            django_app_label="ui",
            notion_database_id="",  # Será preenchido depois
            sync_enabled=False,  # Inicia desabilitado
            description="Departamentos da organização",
        )

    sync, created = DepartamentoSync.objects.get_or_create(
        departamento_id=departamento_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config,
        },
    )
    return sync


def get_or_create_atendente_sync(atendente_id: int) -> AtendenteSync:
    """
    Obtém ou cria registro AtendenteSync para um atendente.

    Esta é uma função auxiliar para os signals de Atendente.

    Args:
        atendente_id: ID do atendente no Django.

    Returns:
        Instância do AtendenteSync.
    """
    from .models import AtendenteSync, NotionDatabaseConfig

    # Obter configuração do Notion para Atendentes
    try:
        config = NotionDatabaseConfig.objects.get(
            slug="ui_operacional_atendente"
        )
    except NotionDatabaseConfig.DoesNotExist:
        # Criar configuração padrão se não existir
        config = NotionDatabaseConfig.objects.create(
            slug="ui_operacional_atendente",
            name="Atendentes",
            django_model="operacional.Atendente",
            django_app_label="ui",
            notion_database_id="",  # Será preenchido depois
            sync_enabled=False,  # Inicia desabilitado
            description="Atendentes da organização",
        )

    sync, created = AtendenteSync.objects.get_or_create(
        atendente_id=atendente_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config,
        },
    )
    return sync


def get_or_create_atendimento_sync(atendimento_id: int) -> AtendimentoSync:
    """
    Obtém ou cria registro AtendimentoSync para um atendimento.
    """
    from .models import AtendimentoSync, NotionDatabaseConfig
    config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_atendimento")
    sync, created = AtendimentoSync.objects.get_or_create(
        atendimento_id=atendimento_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config,
        },
    )
    return sync


def get_or_create_mensagem_sync(mensagem_id: int) -> MensagemSync:
    """
    Obtém ou cria registro MensagemSync para uma mensagem.

    Comentário: Este helper garante que os campos obrigatórios
    (atendimento_sync, conteudo_formatado, remetente_formatado)
    sejam preenchidos na criação, evitando violações de NOT NULL.
    """
    from typing import Any
    from .models import MensagemSync, NotionDatabaseConfig
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Mensagem as MensagemModel,
    )

    config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_mensagem")

    mensagem_obj: MensagemModel | None = (
        MensagemModel.objects.filter(id=mensagem_id).select_related("atendimento")
        .first()
    )

    # Fallback defensivo caso mensagem não exista (não esperado)
    if not mensagem_obj:
        sync, _ = MensagemSync.objects.get_or_create(
            mensagem_id=mensagem_id,
            defaults={
                "external_id": None,
                "sync_status": "pending",
                "config": config,
                # Preenche mínimos para evitar falha
                "conteudo_formatado": "",
                "remetente_formatado": "Sistema",
            },
        )
        return sync

    # Garante que o atendimento_sync exista
    atendimento_sync = get_or_create_atendimento_sync(
        mensagem_obj.atendimento_id
    )

    # Formatação básica
    conteudo: str = mensagem_obj.conteudo or ""
    if mensagem_obj.remetente == "cliente" and mensagem_obj.atendimento \
            and mensagem_obj.atendimento.contato:
        remetente_formatado: str = (
            mensagem_obj.atendimento.contato.nome_contato or "Cliente"
        )
    elif mensagem_obj.remetente == "atendente" and mensagem_obj.atendimento \
            and mensagem_obj.atendimento.atendente_humano:
        remetente_formatado = (
            mensagem_obj.atendimento.atendente_humano.nome or "Atendente"
        )
    else:
        remetente_formatado = "Sistema"

    defaults: dict[str, Any] = {
        "external_id": None,
        "sync_status": "pending",
        "config": config,
        "atendimento_sync": atendimento_sync,
        "conteudo_formatado": conteudo,
        "remetente_formatado": remetente_formatado,
    }

    sync, _ = MensagemSync.objects.get_or_create(
        mensagem_id=mensagem_id,
        defaults=defaults,
    )
    return sync


def schedule_sync_operation(
    model_name: str, instance_id: int, operation: str
) -> None:
    """
    Agenda uma operação de sincronização.

    Esta função centraliza a lógica de agendamento de sincronizações
    e será usada pelos signals quando forem reabilitados.

    Args:
        model_name: Nome do modelo (ex: "Contato", "Cliente", "Departamento", "Atendente").
        instance_id: ID da instância.
        operation: Tipo de operação ("create", "update", "delete").
    """
    from .services import NotionSyncService
    from .models import (
        AtendenteSync,
        AtendimentoSync,
        ClienteSync,
        ContatoSync,
        DepartamentoSync,
        MensagemSync,
    )

    try:
        service = NotionSyncService()

        if operation == "delete":
            logger.warning(
                f"Operação de delete para {model_name} deve ser tratada em pre_delete signal"
            )
            return

        # Obter o registro sync correspondente (para create/update)
        if model_name == "Contato":
            sync_record = ContatoSync.objects.get(contato_id=instance_id)
        elif model_name == "Cliente":
            sync_record = ClienteSync.objects.get(cliente_id=instance_id)
        elif model_name == "Departamento":
            sync_record = DepartamentoSync.objects.get(
                departamento_id=instance_id
            )
        elif model_name == "Atendente":
            sync_record = AtendenteSync.objects.get(
                atendente_id=instance_id
            )
        elif model_name == "Atendimento":
            sync_record = AtendimentoSync.objects.get(atendimento_id=instance_id)
        elif model_name == "Mensagem":
            sync_record = MensagemSync.objects.get(mensagem_id=instance_id)
        else:
            logger.warning(f"Modelo não suportado: {model_name}")
            return

        logger.info(
            f"Executando sincronização: {model_name} #{instance_id} - {operation}"
        )
        logger.debug(f"Sync record: {sync_record}")

        if operation == "create":
            external_id = service.create_record(
                model_name, instance_id, sync_record
            )
            sync_record.mark_as_synced(external_id)

        elif operation == "update":
            if sync_record.external_id:
                success = service.update_record(
                    model_name,
                    sync_record.external_id,
                    instance_id,
                    sync_record,
                )
                if success:
                    sync_record.mark_as_synced()
                else:
                    sync_record.mark_as_failed("Falha na atualização")
            else:
                # Se não tem external_id, tenta criar
                external_id = service.create_record(
                    model_name, instance_id, sync_record
                )
                sync_record.external_id = external_id
                sync_record.mark_as_synced(external_id)
        logger.info(
            f"Sincronização executada com sucesso: {model_name} #{instance_id} - {operation}"
        )

    except Exception as e:
        logger.error(f"Erro ao executar sincronização: {e}")
        logger.exception("Stack trace completo do erro:")
        try:
            if model_name == "Contato":
                sync_record = ContatoSync.objects.get(contato_id=instance_id)
            elif model_name == "Cliente":
                sync_record = ClienteSync.objects.get(cliente_id=instance_id)
            elif model_name == "Atendimento":
                sync_record = AtendimentoSync.objects.get(atendimento_id=instance_id)
            logger.info(
                f"Marcando sync_record como falha: {model_name} #{instance_id}"
            )
            sync_record.mark_as_failed(str(e))
        except Exception as mark_error:
            logger.error(f"Erro ao marcar como falha: {mark_error}")
            logger.exception("Stack trace do erro de marcação:")


@receiver(post_save, sender=Contato)
def on_contato_saved(
    sender: Any, instance: "Contato", created: bool, **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar Contato quando salvo.
    """
    if kwargs.get("skip_sync", False):
        logger.debug(f"Sincronização ignorada para Contato #{instance.id}")
        return

    try:
        sync_metadata = get_or_create_contato_sync(instance.id)
        operation = "create" if created else "update"
        sync_metadata.prepare_notion_data()
        sync_metadata.save()
        schedule_sync_operation(
            model_name="Contato", instance_id=instance.id, operation=operation
        )
        logger.info(
            f"Contato #{instance.id} {'criado' if created else 'atualizado'}"
            f" - Sincronização agendada"
        )
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Contato #{instance.id}: {e}"
        )


@receiver(post_save, sender=Cliente)
def on_cliente_saved(
    sender: Any, instance: "Cliente", created: bool, **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar Cliente quando salvo.
    """
    if kwargs.get("skip_sync", False):
        logger.debug(f"Sincronização ignorada para Cliente #{instance.id}")
        return

    try:
        sync_metadata = get_or_create_cliente_sync(instance.id)
        operation = "create" if created else "update"
        sync_metadata.prepare_notion_data()
        sync_metadata.save()
        schedule_sync_operation(
            model_name="Cliente", instance_id=instance.id, operation=operation
        )
        logger.info(
            f"Cliente #{instance.id} {'criado' if created else 'atualizado'}"
            f" - Sincronização agendada"
        )
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Cliente #{instance.id}: {e}"
        )


@receiver(pre_delete, sender=Contato)
def on_contato_pre_delete(
    sender: Any, instance: "Contato", **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Contato.
    """
    try:
        from .models import ContatoSync

        sync_record = ContatoSync.objects.filter(
            contato_id=instance.id
        ).first()
        if sync_record and sync_record.external_id:
            service = NotionSyncService()
            service.delete_record("Contato", sync_record.external_id)
            logger.info(
                f"Contato #{instance.id} arquivado no Notion (external_id: {sync_record.external_id})"
            )
        else:
            logger.warning(
                f"Contato #{instance.id} não possui external_id para arquivar no Notion"
            )
    except Exception as e:
        logger.error(
            f"Erro ao processar deleção de Contato #{instance.id}: {e}"
        )


@receiver(pre_delete, sender=Cliente)
def on_cliente_pre_delete(
    sender: Any, instance: "Cliente", **kwargs: Any
) -> None:
    """
    Signal receiver para sincronizar deleção de Cliente.
    """
    try:
        from .models import ClienteSync

        sync_record = ClienteSync.objects.filter(
            cliente_id=instance.id
        ).first()
        if sync_record and sync_record.external_id:
            service = NotionSyncService()
            service.delete_record("Cliente", sync_record.external_id)
            logger.info(
                f"Cliente #{instance.id} arquivado no Notion (external_id: {sync_record.external_id})"
            )
        else:
            logger.warning(
                f"Cliente #{instance.id} não possui external_id para arquivar no Notion"
            )
    except Exception as e:
        logger.error(
            f"Erro ao processar deleção de Cliente #{instance.id}: {e}"
        )


@receiver(m2m_changed, sender=Contato.clientes.through)
def on_contato_clientes_changed(
    sender: Any,
    instance: "Contato",
    action: str,
    reverse: bool,
    model: "Cliente",
    pk_set: Any,
    **kwargs: Any,
) -> None:
    """
    Signal receiver para sincronizar mudanças no relacionamento Contato <-> Clientes.
    """
    if reverse:
        return

    try:
        from .models import ContatoSync

        sync_record = ContatoSync.objects.filter(
            contato_id=instance.id
        ).first()
        if not sync_record or not sync_record.external_id:
            logger.warning(
                f"Contato #{instance.id} não possui sync_record para atualizar relacionamentos"
            )
            return

        sync_record.prepare_notion_data()
        sync_record.save()

        service = NotionSyncService()
        success = service.update_record(
            "Contato", sync_record.external_id, instance.id, sync_record
        )

        if success:
            sync_record.mark_as_synced()
            logger.info(
                f"Relacionamentos do Contato #{instance.id} atualizados no Notion (action: {action})"
            )
        else:
            sync_record.mark_as_failed(
                f"Falha na atualização de relacionamentos (action: {action})"
            )
            logger.error(
                f"Falha ao atualizar relacionamentos do Contato #{instance.id} (action: {action})"
            )

        try:
            from .models import ClienteSync

            service = NotionSyncService()
            cliente_ids = list(pk_set or [])
            for cliente_id in cliente_ids:
                cliente_sync = ClienteSync.objects.filter(
                    cliente_id=cliente_id
                ).first()
                if not cliente_sync:
                    cliente_sync = get_or_create_cliente_sync(cliente_id)

                cliente_sync.prepare_notion_data()
                cliente_sync.save()

                if not cliente_sync.external_id:
                    try:
                        created_id = service.create_record(
                            "Cliente", cliente_id, cliente_sync
                        )
                        cliente_sync.external_id = created_id
                        cliente_sync.mark_as_synced()
                        cliente_sync.save()
                        logger.info(
                            f"Cliente #{cliente_id} criado no Notion "
                            f"(external_id: {created_id})"
                        )
                    except Exception as ce:
                        cliente_sync.mark_as_failed(str(ce))
                        logger.error(
                            f"Erro ao criar Cliente #{cliente_id} "
                            f"no Notion: {ce}"
                        )
                        continue

                try:
                    ok_cliente = service.update_record(
                        "Cliente",
                        cliente_sync.external_id,
                        cliente_id,
                        cliente_sync,
                    )
                    if ok_cliente:
                        cliente_sync.mark_as_synced()
                        logger.info(
                            f"Relacionamentos do Cliente #{cliente_id} "
                            f"atualizados (via Contato action: {action})"
                        )
                    else:
                        cliente_sync.mark_as_failed(
                            "Falha ao atualizar relacionamento (via Contato)"
                        )
                        logger.error(
                            f"Falha ao atualizar Cliente #{cliente_id} "
                            f"(via Contato)"
                        )
                except Exception as ue:
                    cliente_sync.mark_as_failed(str(ue))
                    logger.error(
                        f"Erro ao atualizar Cliente #{cliente_id} "
                        f"(via Contato): {ue}"
                    )
        except Exception as e_inner:
            logger.error(
                f"Erro ao sincronizar Clientes impactados "
                f"(Contato #{instance.id}): {e_inner}"
            )

    except Exception as e:
        logger.error(
            f"Erro ao processar mudança de relacionamento do Contato #{instance.id}: {e}"
        )


@receiver(m2m_changed, sender=Cliente.contatos.through)
def on_cliente_contatos_changed(
    sender: Any,
    instance: "Cliente",
    action: str,
    reverse: bool,
    model: "Contato",
    pk_set: Any,
    **kwargs: Any,
) -> None:
    """
    Signal receiver para sincronizar mudanças no relacionamento Cliente <-> Contatos.
    """
    if reverse:
        return

    try:
        service = NotionSyncService()

        if action in ("post_add", "post_remove", "post_clear"):
            try:
                from .models import ContatoSync

                for contato_id in pk_set or []:
                    contato_obj = Contato.objects.filter(pk=contato_id).first()
                    if not contato_obj:
                        continue

                    contato_sync = ContatoSync.objects.filter(
                        contato_id=contato_obj.id
                    ).first()
                    if not contato_sync:
                        contato_sync = get_or_create_contato_sync(
                            contato_obj.id
                        )

                    contato_sync.prepare_notion_data()
                    contato_sync.save()

                    if not contato_sync.external_id:
                        try:
                            created_id = service.create_record(
                                "Contato", contato_obj.id, contato_sync
                            )
                            contato_sync.external_id = created_id
                            contato_sync.mark_as_synced()
                            contato_sync.save()
                            logger.info(
                                f"Contato #{contato_obj.id} criado no Notion "
                                f"(external_id: {created_id})"
                            )
                        except Exception as ce:
                            contato_sync.mark_as_failed(str(ce))
                            logger.error(
                                f"Erro ao criar Contato #{contato_obj.id} "
                                f"no Notion: {ce}"
                            )
                            continue

                    try:
                        ok = service.update_record(
                            "Contato",
                            contato_sync.external_id,
                            contato_obj.id,
                            contato_sync,
                        )
                        if ok:
                            contato_sync.mark_as_synced()
                            logger.info(
                                f"Relacionamentos do Contato #{contato_obj.id} "
                                f"atualizados (via Cliente action: {action})"
                            )
                        else:
                            contato_sync.mark_as_failed(
                                "Falha ao atualizar relacionamento (via Cliente)"
                            )
                            logger.error(
                                f"Falha ao atualizar Contato #{contato_obj.id} "
                                f"(via Cliente)"
                            )
                    except Exception as ue:
                        contato_sync.mark_as_failed(str(ue))
                        logger.error(
                            f"Erro ao atualizar Contato #{contato_obj.id} "
                            f"(via Cliente): {ue}"
                        )
            except Exception as e_inner:
                logger.error(
                    f"Erro ao sincronizar contatos impactados "
                    f"(Cliente #{instance.id}): {e_inner}"
                )

        try:
            from .models import ClienteSync

            cliente_sync = ClienteSync.objects.filter(
                cliente_id=instance.id
            ).first()
            if not cliente_sync:
                cliente_sync = get_or_create_cliente_sync(instance.id)

            cliente_sync.prepare_notion_data()
            cliente_sync.save()

            if not cliente_sync.external_id:
                try:
                    created_id = service.create_record(
                        "Cliente", instance.id, cliente_sync
                    )
                    cliente_sync.external_id = created_id
                    cliente_sync.mark_as_synced()
                    cliente_sync.save()
                    logger.info(
                        f"Cliente #{instance.id} criado no Notion "
                        f"(external_id: {created_id})"
                    )
                except Exception as ce:
                    cliente_sync.mark_as_failed(str(ce))
                    logger.error(
                        f"Erro ao criar Cliente #{instance.id} no Notion: {ce}"
                    )
            else:
                try:
                    ok_cli = service.update_record(
                        "Cliente",
                        cliente_sync.external_id,
                        instance.id,
                        cliente_sync,
                    )
                    if ok_cli:
                        cliente_sync.mark_as_synced()
                        logger.info(
                            f"Cliente #{instance.id} atualizado "
                            f"(action: {action})"
                        )
                    else:
                        cliente_sync.mark_as_failed(
                            "Falha ao atualizar relacionamento (Cliente)"
                        )
                        logger.error(
                            f"Falha ao atualizar Cliente #{instance.id}"
                        )
                except Exception as ue:
                    cliente_sync.mark_as_failed(str(ue))
                    logger.error(
                        f"Erro ao atualizar Cliente #{instance.id}: {ue}"
                    )
        except Exception as e_cliente:
            logger.error(
                f"Erro ao sincronizar o cliente #{instance.id}: {e_cliente}"
            )

    except Exception as exc:
        logger.error(
            f"Erro ao processar mudança de contatos no cliente {instance.id}: {exc}"
        )


# Signals para Departamento
@receiver(post_save, sender=Departamento)
def on_departamento_saved(
    sender: type[Departamento],
    instance: Departamento,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Signal disparado após salvar um Departamento.
    """
    logger.info(f"Departamento salvo: {instance.nome} (created={created})")

    try:
        sync = get_or_create_departamento_sync(instance.id)
        logger.info(f"Sync criado/atualizado: {sync}")

        sync.prepare_notion_data()
        sync.save()

        schedule_sync_operation(
            model_name="Departamento",
            instance_id=instance.id,
            operation="create" if created else "update",
        )

    except Exception as exc:
        logger.error(
            f"Erro ao processar sync do departamento {instance.id}: {exc}"
        )


@receiver(pre_delete, sender=Departamento)
def on_departamento_pre_delete(
    sender: type[Departamento], instance: Departamento, **kwargs: Any
) -> None:
    """
    Signal disparado antes de excluir um Departamento.
    """
    logger.info(f"Departamento para exclusão: {instance.nome}")

    try:
        from .models import DepartamentoSync

        sync_record = DepartamentoSync.objects.filter(
            departamento_id=instance.id
        ).first()
        if sync_record and sync_record.external_id:
            service = NotionSyncService()
            service.delete_record("Departamento", sync_record.external_id)
            logger.info(
                f"Departamento #{instance.id} arquivado no Notion "
                f"(external_id: {sync_record.external_id})"
            )
        else:
            logger.warning(
                f"Departamento #{instance.id} não possui external_id "
                "para arquivar no Notion"
            )

    except Exception as exc:
        logger.error(
            f"Erro ao processar exclusão do departamento {instance.id}: {exc}"
        )


@receiver(post_save, sender=Atendente)
def on_atendente_department_change(
    sender: type[Atendente],
    instance: Atendente,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Signal disparado ao salvar Atendente.
    """
    return


@receiver(post_delete, sender=Atendente)
def on_atendente_deleted(
    sender: type[Atendente], instance: Atendente, **kwargs: Any
) -> None:
    """
    Signal disparado quando um Atendente é excluído.
    """
    return


# Signals para Atendente
@receiver(post_save, sender=Atendente)
def on_atendente_saved(
    sender: type[Atendente],
    instance: Atendente,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    Signal disparado após salvar um Atendente.
    """
    logger.info(f"Atendente salvo: {instance.nome} (created={created})")

    try:
        sync = get_or_create_atendente_sync(instance.id)
        logger.info(f"Sync criado/atualizado: {sync}")

        sync.prepare_notion_data()
        sync.save()

        schedule_sync_operation(
            model_name="Atendente",
            instance_id=instance.id,
            operation="create" if created else "update",
        )
        try:
            prev_id = getattr(instance, "_original_departamento_id", None)
            curr_id = instance.departamento_id

            ids_to_update: list[int] = []
            if created:
                if curr_id:
                    ids_to_update.append(curr_id)
            else:
                if prev_id != curr_id:
                    if prev_id:
                        ids_to_update.append(prev_id)
                    if curr_id:
                        ids_to_update.append(curr_id)

            for dep_id in ids_to_update:
                try:
                    dep_sync = get_or_create_departamento_sync(dep_id)
                    dep_sync.prepare_notion_data()
                    dep_sync.save()
                    schedule_sync_operation(
                        model_name="Departamento",
                        instance_id=dep_id,
                        operation="update",
                    )
                except Exception as e:
                    logger.error(
                        "Erro ao atualizar Departamento vinculado "
                        f"#{dep_id}: {e}"
                    )
        except Exception as e_dep:
            logger.error(
                "Erro ao processar atualização de departamentos relacionados "
                f"para atendente #{instance.id}: {e_dep}"
            )

    except Exception as exc:
        logger.error(
            f"Erro ao processar sync do atendente {instance.id}: {exc}"
        )


@receiver(pre_delete, sender=Atendente)
def on_atendente_pre_delete(
    sender: type[Atendente], instance: Atendente, **kwargs: Any
) -> None:
    """
    Signal disparado antes de excluir um Atendente.
    """
    logger.info(f"Atendente para exclusão: {instance.nome}")

    try:
        from .models import AtendenteSync

        sync_record = AtendenteSync.objects.filter(
            atendente_id=instance.id
        ).first()
        if sync_record and sync_record.external_id:
            service = NotionSyncService()
            service.delete_record("Atendente", sync_record.external_id)
            logger.info(
                f"Atendente #{instance.id} arquivado no Notion "
                f"(external_id: {sync_record.external_id})"
            )
        else:
            logger.warning(
                f"Atendente #{instance.id} não possui external_id "
                "para arquivar no Notion"
            )

        try:
            dep_id = instance.departamento_id
            if dep_id:
                dep_sync = get_or_create_departamento_sync(dep_id)
                dep_sync.prepare_notion_data()
                dep_sync.save()
                schedule_sync_operation(
                    model_name="Departamento",
                    instance_id=dep_id,
                    operation="update",
                )
        except Exception as e:
            logger.error(
                "Erro ao atualizar Departamento após exclusão do "
                f"atendente #{instance.id}: {e}"
            )

    except Exception as exc:
        logger.error(
            f"Erro ao processar exclusão do atendente {instance.id}: {exc}"
        )


@receiver(pre_save, sender=Atendente)
def on_atendente_pre_save(
    sender: type[Atendente], instance: Atendente, **kwargs: Any
) -> None:
    """
    Signal disparado antes de salvar um Atendente.
    """
    if instance.pk:
        try:
            original = Atendente.objects.get(pk=instance.pk)
            instance._original_departamento_id = original.departamento_id
        except Atendente.DoesNotExist:
            instance._original_departamento_id = None
    else:
        instance._original_departamento_id = None


# Signals para Atendimento
@receiver(post_save, sender=Atendimento)
def on_atendimento_saved(
    sender: Any, instance: "Atendimento", created: bool, **kwargs: Any
) -> None:
    if kwargs.get("skip_sync", False):
        return
    try:
        sync_metadata = get_or_create_atendimento_sync(instance.id)
        operation = "create" if created else "update"
        sync_metadata.prepare_notion_data()
        sync_metadata.save()
        schedule_sync_operation(
            model_name="Atendimento", instance_id=instance.id, operation=operation
        )
    except Exception as e:
        logger.error(f"Erro ao processar signal de Atendimento #{instance.id}: {e}")


@receiver(pre_delete, sender=Atendimento)
def on_atendimento_pre_delete(
    sender: Any, instance: "Atendimento", **kwargs: Any
) -> None:
    try:
        sync_record = AtendimentoSync.objects.filter(atendimento_id=instance.id).first()
        if sync_record and sync_record.external_id:
            service = NotionSyncService()
            service.delete_record("Atendimento", sync_record.external_id)
    except Exception as e:
        logger.error(f"Erro ao processar deleção de Atendimento #{instance.id}: {e}")


# Signals para Mensagem
@receiver(post_save, sender=Mensagem)
def on_mensagem_saved(
    sender: Any, instance: "Mensagem", created: bool, **kwargs: Any
) -> None:
    if kwargs.get("skip_sync", False) or not created:
        return  # Sincroniza apenas na criação
    try:
        sync_metadata = get_or_create_mensagem_sync(instance.id)
        sync_metadata.prepare_notion_data()
        sync_metadata.save()
        schedule_sync_operation(
            model_name="Mensagem", instance_id=instance.id, operation="create"
        )
    except Exception as e:
        logger.error(f"Erro ao processar signal de Mensagem #{instance.id}: {e}")
