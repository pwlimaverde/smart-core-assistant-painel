"""
Signals para sincronização automática de models com plataformas externas.

Este módulo contém os signal receivers que capturam mudanças nos models
principais (Cliente, Contato, Departamento, Atendente) e disparam
o processo de sincronização com plataformas externas (Notion, Airtable, etc).
"""

from typing import Any, Optional
import uuid

from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.dispatch import receiver
from django.db import transaction
from loguru import logger
from asgiref.sync import async_to_sync

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
from smart_core_assistant_painel.modules.services import (
    SERVICEHUB,
    FeaturesCompose,
)
from .services.mappers.contato_mapper import ContatoMapper
from .services.mappers.cliente_mapper import ClienteMapper
from .models import NotionDatabaseConfig


def _bootstrap_uds_for_contato(config: NotionDatabaseConfig) -> None:
    """
    Garante o bootstrap do UDS para o modelo Contato.

    - Atualiza o schema do Data Source de Contato no UDS.
    - Cria/atualiza a relação "Clientes Relacionados" se disponível.

    Comentários:
    - Idempotente no UDS in-memory; seguro para múltiplas invocações.
    - Não modifica configurações de Notion; apenas o schema do UDS.
    """

    # Garante que o UDS esteja inicializado no SERVICEHUB
    try:
        uds = SERVICEHUB.unified_data_service
    except Exception:
        FeaturesCompose.unifield_data_services()
        uds = SERVICEHUB.unified_data_service

    def _ensure_uds_data_source_id(
        cfg: NotionDatabaseConfig, service: Any
    ) -> str:
        """
        Garante que o `data_source_id` esteja definido para o config.

        - Se não houver, cria um container simples e vincula uma fonte
          usando o `slug` como ID estável no UDS in-memory.
        """
        # Quando já existir `data_source_id`, habilita `sync_enabled`
        # para permitir operações do UDS (ex.: update_schema).
        if cfg.data_source_id:
            if not getattr(cfg, "sync_enabled", False):
                cfg.sync_enabled = True
                cfg.save(update_fields=["sync_enabled"])
            return str(cfg.data_source_id)

        # Comentário: gerar UUID válido para o data_source_id
        ds_id_local: str = str(uuid.uuid4())
        container_name: str = cfg.name or "Unified Data Root"
        container_id: str = service.create_container(container_name)
        service.add_data_source(container_id, ds_id_local)
        # Habilita sync para que o adapter Notion consiga localizar
        # a configuração ao atualizar o schema via UDS.
        cfg.data_source_id = ds_id_local
        cfg.sync_enabled = True
        cfg.save(update_fields=["data_source_id", "sync_enabled"])
        return ds_id_local

    # Schema de Contato pelo mapper e garantia de data_source_id
    schema: dict[str, Any] = ContatoMapper.get_database_schema()
    contato_ds_id: str = _ensure_uds_data_source_id(config, uds)

    try:
        uds.update_schema(contato_ds_id, schema)
    except Exception as exc:
        logger.warning(
            f"Falha ao atualizar schema UDS para Contato: {exc}"
        )

    # Garante configuração de Clientes e cria a relação
    try:
        cliente_cfg: Optional[NotionDatabaseConfig] = (
            NotionDatabaseConfig.objects.filter(
                slug="ui_clientes_cliente"
            ).first()
        )
        if not cliente_cfg:
            cliente_cfg = NotionDatabaseConfig.objects.create(
                slug="ui_clientes_cliente",
                name="Clientes",
                django_model="clientes.Cliente",
                django_app_label="ui",
                notion_database_id="00000000-0000-0000-0000-000000000000",
                sync_enabled=False,
                description=(
                    "Configuração padrão para sincronização de Clientes"
                ),
            )

        cliente_ds_id: str = _ensure_uds_data_source_id(cliente_cfg, uds)
        # Cria propriedade de relação apenas quando ambos configs
        # possuem `database_id` válido (evita chamar Notion com UUID
        # placeholder). Para UDS in-memory, armazenar o target como
        # `database_id` também é aceitável.
        def _has_valid_db_id(cfg_obj: NotionDatabaseConfig) -> bool:
            try:
                return bool(cfg_obj.has_valid_database_id())
            except Exception:
                dbid = getattr(cfg_obj, "notion_database_id", None)
                return bool(dbid) and str(dbid) != (
                    "00000000-0000-0000-0000-000000000000"
                )

        if _has_valid_db_id(config) and _has_valid_db_id(cliente_cfg):
            target_db_id: str = str(cliente_cfg.notion_database_id)
            uds.add_relation_property(
                contato_ds_id,
                "Clientes Relacionados",
                target_db_id,
            )
        else:
            logger.warning(
                "Relação Contato -> Clientes não aplicada: IDs de "
                "database inválidos. Apenas schema UDS atualizado."
            )
    except Exception as exc:
        logger.warning(
            f"Falha ao configurar relação de Clientes no UDS: {exc}"
        )


def _bootstrap_uds_for_cliente(config: NotionDatabaseConfig) -> None:
    """
    Garante o bootstrap do UDS para o modelo Cliente.

    - Atualiza o schema do Data Source de Cliente no UDS.
    - Cria/atualiza a relação "Contatos Relacionados" se disponível.

    Comentários:
    - Idempotente no UDS; seguro para múltiplas invocações.
    - Não modifica configurações do Notion além do schema espelhado.
    """

    # Garante que o UDS esteja inicializado no SERVICEHUB
    try:
        uds = SERVICEHUB.unified_data_service
    except Exception:
        FeaturesCompose.unifield_data_services()
        uds = SERVICEHUB.unified_data_service

    def _ensure_uds_data_source_id(
        cfg: NotionDatabaseConfig, service: Any
    ) -> str:
        """
        Garante que o `data_source_id` esteja definido para o config.

        - Se não houver, cria um container simples e vincula uma fonte
          usando o `slug` como ID estável no UDS.
        """
        if cfg.data_source_id:
            return str(cfg.data_source_id)

        ds_id_local: str = str(uuid.uuid4())
        container_name: str = cfg.name or "Unified Data Root"
        container_id: str = service.create_container(container_name)
        service.add_data_source(container_id, ds_id_local)
        cfg.data_source_id = ds_id_local
        cfg.save(update_fields=["data_source_id"])
        return ds_id_local

    # Schema de Cliente pelo mapper e garantia de data_source_id
    schema: dict[str, Any] = ClienteMapper.get_database_schema()
    cliente_ds_id: str = _ensure_uds_data_source_id(config, uds)

    try:
        uds.update_schema(cliente_ds_id, schema)
    except Exception as exc:
        logger.warning(
            f"Falha ao atualizar schema UDS para Cliente: {exc}"
        )

    # Garante configuração de Contato e cria a relação inversa
    try:
        contato_cfg: Optional[NotionDatabaseConfig] = (
            NotionDatabaseConfig.objects.filter(
                slug="ui_clientes_contato"
            ).first()
        )
        if not contato_cfg:
            contato_cfg = NotionDatabaseConfig.objects.create(
                slug="ui_clientes_contato",
                name="Contatos",
                django_model="clientes.Contato",
                django_app_label="ui",
                notion_database_id=(
                    "00000000-0000-0000-0000-000000000000"
                ),
                sync_enabled=False,
                description=(
                    "Configuração padrão para sincronização de Contatos"
                ),
            )

        contato_ds_id: str = _ensure_uds_data_source_id(contato_cfg, uds)
        uds.add_relation_property(
            cliente_ds_id,
            "Contatos Relacionados",
            contato_ds_id,
        )
    except Exception as exc:
        logger.warning(
            f"Falha ao configurar relação de Contatos no UDS: {exc}"
        )


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

    # Obter ou criar configuração do Notion para Contatos
    # Comentário: evita NameError quando a config ainda não existe.
    try:
        config = NotionDatabaseConfig.objects.get(slug="ui_clientes_contato")
    except NotionDatabaseConfig.DoesNotExist:
        # Cria configuração padrão desabilitada com UUID placeholder válido
        config = NotionDatabaseConfig.objects.create(
            slug="ui_clientes_contato",
            name="Contatos",
            django_model="clientes.Contato",
            django_app_label="clientes",
            notion_database_id=(
                "00000000-0000-0000-0000-000000000000"
            ),
            sync_enabled=False,
            description=(
                "Configuração padrão para sincronização de Contatos"
            ),
        )

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

    # Obter ou criar configuração do Notion para Clientes
    # Comentário: evita NameError quando a config ainda não existe.
    try:
        config = NotionDatabaseConfig.objects.get(slug="ui_clientes_cliente")
    except NotionDatabaseConfig.DoesNotExist:
        # Cria configuração padrão desabilitada com UUID placeholder válido
        config = NotionDatabaseConfig.objects.create(
            slug="ui_clientes_cliente",
            name="Clientes",
            django_model="clientes.Cliente",
            django_app_label="clientes",
            notion_database_id=(
                "00000000-0000-0000-0000-000000000000"
            ),
            sync_enabled=False,
            description=(
                "Configuração padrão para sincronização de Clientes"
            ),
        )

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
        # Criar configuração padrão se não existir (UUID placeholder válido)
        config = NotionDatabaseConfig.objects.create(
            slug="ui_operacional_departamento",
            name="Departamentos",
            django_model="operacional.Departamento",
            django_app_label="ui",
            notion_database_id=(
                "00000000-0000-0000-0000-000000000000"
            ),
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
        # Criar configuração padrão se não existir (UUID placeholder válido)
        config = NotionDatabaseConfig.objects.create(
            slug="ui_operacional_atendente",
            name="Atendentes",
            django_model="operacional.Atendente",
            django_app_label="ui",
            notion_database_id=(
                "00000000-0000-0000-0000-000000000000"
            ),
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

    # Obter ou criar configuração do Notion para Atendimentos
    # Comentário: evita NameError quando a config ainda não existe.
    try:
        config = NotionDatabaseConfig.objects.get(
            slug="ui_atendimentos_atendimento"
        )
    except NotionDatabaseConfig.DoesNotExist:
        # Cria configuração padrão desabilitada (UUID placeholder válido)
        config = NotionDatabaseConfig.objects.create(
            slug="ui_atendimentos_atendimento",
            name="Atendimentos",
            django_model="atendimentos.Atendimento",
            django_app_label="ui",
            notion_database_id=(
                "00000000-0000-0000-0000-000000000000"
            ),
            sync_enabled=False,
            description=(
                "Configuração padrão para sincronização de Atendimentos"
            ),
        )
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

    # Obter ou criar configuração do Notion para Mensagens
    # Comentário: evita NameError quando a config ainda não existe.
    try:
        config = NotionDatabaseConfig.objects.get(
            slug="ui_atendimentos_mensagem"
        )
    except NotionDatabaseConfig.DoesNotExist:
        # Cria configuração padrão desabilitada (UUID placeholder válido)
        config = NotionDatabaseConfig.objects.create(
            slug="ui_atendimentos_mensagem",
            name="Mensagens",
            django_model="atendimentos.Mensagem",
            django_app_label="ui",
            notion_database_id=(
                "00000000-0000-0000-0000-000000000000"
            ),
            sync_enabled=False,
            description=(
                "Configuração padrão para sincronização de Mensagens"
            ),
        )

    mensagem_obj: MensagemModel | None = (
        MensagemModel.objects.filter(id=mensagem_id)
        .select_related("atendimento")
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
    if (
        mensagem_obj.remetente == "cliente"
        and mensagem_obj.atendimento
        and mensagem_obj.atendimento.contato
    ):
        remetente_formatado: str = (
            mensagem_obj.atendimento.contato.nome_contato or "Cliente"
        )
    elif (
        mensagem_obj.remetente == "atendente"
        and mensagem_obj.atendimento
        and mensagem_obj.atendimento.atendente_humano
    ):
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
            sync_record = AtendenteSync.objects.get(atendente_id=instance_id)
        elif model_name == "Atendimento":
            sync_record = AtendimentoSync.objects.get(
                atendimento_id=instance_id
            )
        elif model_name == "Mensagem":
            sync_record = MensagemSync.objects.get(mensagem_id=instance_id)
        else:
            logger.warning(f"Modelo não suportado: {model_name}")
            return

        logger.info(
            f"Executando sincronização: {model_name} #{instance_id} - {operation}"
        )
        logger.debug(f"Sync record: {sync_record}")

        # Validação de prontidão da configuração
        cfg = getattr(sync_record, "config", None)
        if not cfg or not cfg.is_ready_for_sync():
            # Comentário: informa detalhadamente o estado da configuração,
            # tratando UUID nulo como "não definido".
            try:
                db_id_ok = cfg.has_valid_database_id() if cfg else False
            except Exception:
                db_id_ok = bool(getattr(cfg, "notion_database_id", None))

            try:
                ds_id_ok = cfg.has_valid_data_source_id() if cfg else False
            except Exception:
                ds_id_ok = bool(getattr(cfg, "data_source_id", None))

            ready_details = (
                f"ready={cfg.is_ready_for_sync() if cfg else False} "
                f"sync_enabled={getattr(cfg, 'sync_enabled', False)} "
                f"db_id_set={db_id_ok} "
                f"ds_id_set={ds_id_ok}"
            )
            msg = (
                "Configuração Notion não pronta para sincronização. "
                f"{ready_details}"
            )
            logger.warning(msg)
            try:
                sync_record.mark_as_failed(msg)
            except Exception:
                # Fallback caso método não exista; atualiza campos básicos
                sync_record.sync_status = "disabled"
                sync_record.sync_error = msg
                sync_record.save()
            return

        # Validação específica para Mensagem: precisa do atendimento pai
        if model_name == "Mensagem":
            try:
                at_sync = getattr(sync_record, "atendimento_sync", None)
                parent_id = getattr(at_sync, "external_id", None)
                if not parent_id:
                    msg = (
                        "Mensagem não pode ser sincronizada: atendimento pai "
                        "sem external_id."
                    )
                    logger.warning(msg)
                    try:
                        sync_record.mark_as_failed(msg)
                    except Exception:
                        sync_record.sync_status = "error"
                        sync_record.sync_error = msg
                        sync_record.save()
                    return
            except Exception as e:
                logger.error(
                    ("Erro ao validar relacionamento de Mensagem: {}").format(
                        e
                    )
                )
                try:
                    sync_record.mark_as_failed(str(e))
                except Exception:
                    sync_record.sync_status = "error"
                    sync_record.sync_error = str(e)
                    sync_record.save()
                return

        # Integração UDS para Contato: criação/atualização via serviço unificado
        if model_name == "Contato":
            try:
                # Garante serviço UDS
                try:
                    uds = SERVICEHUB.unified_data_service
                except Exception:
                    FeaturesCompose.unifield_data_services()
                    uds = SERVICEHUB.unified_data_service

                # Prepara payload (propriedades do Notion)
                payload = getattr(sync_record, "notion_properties", {})
                if not isinstance(payload, dict) or not payload:
                    # Comentário: garante que o mapper foi aplicado
                    sync_record.prepare_notion_data()
                    payload = getattr(sync_record, "notion_properties", {})

                ds_id = str(getattr(cfg, "data_source_id", "") or "")
                if not ds_id:
                    msg = (
                        "Config Notion para Contato sem data_source_id. "
                        "Execute bootstrap de Clientes/Contatos."
                    )
                    sync_record.mark_as_failed(msg)
                    logger.warning(msg)
                    return

                if operation == "create":
                    page_id = uds.create_item(ds_id, payload)
                    sync_record.external_id = page_id
                    sync_record.mark_as_synced(page_id)
                elif operation == "update":
                    if sync_record.external_id:
                        op_id = uds.update_item(
                            ds_id, sync_record.external_id, payload
                        )
                        if op_id:
                            sync_record.mark_as_synced()
                        else:
                            sync_record.mark_as_failed(
                                "Falha na atualização via UDS"
                            )
                    else:
                        # Sem external_id, cria primeiro
                        page_id = uds.create_item(ds_id, payload)
                        sync_record.external_id = page_id
                        sync_record.mark_as_synced(page_id)

                logger.info(
                    (
                        "Sincronização via UDS concluída: Contato #{} - {}"
                    ).format(instance_id, operation)
                )
                return
            except Exception as uds_err:
                # Em caso de erro no UDS, marca falha e segue para logging
                sync_record.mark_as_failed(str(uds_err))
                logger.error(
                    (
                        "Erro na sincronização via UDS para Contato #{}: {}"
                    ).format(instance_id, uds_err)
                )

        # Demais modelos seguem fluxo do NotionSyncService
        # Integração UDS para Cliente: criação/atualização via serviço unificado
        if model_name == "Cliente":
            try:
                # Garante serviço UDS
                try:
                    uds = SERVICEHUB.unified_data_service
                except Exception:
                    FeaturesCompose.unifield_data_services()
                    uds = SERVICEHUB.unified_data_service

                # Prepara payload (propriedades do Notion)
                payload = getattr(sync_record, "notion_properties", {})
                if not isinstance(payload, dict) or not payload:
                    # Comentário: garante que o mapper foi aplicado
                    sync_record.prepare_notion_data()
                    payload = getattr(sync_record, "notion_properties", {})

                ds_id = str(getattr(cfg, "data_source_id", "") or "")
                if not ds_id:
                    msg = (
                        "Config Notion para Cliente sem data_source_id. "
                        "Execute bootstrap de Clientes/Contatos."
                    )
                    sync_record.mark_as_failed(msg)
                    logger.warning(msg)
                    return

                if operation == "create":
                    page_id = uds.create_item(ds_id, payload)
                    sync_record.external_id = page_id
                    sync_record.mark_as_synced(page_id)
                elif operation == "update":
                    if sync_record.external_id:
                        op_id = uds.update_item(
                            ds_id, sync_record.external_id, payload
                        )
                        if op_id:
                            sync_record.mark_as_synced()
                        else:
                            sync_record.mark_as_failed(
                                "Falha na atualização via UDS"
                            )
                    else:
                        # Sem external_id, cria primeiro
                        page_id = uds.create_item(ds_id, payload)
                        sync_record.external_id = page_id
                        sync_record.mark_as_synced(page_id)

                logger.info(
                    (
                        "Sincronização via UDS concluída: Cliente #{} - {}"
                    ).format(instance_id, operation)
                )
                return
            except Exception as uds_err:
                # Em caso de erro no UDS, marca falha e segue para logging
                sync_record.mark_as_failed(str(uds_err))
                logger.error(
                    (
                        "Erro na sincronização via UDS para Cliente #{}: {}"
                    ).format(instance_id, uds_err)
                )

        # Demais modelos seguem fluxo do NotionSyncService
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
                sync_record = AtendimentoSync.objects.get(
                    atendimento_id=instance_id
                )
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

        def _after_commit() -> None:
            """Executa sincronização e bootstrap após o commit da transação.

            Comentário: evita quebrar a transação do admin quando
            qualquer erro ocorre; toda operação pesada roda pós-commit.
            """
            try:
                # Garantir que a configuração de Notion existe e está pronta
                ok_ready = ensure_clientes_configs_ready()
                if not ok_ready:
                    logger.warning(
                        "Config Notion para Clientes/Contatos ainda não pronta."
                    )
                sync_metadata.prepare_notion_data()
                sync_metadata.save()
                # Bootstrap UDS (schema e relação) de forma resiliente
                try:
                    _bootstrap_uds_for_contato(sync_metadata.config)
                except Exception as exc:
                    logger.warning(
                        "Falha no bootstrap UDS para Contato #{}: {}",
                        instance.id,
                        str(exc),
                    )
                schedule_sync_operation(
                    model_name="Contato",
                    instance_id=instance.id,
                    operation=operation,
                )
                logger.info(
                    "Contato #{} {} - Sincronização agendada",
                    instance.id,
                    "criado" if created else "atualizado",
                )
            except Exception as err:
                logger.error(
                    "Erro pós-commit no signal de Contato #{}: {}",
                    instance.id,
                    str(err),
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            f"Erro ao preparar sync de Contato #{instance.id}: {e}"
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

        def _after_commit() -> None:
            """Executa sincronização e bootstrap após o commit da transação.

            Comentário: mantém simetria com Contato, garantindo que a
            criação das databases (Clientes/Contatos) no Notion seja
            disparada caso ainda não existam.
            """
            try:
                # Garantir que a configuração de Notion existe e está pronta
                ok_ready = ensure_clientes_configs_ready()
                if not ok_ready:
                    logger.warning(
                        "Config Notion para Clientes/Contatos ainda não pronta."
                    )

                # Preparar e salvar metadados de sync
                sync_metadata.prepare_notion_data()
                sync_metadata.save()

                # Bootstrap UDS (schema e relação) de forma resiliente
                try:
                    _bootstrap_uds_for_cliente(sync_metadata.config)
                except Exception as exc:
                    logger.warning(
                        "Falha no bootstrap UDS para Cliente #{}: {}",
                        instance.id,
                        str(exc),
                    )

                # Agendar operação de sincronização
                schedule_sync_operation(
                    model_name="Cliente",
                    instance_id=instance.id,
                    operation=operation,
                )
                logger.info(
                    "Cliente #{} {} - Sincronização agendada",
                    instance.id,
                    "criado" if created else "atualizado",
                )
            except Exception as err:
                logger.error(
                    "Erro pós-commit no signal de Cliente #{}: {}",
                    instance.id,
                    str(err),
                )

        transaction.on_commit(_after_commit)
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
        logger.info(f"[SIGNAL_DEBUG] Signal de atendimento disparado para #{instance.id} (created={created})")
        logger.info(f"[SIGNAL_DEBUG] Contexto da conversa no signal: {instance.contexto_conversa}")

        sync_metadata = get_or_create_atendimento_sync(instance.id)
        logger.info(f"[SIGNAL_DEBUG] Sync metadata criado: {sync_metadata.id}")

        operation = "create" if created else "update"
        logger.info(f"[SIGNAL_DEBUG] Operação: {operation}")

        sync_metadata.prepare_notion_data()
        logger.info(f"[SIGNAL_DEBUG] Dados preparados com sucesso")

        sync_metadata.save()
        logger.info(f"[SIGNAL_DEBUG] Sync metadata salvo")

        schedule_sync_operation(
            model_name="Atendimento", instance_id=instance.id, operation=operation
        )
        logger.info(f"[SIGNAL_DEBUG] Operação de sync agendada")
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Atendimento #{instance.id}: {e}", exc_info=True
        )


@receiver(pre_delete, sender=Atendimento)
def on_atendimento_pre_delete(
    sender: Any, instance: "Atendimento", **kwargs: Any
) -> None:
    try:
        sync_record = AtendimentoSync.objects.filter(
            atendimento_id=instance.id
        ).first()
        if sync_record and sync_record.external_id:
            service = NotionSyncService()
            service.delete_record("Atendimento", sync_record.external_id)
    except Exception as e:
        logger.error(
            f"Erro ao processar deleção de Atendimento #{instance.id}: {e}"
        )


# Signals para Mensagem
@receiver(post_save, sender=Mensagem)
def on_mensagem_saved(
    sender: Any, instance: "Mensagem", created: bool, **kwargs: Any
) -> None:
    if kwargs.get("skip_sync", False):
        return
    try:
        # Sincroniza a mensagem (criação ou atualização)
        sync_metadata = get_or_create_mensagem_sync(instance.id)
        sync_metadata.prepare_notion_data()
        sync_metadata.save()

        # Verifica se precisa sincronizar (incluindo atualizações de campos importantes)
        if sync_metadata.needs_sync():
            # Define a operação com base no status
            operation = "create" if created else "update"
            schedule_sync_operation(
                model_name="Mensagem", instance_id=instance.id, operation=operation
            )
            logger.info(f"Mensagem {operation.lower()}izada: #{instance.id}")

        # ATUALIZAÇÃO: Também atualiza o atendimento relacionado se houver resposta do bot
        if instance.atendimento and (instance.resposta_bot or instance.respondida):
            # Obtém ou cria o sync do atendimento
            atendimento_sync = get_or_create_atendimento_sync(instance.atendimento.id)

            # Prepara e salva os dados atualizados do atendimento
            atendimento_sync.prepare_notion_data()
            atendimento_sync.save()

            # Agenda a atualização do atendimento
            schedule_sync_operation(
                model_name="Atendimento",
                instance_id=instance.atendimento.id,
                operation="update"
            )
            logger.info(f"Atendimento #{instance.atendimento.id} atualizado com resposta do bot")

    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Mensagem #{instance.id}: {e}", exc_info=True
        )
def ensure_clientes_configs_ready() -> bool:
    """Garante que as configs de Clientes/Contatos no Notion existam.

    Comentário (PT-BR):
    - Se as configurações já estiverem prontas, retorna True.
    - Caso contrário, constrói as databases via construtor assíncrono
      e salva no `NotionDatabaseConfig`.
    """
    try:
        contato_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_clientes_contato"
        ).first()
        cliente_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_clientes_cliente"
        ).first()

        if (
            contato_cfg
            and cliente_cfg
            and contato_cfg.is_ready_for_sync()
            and cliente_cfg.is_ready_for_sync()
        ):
            return True

        # Construir bases Notion e salvar configs
        try:
            from .services.bootstrap_clientes import (
                NotionClientesBootstrapService,
            )

            bootstrap = NotionClientesBootstrapService()
            async_to_sync(bootstrap.construct_minimal)()
            logger.info(
                "Databases Notion criadas (sem exemplos) e configs salvas."
            )
            # Revalidar
            contato_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_clientes_contato"
            ).first()
            cliente_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_clientes_cliente"
            ).first()
            return bool(
                contato_cfg
                and cliente_cfg
                and contato_cfg.is_ready_for_sync()
                and cliente_cfg.is_ready_for_sync()
            )
        except Exception as exc:
            logger.error(
                f"Erro ao construir bases Notion (Clientes/Contatos): {exc}"
            )
            return False
    except Exception as outer:
        logger.error(
            f"Falha ao verificar/garantir configs de Clientes/Contatos: {outer}"
        )
        return False
