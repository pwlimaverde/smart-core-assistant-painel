"""
Signals para sincronização automática de models com plataformas externas.

Este módulo contém os signal receivers que capturam mudanças nos models
principais (Cliente, Contato, Departamento, Atendente) e disparam
o processo de sincronização com plataformas externas (Notion, Airtable, etc).
"""

from typing import Any, Optional
import time
import uuid

from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.dispatch import receiver
from django.db import transaction, connection
from loguru import logger
from asgiref.sync import async_to_sync
from django_q.tasks import async_task

from ..ui.atendimentos.models import Atendimento, Mensagem
from ..ui.clientes.models import Cliente, Contato
from ..ui.operacional.models import (
    Atendente,
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
    MovimentoFluxo,
)
from .exceptions import NotionSyncError, SyncError
from .models import (
    AtendenteSync,
    AtendimentoSync,
    ClienteSync,
    ContatoSync,
    DepartamentoSync,
    MensagemSync,
    FluxoAtendimentoSync,
    EtapaFluxoSync,
    MovimentoFluxoSync,
)
from .services import NotionSyncService
from smart_core_assistant_painel.modules.services import (
    SERVICEHUB,
    FeaturesCompose,
)
from .services.mappers.contato_mapper import ContatoMapper
from .services.mappers.cliente_mapper import ClienteMapper
from .services.mappers.departamento_mapper import DepartamentoMapper
from .services.mappers.atendente_mapper import AtendenteMapper
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
        logger.warning(f"Falha ao atualizar schema UDS para Contato: {exc}")

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
        logger.warning(f"Falha ao atualizar schema UDS para Cliente: {exc}")

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
                notion_database_id=("00000000-0000-0000-0000-000000000000"),
                sync_enabled=False,
                description=(
                    "Configuração padrão para sincronização de Contatos"
                ),
            )

        # Cria propriedade de relação apenas quando ambos configs
        # possuem `database_id` válido (evita chamar Notion com UUID
        # placeholder). O terceiro parâmetro deve ser o `database_id`
        # de destino, não o `data_source_id`.
        contato_ds_id: str = _ensure_uds_data_source_id(contato_cfg, uds)

        def _has_valid_db_id(cfg_obj: NotionDatabaseConfig) -> bool:
            try:
                return bool(cfg_obj.has_valid_database_id())
            except Exception:
                dbid = getattr(cfg_obj, "notion_database_id", None)
                return bool(dbid) and str(dbid) != (
                    "00000000-0000-0000-0000-000000000000"
                )

        if _has_valid_db_id(contato_cfg) and _has_valid_db_id(config):
            target_db_id: str = str(contato_cfg.notion_database_id)
            uds.add_relation_property(
                cliente_ds_id,
                "Contatos Relacionados",
                target_db_id,
            )
        else:
            logger.warning(
                "Relação Cliente -> Contatos não aplicada: IDs de "
                "database inválidos. Apenas schema UDS atualizado."
            )
    except Exception as exc:
        logger.warning(
            f"Falha ao configurar relação de Contatos no UDS: {exc}"
        )


def _bootstrap_uds_for_departamento(config: NotionDatabaseConfig) -> None:
    """
    Garante o bootstrap do UDS para o modelo Departamento.

    - Atualiza o schema do Data Source de Departamento no UDS.
    - Cria/atualiza a relação "Atendentes Relacionados" se disponível.

    Comentário:
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

        - Cria container e data source quando ausente.
        """
        if cfg.data_source_id:
            if not getattr(cfg, "sync_enabled", False):
                cfg.sync_enabled = True
                cfg.save(update_fields=["sync_enabled"])
            return str(cfg.data_source_id)

        ds_id_local: str = str(uuid.uuid4())
        container_name: str = cfg.name or "Unified Data Root"
        container_id: str = service.create_container(container_name)
        service.add_data_source(container_id, ds_id_local)
        cfg.data_source_id = ds_id_local
        cfg.sync_enabled = True
        cfg.save(update_fields=["data_source_id", "sync_enabled"])
        return ds_id_local

    # Schema e data source de Departamento
    schema: dict[str, Any] = DepartamentoMapper.get_notion_schema()
    departamento_ds_id: str = _ensure_uds_data_source_id(config, uds)

    try:
        uds.update_schema(departamento_ds_id, schema)
    except Exception as exc:
        logger.warning(
            f"Falha ao atualizar schema UDS para Departamento: {exc}"
        )

    # Configuração de Atendente e relação
    try:
        atendente_cfg: Optional[NotionDatabaseConfig] = (
            NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_atendente"
            ).first()
        )
        if not atendente_cfg:
            atendente_cfg = NotionDatabaseConfig.objects.create(
                slug="ui_operacional_atendente",
                name="Atendentes",
                django_model="operacional.Atendente",
                django_app_label="ui",
                notion_database_id=("00000000-0000-0000-0000-000000000000"),
                sync_enabled=False,
                description=(
                    "Configuração padrão para sincronização de Atendentes"
                ),
            )

        atendente_ds_id: str = _ensure_uds_data_source_id(atendente_cfg, uds)

        def _has_valid_db_id(cfg_obj: NotionDatabaseConfig) -> bool:
            try:
                return bool(cfg_obj.has_valid_database_id())
            except Exception:
                dbid = getattr(cfg_obj, "notion_database_id", None)
                return bool(dbid) and str(dbid) != (
                    "00000000-0000-0000-0000-000000000000"
                )

        if _has_valid_db_id(config) and _has_valid_db_id(atendente_cfg):
            target_db_id: str = str(atendente_cfg.notion_database_id)
            uds.add_relation_property(
                departamento_ds_id,
                "Atendentes Relacionados",
                target_db_id,
            )
        else:
            logger.warning(
                "Relação Departamento -> Atendentes não aplicada: IDs de "
                "database inválidos. Apenas schema UDS atualizado."
            )
    except Exception as exc:
        logger.warning(
            f"Falha ao configurar relação de Atendentes no UDS: {exc}"
        )


def _bootstrap_uds_for_atendente(config: NotionDatabaseConfig) -> None:
    """
    Garante o bootstrap do UDS para o modelo Atendente.

    - Atualiza o schema do Data Source de Atendente no UDS.
    - Cria/atualiza a relação "Departamentos Relacionados" se disponível.

    Comentário:
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

        - Cria container e data source quando ausente.
        """
        if cfg.data_source_id:
            if not getattr(cfg, "sync_enabled", False):
                cfg.sync_enabled = True
                cfg.save(update_fields=["sync_enabled"])
            return str(cfg.data_source_id)

        ds_id_local: str = str(uuid.uuid4())
        container_name: str = cfg.name or "Unified Data Root"
        container_id: str = service.create_container(container_name)
        service.add_data_source(container_id, ds_id_local)
        cfg.data_source_id = ds_id_local
        cfg.sync_enabled = True
        cfg.save(update_fields=["data_source_id", "sync_enabled"])
        return ds_id_local

    # Schema e data source de Atendente
    schema: dict[str, Any] = AtendenteMapper.get_notion_schema()
    atendente_ds_id: str = _ensure_uds_data_source_id(config, uds)

    try:
        uds.update_schema(atendente_ds_id, schema)
    except Exception as exc:
        logger.warning(f"Falha ao atualizar schema UDS para Atendente: {exc}")

    # Configuração de Departamento e relação
    try:
        departamento_cfg: Optional[NotionDatabaseConfig] = (
            NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_departamento"
            ).first()
        )
        if not departamento_cfg:
            departamento_cfg = NotionDatabaseConfig.objects.create(
                slug="ui_operacional_departamento",
                name="Departamentos",
                django_model="operacional.Departamento",
                django_app_label="ui",
                notion_database_id=("00000000-0000-0000-0000-000000000000"),
                sync_enabled=False,
                description=(
                    "Configuração padrão para sincronização de Departamentos"
                ),
            )

        departamento_ds_id: str = _ensure_uds_data_source_id(
            departamento_cfg, uds
        )

        def _has_valid_db_id(cfg_obj: NotionDatabaseConfig) -> bool:
            try:
                return bool(cfg_obj.has_valid_database_id())
            except Exception:
                dbid = getattr(cfg_obj, "notion_database_id", None)
                return bool(dbid) and str(dbid) != (
                    "00000000-0000-0000-0000-000000000000"
                )

        if _has_valid_db_id(config) and _has_valid_db_id(departamento_cfg):
            target_db_id: str = str(departamento_cfg.notion_database_id)
            uds.add_relation_property(
                atendente_ds_id,
                "Departamentos Relacionados",
                target_db_id,
            )
        else:
            logger.warning(
                "Relação Atendente -> Departamentos não aplicada: IDs de "
                "database inválidos. Apenas schema UDS atualizado."
            )
    except Exception as exc:
        logger.warning(
            f"Falha ao configurar relação de Departamentos no UDS: {exc}"
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
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
            sync_enabled=False,
            description=("Configuração padrão para sincronização de Contatos"),
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
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
            sync_enabled=False,
            description=("Configuração padrão para sincronização de Clientes"),
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
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
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
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
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
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
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
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
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


def get_or_create_fluxo_sync(fluxo_id: int) -> FluxoAtendimentoSync:
    """
    Obtém ou cria registro FluxoAtendimentoSync para um fluxo.

    Comentário: garante existência de configuração Notion mínima
    e cria o espelho com status pendente.

    Args:
        fluxo_id: ID do fluxo de atendimento no Django.

    Returns:
        Instância do FluxoAtendimentoSync.
    """
    from .models import FluxoAtendimentoSync, NotionDatabaseConfig

    try:
        config = NotionDatabaseConfig.objects.get(
            slug="ui_operacional_fluxo_atendimento"
        )
    except NotionDatabaseConfig.DoesNotExist:
        config = NotionDatabaseConfig.objects.create(
            slug="ui_operacional_fluxo_atendimento",
            name="Fluxos de Atendimento",
            django_model="operacional.FluxoAtendimento",
            django_app_label="ui",
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
            sync_enabled=False,
            description="Config de Fluxos de Atendimento (placeholder)",
        )

    sync, _ = FluxoAtendimentoSync.objects.get_or_create(
        fluxo_id=fluxo_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config,
        },
    )
    return sync


def get_or_create_etapa_sync(etapa_id: int) -> EtapaFluxoSync:
    """
    Obtém ou cria registro EtapaFluxoSync para uma etapa.

    Comentário: garante configuração Notion mínima e cria espelho.

    Args:
        etapa_id: ID da etapa no Django.

    Returns:
        Instância do EtapaFluxoSync.
    """
    from .models import EtapaFluxoSync, NotionDatabaseConfig

    try:
        config = NotionDatabaseConfig.objects.get(
            slug="ui_operacional_etapa_fluxo"
        )
    except NotionDatabaseConfig.DoesNotExist:
        config = NotionDatabaseConfig.objects.create(
            slug="ui_operacional_etapa_fluxo",
            name="Etapas do Fluxo",
            django_model="operacional.EtapaFluxo",
            django_app_label="ui",
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
            sync_enabled=False,
            description="Config de Etapas do Fluxo (placeholder)",
        )

    sync, _ = EtapaFluxoSync.objects.get_or_create(
        etapa_id=etapa_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config,
        },
    )
    return sync


def get_or_create_movimento_sync(movimento_id: int) -> MovimentoFluxoSync:
    """
    Obtém ou cria registro MovimentoFluxoSync para um movimento do fluxo.

    Comentário: garante configuração Notion mínima e cria espelho.

    Args:
        movimento_id: ID do movimento no Django.

    Returns:
        Instância do MovimentoFluxoSync.
    """
    from .models import MovimentoFluxoSync, NotionDatabaseConfig

    try:
        config = NotionDatabaseConfig.objects.get(
            slug="ui_operacional_movimento_fluxo"
        )
    except NotionDatabaseConfig.DoesNotExist:
        config = NotionDatabaseConfig.objects.create(
            slug="ui_operacional_movimento_fluxo",
            name="Movimentos do Fluxo",
            django_model="operacional.MovimentoFluxo",
            django_app_label="ui",
            notion_database_id=("00000000-0000-0000-0000-000000000000"),
            sync_enabled=False,
            description="Config de Movimentos do Fluxo (placeholder)",
        )

    sync, _ = MovimentoFluxoSync.objects.get_or_create(
        movimento_id=movimento_id,
        defaults={
            "external_id": None,
            "sync_status": "pending",
            "config": config,
        },
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
        FluxoAtendimentoSync,
        EtapaFluxoSync,
        MovimentoFluxoSync,
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
        elif model_name == "FluxoAtendimento":
            sync_record = FluxoAtendimentoSync.objects.get(
                fluxo_id=instance_id
            )
        elif model_name == "EtapaFluxo":
            sync_record = EtapaFluxoSync.objects.get(etapa_id=instance_id)
        elif model_name == "MovimentoFluxo":
            sync_record = MovimentoFluxoSync.objects.get(
                movimento_id=instance_id
            )
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

                # Comentário: aguarda external_id de clientes relacionados em updates
                if operation == "update":
                    try:
                        contato_obj = Contato.objects.filter(
                            pk=instance_id
                        ).first()
                        if contato_obj:
                            attempts = 0
                            max_attempts = 5
                            delay_sec = 1
                            while attempts < max_attempts:
                                pending = False
                                for cli in contato_obj.clientes.all():
                                    from .models import ClienteSync

                                    cli_sync = ClienteSync.objects.filter(
                                        cliente_id=cli.id
                                    ).first()
                                    if not cli_sync or not getattr(
                                        cli_sync, "external_id", None
                                    ):
                                        pending = True
                                        break
                                if not pending:
                                    break
                                attempts += 1
                                time.sleep(delay_sec)
                    except Exception as wait_err:
                        logger.warning(
                            (
                                "Falha ao aguardar external_id de clientes "
                                "relacionados ao Contato #{}: {}"
                            ).format(instance_id, wait_err)
                        )

                # Prepara payload (propriedades do Notion)
                # Comentário: em updates, sempre recalcula para refletir
                # relacionamentos atualizados (evita usar cache antigo).
                if operation == "update":
                    try:
                        sync_record.prepare_notion_data()
                    except Exception as prep_err:
                        logger.warning(
                            (
                                "Falha ao preparar dados do Contato #{}: {}"
                            ).format(instance_id, prep_err)
                        )

                payload = getattr(sync_record, "notion_properties", {})
                if not isinstance(payload, dict) or not payload:
                    # Comentário: garante que o mapper foi aplicado
                    sync_record.prepare_notion_data()
                    payload = getattr(sync_record, "notion_properties", {})

                # LOG: visualizar execução da atualização do Contato com
                # foco no relacionamento "Clientes Relacionados".
                try:
                    rel = payload.get("Clientes Relacionados", {}).get(
                        "relation", []
                    )
                    rel_ids = [str(it.get("id")) for it in rel]
                    logger.info(
                        (
                            "[LINK_SYNC] Execução update Contato #{} "
                            "com clientes_relacionados={}"
                        ).format(instance_id, len(rel_ids))
                    )
                    if rel_ids:
                        logger.debug(
                            (
                                "[LINK_SYNC] IDs clientes no payload do "
                                "Contato #{}: {}"
                            ).format(instance_id, rel_ids)
                        )
                except Exception as log_err:
                    logger.warning(
                        (
                            "[LINK_SYNC] Falha ao logar payload de Contato "
                            "#{}: {}"
                        ).format(instance_id, log_err)
                    )

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
                        # Atualização solicitada sem external_id: evita criação implícita
                        # Comentário: evitamos duplicidade. O fluxo de criação ocorre no post_save.
                        msg = "Update ignorado: Contato sem external_id. Aguarde fluxo de criação."
                        logger.warning(msg)
                        try:
                            sync_record.mark_as_failed(msg)
                        except Exception:
                            sync_record.sync_status = "error"
                            sync_record.sync_error = msg
                            sync_record.save()

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
        # Departamento: aguarda external_id dos Fluxos relacionados antes de atualizar
        if model_name == "Departamento" and operation == "update":
            try:
                attempts = 0
                max_attempts = 5
                delay_sec = 1
                from django.db.models import Q

                while attempts < max_attempts:
                    fluxo_syncs = FluxoAtendimentoSync.objects.filter(
                        Q(departamento_sync=sync_record)
                        | Q(fluxo__departamento_id=instance_id)
                    )

                    # Comentário: se não há fluxos, não há o que aguardar
                    if not fluxo_syncs.exists():
                        break

                    pending = any(
                        not getattr(fs, "external_id", None)
                        for fs in fluxo_syncs
                    )

                    if not pending:
                        break

                    attempts += 1
                    time.sleep(delay_sec)
            except Exception as wait_err:
                logger.warning(
                    (
                        "Falha ao aguardar external_id de Fluxos relacionados "
                        "para Departamento #{}: {}"
                    ).format(instance_id, wait_err)
                )

            # Comentário: recalcula propriedades após aguardar os relacionamentos
            try:
                sync_record.prepare_notion_data()
            except Exception as prep_err:
                logger.warning(
                    ("Falha ao preparar dados do Departamento #{}: {}").format(
                        instance_id, prep_err
                    )
                )
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
                        # Atualização solicitada sem external_id: evita criação implícita
                        # Comentário: evitamos duplicidade. O fluxo de criação ocorre no post_save.
                        msg = "Update ignorado: Cliente sem external_id. Aguarde fluxo de criação."
                        logger.warning(msg)
                        try:
                            sync_record.mark_as_failed(msg)
                        except Exception:
                            sync_record.sync_status = "error"
                            sync_record.sync_error = msg
                            sync_record.save()

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
                # Sem external_id em update: evita criação implícita para reduzir duplicidade
                # Comentário: a criação deve ocorrer no fluxo específico de criação (post_save).
                msg = f"Update ignorado: {model_name} #{instance_id} sem external_id."
                logger.warning(msg)
                try:
                    sync_record.mark_as_failed(msg)
                except Exception:
                    sync_record.sync_status = "error"
                    sync_record.sync_error = msg
                    sync_record.save()
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
            elif model_name == "FluxoAtendimento":
                sync_record = FluxoAtendimentoSync.objects.get(
                    fluxo_id=instance_id
                )
            elif model_name == "EtapaFluxo":
                sync_record = EtapaFluxoSync.objects.get(etapa_id=instance_id)
            elif model_name == "MovimentoFluxo":
                sync_record = MovimentoFluxoSync.objects.get(
                    movimento_id=instance_id
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
                # Agenda a sincronização via cluster (Django Q)
                async_task(
                    schedule_sync_operation,
                    "Contato",
                    instance.id,
                    operation,
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
        logger.error(f"Erro ao preparar sync de Contato #{instance.id}: {e}")


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
                # Agenda a sincronização via cluster (Django Q)
                async_task(
                    schedule_sync_operation,
                    "Cliente",
                    instance.id,
                    operation,
                )
                logger.info(
                    "Cliente #{} {} - Sincronização agendada",
                    instance.id,
                    "criado" if created else "atualizado",
                )

                # Além do cliente, agenda atualização dos contatos vinculados
                try:
                    from .models import ContatoSync

                    contatos_rel = list(instance.contatos.all())
                    for contato in contatos_rel:
                        contato_sync = ContatoSync.objects.filter(
                            contato_id=contato.id
                        ).first()
                        if not contato_sync:
                            contato_sync = get_or_create_contato_sync(
                                contato.id
                            )

                        contato_sync.prepare_notion_data()
                        contato_sync.save()

                        # Loga claramente o disparo de atualização do contato
                        # após cadastro/atualização do cliente, incluindo
                        # quantos clientes relacionados serão enviados.
                        try:
                            rel = contato_sync.notion_properties.get(
                                "Clientes Relacionados", {}
                            ).get("relation", [])
                            rel_ids = [str(it.get("id")) for it in rel]
                            logger.info(
                                (
                                    "[LINK_SYNC] post_save(Cliente #{}) → "
                                    "agendando update do Contato #{} "
                                    "(clientes_relacionados={})"
                                ).format(instance.id, contato.id, len(rel_ids))
                            )
                            logger.debug(
                                (
                                    "[LINK_SYNC] IDs de clientes mapeados "
                                    "para Contato #{}: {}"
                                ).format(contato.id, rel_ids)
                            )
                        except Exception as log_err:
                            # Comentário: log falho não deve impedir agendamento
                            logger.warning(
                                (
                                    "[LINK_SYNC] Falha ao logar relação "
                                    "do Contato #{}: {}"
                                ).format(contato.id, log_err)
                            )

                        async_task(
                            schedule_sync_operation,
                            "Contato",
                            contato.id,
                            "update",
                        )
                    if contatos_rel:
                        logger.info(
                            (
                                "Atualizações de Contatos vinculados ao Cliente #{} agendadas"
                            ).format(instance.id)
                        )
                except Exception as e_contato:
                    logger.error(
                        (
                            "Erro ao agendar atualização de contatos vinculados "
                            "para Cliente #{}: {}"
                        ).format(instance.id, e_contato)
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


@receiver(post_save, sender=ClienteSync)
def on_cliente_sync_saved(
    sender: Any, instance: ClienteSync, created: bool, **kwargs: Any
) -> None:
    """
    Dispara atualização dos Contatos vinculados após ClienteSync ser
    marcado como sincronizado.

    Comentário (PT-BR):
    - Este receiver garante o refresh dos relacionamentos "Clientes
      Relacionados" em Contato assim que o `external_id` do Cliente
      estiver disponível (após `mark_as_synced`).
    - É complementar ao fluxo em `on_cliente_saved`, evitando corrida
      quando a criação da página no Notion ainda não forneceu o ID.
    """
    try:
        # Apenas atua quando está efetivamente sincronizado e há external_id
        if instance.sync_status != "synced" or not instance.external_id:
            return

        def _after_commit() -> None:
            """Agenda updates de Contatos vinculados pós-commit.

            Comentário: uso pós-commit para não interferir na transação
            atual e manter simetria com demais receivers do módulo.
            """
            try:
                cliente_obj = instance.cliente
                contatos_rel = list(cliente_obj.contatos.all())

                for contato in contatos_rel:
                    # Garante ContatoSync e payload preparado
                    contato_sync = ContatoSync.objects.filter(
                        contato_id=contato.id
                    ).first()
                    if not contato_sync:
                        contato_sync = get_or_create_contato_sync(contato.id)

                    # Prepara propriedades com relações atualizadas
                    contato_sync.prepare_notion_data()
                    contato_sync.save()

                    # Logging focado no relacionamento clientes → contato
                    try:
                        rel = contato_sync.notion_properties.get(
                            "Clientes Relacionados", {}
                        ).get("relation", [])
                        rel_ids = [str(it.get("id")) for it in rel]
                        logger.info(
                            (
                                "[LINK_SYNC] post_save(ClienteSync -> {}) → "
                                "agendando update do Contato #{} "
                                "(clientes_relacionados={})"
                            ).format(
                                instance.cliente_id, contato.id, len(rel_ids)
                            )
                        )
                        if rel_ids:
                            logger.debug(
                                (
                                    "[LINK_SYNC] IDs de clientes mapeados "
                                    "para Contato #{}: {}"
                                ).format(contato.id, rel_ids)
                            )
                    except Exception as log_err:
                        logger.warning(
                            (
                                "[LINK_SYNC] Falha ao logar relação do "
                                "Contato #{}: {}"
                            ).format(contato.id, log_err)
                        )

                    # Agenda atualização via cluster (Django Q)
                    async_task(
                        schedule_sync_operation,
                        "Contato",
                        contato.id,
                        "update",
                    )

                if contatos_rel:
                    logger.info(
                        (
                            "Atualizações de Contatos pós-sync do Cliente "
                            "#{} agendadas"
                        ).format(instance.cliente_id)
                    )
            except Exception as err:
                logger.error(
                    (
                        "Erro pós-commit no signal de ClienteSync #{}: {}"
                    ).format(instance.cliente_id, err)
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            ("Erro ao processar signal de ClienteSync #{}: {}").format(
                instance.cliente_id, e
            )
        )


@receiver(post_save, sender=AtendenteSync)
def on_atendente_sync_saved(
    sender: Any, instance: AtendenteSync, created: bool, **kwargs: Any
) -> None:
    """
    Dispara atualização do Departamento vinculado após AtendenteSync ser
    marcado como sincronizado.

    Comentário (PT-BR):
    - Espelha o padrão de `on_cliente_sync_saved`, garantindo que a
      propriedade "Atendentes Relacionados" em Departamento seja
      atualizada somente quando o Atendente possuir `external_id`.
    - Usa pós-commit e agendamento via cluster para não interferir na
      transação atual.
    """
    try:
        # Apenas atua quando está efetivamente sincronizado e há external_id
        if instance.sync_status != "synced" or not instance.external_id:
            return

        def _after_commit() -> None:
            """Agenda atualização do Departamento vinculado pós-commit."""
            try:
                from ..ui.operacional.models import Atendente

                dep_id: Optional[int] = None
                try:
                    # Tenta acessar relação direta, se disponível
                    atendente_obj = getattr(instance, "atendente", None)
                    dep_id = (
                        getattr(atendente_obj, "departamento_id", None)
                        if atendente_obj
                        else None
                    )
                except Exception:
                    dep_id = None

                if dep_id is None:
                    try:
                        # Fallback seguro via consulta
                        atendente_obj = Atendente.objects.filter(
                            id=instance.atendente_id
                        ).first()
                        dep_id = (
                            atendente_obj.departamento_id
                            if atendente_obj
                            else None
                        )
                    except Exception as err:
                        logger.warning(
                            (
                                "Falha ao carregar Atendente para "
                                "AtendenteSync #{}: {}"
                            ).format(instance.atendente_id, err)
                        )

                if dep_id:
                    dep_sync = get_or_create_departamento_sync(dep_id)
                    dep_sync.prepare_notion_data()
                    dep_sync.save()
                    # Agenda atualização de Departamento via cluster
                    async_task(
                        schedule_sync_operation,
                        "Departamento",
                        dep_id,
                        "update",
                    )
            except Exception as err:
                logger.error(
                    (
                        "Erro pós-commit no signal de AtendenteSync -> "
                        "Departamento: {}"
                    ).format(err)
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            ("Erro ao processar signal de AtendenteSync #{}: {}").format(
                instance.atendente_id, e
            )
        )


@receiver(post_save, sender=FluxoAtendimento)
def on_fluxo_saved(
    sender: Any, instance: "FluxoAtendimento", created: bool, **kwargs: Any
) -> None:
    """Sincroniza Fluxo e relacionamentos após salvar.

    Comentários:
    - Usa pós-commit para evitar impacto na transação.
    - Agenda atualização do Departamento vinculado e das Etapas do Fluxo.
    """
    if kwargs.get("skip_sync", False):
        logger.debug(
            f"Sincronização ignorada para FluxoAtendimento #{instance.id}"
        )
        return

    try:

        def _after_commit() -> None:
            try:
                # Evita consultas em tabelas não migradas no ambiente local.
                if not _table_exists("notion_sync_fluxo_atendimento"):
                    logger.warning(
                        (
                            "Tabela 'notion_sync_fluxo_atendimento' "
                            "inexistente; ignorando pós-commit para "
                            "Fluxo #{}"
                        ).format(instance.id)
                    )
                    return

                sync_metadata = safe_get_or_create_fluxo_sync(instance.id)
                if not sync_metadata:
                    return
                operation = "create" if created else "update"

                ok_ops = ensure_operacional_configs_ready()
                ok_pipeline = ensure_fluxo_etapas_movimentos_configs_ready()
                if not (ok_ops and ok_pipeline):
                    logger.warning(
                        (
                            "Configs Notion (Operacional/Fluxo Pipeline) "
                            "não prontas. Prosseguindo com tentativa de "
                            "sync assim mesmo."
                        )
                    )

                sync_metadata.prepare_notion_data()
                sync_metadata.save()

                async_task(
                    schedule_sync_operation,
                    "FluxoAtendimento",
                    instance.id,
                    operation,
                )

                # Atualiza Departamento relacionado
                try:
                    dep_id = getattr(instance, "departamento_id", None)
                    if dep_id:
                        dep_sync = safe_get_or_create_departamento_sync(
                            int(dep_id)
                        )
                        if dep_sync:
                            dep_sync.prepare_notion_data()
                            dep_sync.save()
                            async_task(
                                schedule_sync_operation,
                                "Departamento",
                                int(dep_id),
                                "update",
                            )
                except Exception as rel_err:
                    logger.warning(
                        (
                            "Falha ao agendar atualização do Departamento "
                            "vinculado ao Fluxo #{}: {}"
                        ).format(instance.id, rel_err)
                    )

                # Atualiza Etapas pertencentes ao Fluxo
                try:
                    if _table_exists("notion_sync_etapa_fluxo"):
                        etapa_ids = list(
                            EtapaFluxoSync.objects.filter(
                                fluxo_sync__fluxo_id=instance.id
                            ).values_list("etapa_id", flat=True)
                        )
                        for eid in etapa_ids:
                            async_task(
                                schedule_sync_operation,
                                "EtapaFluxo",
                                int(eid),
                                "update",
                            )
                except Exception as rel_err:
                    logger.warning(
                        (
                            "Falha ao agendar atualização das Etapas do "
                            "Fluxo #{}: {}"
                        ).format(instance.id, rel_err)
                    )
            except Exception as err:
                logger.error(
                    "Erro pós-commit no signal de FluxoAtendimento #{}: {}",
                    instance.id,
                    str(err),
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            f"Erro ao preparar sync de FluxoAtendimento #{instance.id}: {e}"
        )


@receiver(post_save, sender=EtapaFluxo)
def on_etapa_fluxo_saved(
    sender: Any, instance: "EtapaFluxo", created: bool, **kwargs: Any
) -> None:
    """Sincroniza Etapa do Fluxo e relacionamentos após salvar.

    Comentários:
    - Atualiza o Fluxo relacionado e Movimentos que referenciam a etapa.
    """
    if kwargs.get("skip_sync", False):
        logger.debug(f"Sincronização ignorada para EtapaFluxo #{instance.id}")
        return

    try:

        def _after_commit() -> None:
            try:
                # Garante criação/obtensão do espelho apenas após o commit
                # para não impactar a transação caso a tabela ainda não exista.
                if not _table_exists("notion_sync_etapa_fluxo"):
                    logger.warning(
                        (
                            "Tabela 'notion_sync_etapa_fluxo' "
                            "inexistente; ignorando pós-commit para "
                            "Etapa #{}"
                        ).format(instance.id)
                    )
                    return

                sync_metadata = safe_get_or_create_etapa_sync(instance.id)
                if not sync_metadata:
                    return
                operation = "create" if created else "update"

                ok_ops = ensure_operacional_configs_ready()
                ok_pipeline = ensure_fluxo_etapas_movimentos_configs_ready()
                if not (ok_ops and ok_pipeline):
                    logger.warning(
                        "Configs Notion (Operacional/Pipeline) não prontas."
                    )

                sync_metadata.prepare_notion_data()
                sync_metadata.save()

                async_task(
                    schedule_sync_operation,
                    "EtapaFluxo",
                    instance.id,
                    operation,
                )

                # Atualiza Fluxo vinculado
                try:
                    fluxo_id = getattr(instance, "fluxo_id", None)
                    if fluxo_id and _table_exists(
                        "notion_sync_fluxo_atendimento"
                    ):
                        fl_sync = safe_get_or_create_fluxo_sync(int(fluxo_id))
                        if fl_sync:
                            fl_sync.prepare_notion_data()
                            fl_sync.save()
                            async_task(
                                schedule_sync_operation,
                                "FluxoAtendimento",
                                int(fluxo_id),
                                "update",
                            )
                except Exception as rel_err:
                    logger.warning(
                        (
                            "Falha ao agendar atualização do Fluxo "
                            "vinculado à Etapa #{}: {}"
                        ).format(instance.id, rel_err)
                    )

                # Atualiza Movimentos que referenciam esta Etapa
                try:
                    mov_ids = list(
                        MovimentoFluxo.objects.filter(
                            etapa_origem_id=instance.id
                        ).values_list("id", flat=True)
                    ) + list(
                        MovimentoFluxo.objects.filter(
                            etapa_destino_id=instance.id
                        ).values_list("id", flat=True)
                    )
                    for mid in set(mov_ids):
                        async_task(
                            schedule_sync_operation,
                            "MovimentoFluxo",
                            int(mid),
                            "update",
                        )
                except Exception as rel_err:
                    logger.warning(
                        (
                            "Falha ao agendar atualização de Movimentos "
                            "ligados à Etapa #{}: {}"
                        ).format(instance.id, rel_err)
                    )
            except Exception as err:
                logger.error(
                    "Erro pós-commit no signal de EtapaFluxo #{}: {}",
                    instance.id,
                    str(err),
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            f"Erro ao preparar sync de EtapaFluxo #{instance.id}: {e}"
        )


@receiver(post_save, sender=MovimentoFluxo)
def on_movimento_fluxo_saved(
    sender: Any, instance: "MovimentoFluxo", created: bool, **kwargs: Any
) -> None:
    """Sincroniza Movimento do Fluxo e itens relacionados.

    Comentários:
    - Agenda atualização de Atendimento, Etapas e Atendentes envolvidos.
    """
    if kwargs.get("skip_sync", False):
        logger.debug(
            f"Sincronização ignorada para MovimentoFluxo #{instance.id}"
        )
        return

    try:

        def _after_commit() -> None:
            try:
                # Adia consultas de criação do espelho para pós-commit, evitando
                # erros de tabela ausente dentro da transação do admin.
                if not _table_exists("notion_sync_movimento_fluxo"):
                    logger.warning(
                        (
                            "Tabela 'notion_sync_movimento_fluxo' "
                            "inexistente; ignorando pós-commit para "
                            "Movimento #{}"
                        ).format(instance.id)
                    )
                    return

                sync_metadata = safe_get_or_create_movimento_sync(instance.id)
                if not sync_metadata:
                    return
                operation = "create" if created else "update"

                ok_ops = ensure_operacional_configs_ready()
                ok_at = ensure_atendimentos_configs_ready()
                ok_pipeline = ensure_fluxo_etapas_movimentos_configs_ready()
                if not (ok_ops and ok_at and ok_pipeline):
                    logger.warning(
                        "Configs Notion base não totalmente prontas. "
                        "Prosseguindo com sync."
                    )

                sync_metadata.prepare_notion_data()
                sync_metadata.save()

                async_task(
                    schedule_sync_operation,
                    "MovimentoFluxo",
                    instance.id,
                    operation,
                )

                # Atualiza itens relacionados
                try:
                    at_id = getattr(instance, "atendimento_id", None)
                    if at_id:
                        async_task(
                            schedule_sync_operation,
                            "Atendimento",
                            int(at_id),
                            "update",
                        )
                    eo_id = getattr(instance, "etapa_origem_id", None)
                    if eo_id:
                        async_task(
                            schedule_sync_operation,
                            "EtapaFluxo",
                            int(eo_id),
                            "update",
                        )
                    ed_id = getattr(instance, "etapa_destino_id", None)
                    if ed_id:
                        async_task(
                            schedule_sync_operation,
                            "EtapaFluxo",
                            int(ed_id),
                            "update",
                        )
                    ao_id = getattr(instance, "atendente_origem_id", None)
                    if ao_id:
                        async_task(
                            schedule_sync_operation,
                            "Atendente",
                            int(ao_id),
                            "update",
                        )
                    ad_id = getattr(instance, "atendente_destino_id", None)
                    if ad_id:
                        async_task(
                            schedule_sync_operation,
                            "Atendente",
                            int(ad_id),
                            "update",
                        )
                except Exception as rel_err:
                    logger.warning(
                        (
                            "Falha ao agendar atualizações relacionadas "
                            "ao Movimento #{}: {}"
                        ).format(instance.id, rel_err)
                    )
            except Exception as err:
                logger.error(
                    "Erro pós-commit no signal de MovimentoFluxo #{}: {}",
                    instance.id,
                    str(err),
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            f"Erro ao preparar sync de MovimentoFluxo #{instance.id}: {e}"
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

        # Prepara dados e agenda atualização do contato via cluster
        sync_record.prepare_notion_data()
        sync_record.save()
        # Agenda após commit para garantir vínculo persistido
        transaction.on_commit(
            lambda cid=instance.id: async_task(
                schedule_sync_operation, "Contato", cid, "update"
            )
        )

        try:
            from .models import ClienteSync

            cliente_ids = list(pk_set or [])
            for cliente_id in cliente_ids:
                cliente_sync = ClienteSync.objects.filter(
                    cliente_id=cliente_id
                ).first()
                if not cliente_sync:
                    cliente_sync = get_or_create_cliente_sync(cliente_id)

                cliente_sync.prepare_notion_data()
                cliente_sync.save()
                # Agenda após commit para garantir vínculo persistido
                transaction.on_commit(
                    lambda clid=cliente_id: async_task(
                        schedule_sync_operation,
                        "Cliente",
                        clid,
                        "update",
                    )
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
        if action in ("post_add", "post_remove", "post_clear"):
            # Primeiro agenda atualização do próprio cliente
            try:
                from .models import ClienteSync

                cliente_sync = ClienteSync.objects.filter(
                    cliente_id=instance.id
                ).first()
                if not cliente_sync:
                    cliente_sync = get_or_create_cliente_sync(instance.id)

                cliente_sync.prepare_notion_data()
                cliente_sync.save()

                transaction.on_commit(
                    lambda cid=instance.id: async_task(
                        schedule_sync_operation,
                        "Cliente",
                        cid,
                        "update",
                    )
                )
            except Exception as e_cliente:
                logger.error(
                    f"Erro ao sincronizar o cliente #{instance.id}: {e_cliente}"
                )

            # Depois agenda atualização dos contatos relacionados
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

                    transaction.on_commit(
                        lambda ctid=contato_obj.id: async_task(
                            schedule_sync_operation,
                            "Contato",
                            ctid,
                            "update",
                        )
                    )
            except Exception as e_inner:
                logger.error(
                    f"Erro ao sincronizar contatos impactados "
                    f"(Cliente #{instance.id}): {e_inner}"
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

        def _after_commit() -> None:
            """Executa bootstrap/construct e agenda sync após commit.

            Comentário: evita IO pesado e criação de bases dentro
            da transação; segue padrão usado em Clientes/Contatos.
            """
            try:
                ok_ready = ensure_operacional_configs_ready()
                if not ok_ready:
                    logger.warning(
                        "Config Notion Operacional ainda não pronta."
                    )

                sync.prepare_notion_data()
                sync.save()

                try:
                    _bootstrap_uds_for_departamento(sync.config)
                except Exception as exc:
                    logger.warning(
                        "Falha no bootstrap UDS para Departamento #{}: {}",
                        instance.id,
                        str(exc),
                    )
                # Agenda a sincronização via cluster (Django Q),
                # mantendo simetria com Contato/Cliente
                async_task(
                    schedule_sync_operation,
                    "Departamento",
                    instance.id,
                    "create" if created else "update",
                )

                # Agenda atualização dos Fluxos vinculados ao Departamento,
                # garantindo espelho da relação 1:N (Dep → Fluxos) no Notion.
                try:
                    fluxo_ids = list(
                        FluxoAtendimento.objects.filter(
                            departamento_id=instance.id
                        ).values_list("id", flat=True)
                    )
                    for fid in fluxo_ids:
                        async_task(
                            schedule_sync_operation,
                            "FluxoAtendimento",
                            int(fid),
                            "update",
                        )
                except Exception as rel_err:
                    logger.warning(
                        (
                            "Falha ao agendar atualização dos Fluxos do "
                            "Departamento #{}: {}"
                        ).format(instance.id, rel_err)
                    )
            except Exception as inner:
                logger.error(
                    (
                        "Erro pós-commit ao processar Departamento #{}: {}"
                    ).format(instance.id, inner)
                )

        transaction.on_commit(_after_commit)

    except Exception as exc:
        logger.error(
            f"Erro ao preparar sync do departamento {instance.id}: {exc}"
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

        def _after_commit() -> None:
            """Executa bootstrap/construct e agenda sync após commit."""
            try:
                ok_ready = ensure_operacional_configs_ready()
                if not ok_ready:
                    logger.warning(
                        "Config Notion Operacional ainda não pronta."
                    )

                sync.prepare_notion_data()
                sync.save()

                try:
                    _bootstrap_uds_for_atendente(sync.config)
                except Exception as exc:
                    logger.warning(
                        "Falha no bootstrap UDS para Atendente #{}: {}",
                        instance.id,
                        str(exc),
                    )
                # Agenda a sincronização via cluster (Django Q),
                # mantendo simetria com Contato/Cliente
                async_task(
                    schedule_sync_operation,
                    "Atendente",
                    instance.id,
                    "create" if created else "update",
                )

                # Atualização de Departamentos relacionados
                try:
                    prev_id = getattr(
                        instance, "_original_departamento_id", None
                    )
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
                            # Agenda atualização de Departamento via cluster
                            async_task(
                                schedule_sync_operation,
                                "Departamento",
                                dep_id,
                                "update",
                            )
                        except Exception as e:
                            logger.error(
                                "Erro ao atualizar Departamento vinculado "
                                f"#{dep_id}: {e}"
                            )
                except Exception as e_dep:
                    logger.error(
                        "Erro ao processar atualização de departamentos "
                        f"relacionados para atendente #{instance.id}: {e_dep}"
                    )
            except Exception as inner:
                logger.error(
                    ("Erro pós-commit ao processar Atendente #{}: {}").format(
                        instance.id, inner
                    )
                )

        transaction.on_commit(_after_commit)

    except Exception as exc:
        logger.error(
            f"Erro ao preparar sync do atendente {instance.id}: {exc}"
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
                # Agenda atualização de Departamento via cluster (Django Q)
                async_task(
                    schedule_sync_operation,
                    "Departamento",
                    dep_id,
                    "update",
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
        logger.info(
            f"[SIGNAL_DEBUG] Signal de atendimento disparado para #{instance.id} (created={created})"
        )
        logger.info(
            f"[SIGNAL_DEBUG] Contexto da conversa no signal: {instance.contexto_conversa}"
        )

        # Usa pós-commit para evitar IO pesado dentro da transação
        def _after_commit() -> None:
            """Garante configs Notion, prepara dados e agenda sync via cluster."""
            try:
                # Garante que todas as configs necessárias existam/prontas
                ok_ops = ensure_operacional_configs_ready()
                if not ok_ops:
                    logger.warning(
                        "Config Notion Operacional ainda não pronta."
                    )

                ok_cli = ensure_clientes_configs_ready()
                if not ok_cli:
                    logger.warning(
                        "Config Notion de Clientes/Contatos ainda não pronta."
                    )

                ok_at = ensure_atendimentos_configs_ready()
                if not ok_at:
                    logger.warning(
                        "Config Notion de Atendimentos/Mensagens ainda não pronta."
                    )

                # Obtém/Cria metadados de sincronização
                sync_metadata = get_or_create_atendimento_sync(instance.id)
                operation = "create" if created else "update"

                # Prepara e salva dados formatados para Notion
                sync_metadata.prepare_notion_data()
                sync_metadata.save()

                # Agenda sincronização via cluster (Django Q)
                async_task(
                    schedule_sync_operation,
                    "Atendimento",
                    instance.id,
                    operation,
                )
                logger.info(
                    f"[SIGNAL_DEBUG] Atendimento #{instance.id} {operation} - sync agendada via cluster"
                )

                # Se já existirem mensagens vinculadas, agenda atualização delas
                try:
                    from .models import MensagemSync

                    rel_msgs = MensagemSync.objects.filter(
                        atendimento_sync__atendimento_id=instance.id
                    ).values_list("mensagem_id", flat=True)
                    for msg_id in rel_msgs:
                        async_task(
                            schedule_sync_operation,
                            "Mensagem",
                            int(msg_id),
                            "update",
                        )
                    if rel_msgs:
                        logger.info(
                            f"[SIGNAL_DEBUG] Atualizações de Mensagens relacionadas agendadas ({len(rel_msgs)})"
                        )
                except Exception as rel_err:
                    logger.warning(
                        f"[SIGNAL_DEBUG] Falha ao agendar atualizações de mensagens relacionadas: {rel_err}"
                    )
            except Exception as e:
                logger.error(
                    f"Erro pós-commit ao processar Atendimento #{instance.id}: {e}",
                    exc_info=True,
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Atendimento #{instance.id}: {e}",
            exc_info=True,
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
        # Usa pós-commit para evitar IO pesado dentro da transação
        def _after_commit() -> None:
            """Garante configs Notion, agenda Mensagem e espelha relação no Atendimento."""
            try:
                # Garantir que bases de Atendimentos/Mensagens existem
                ok_at = ensure_atendimentos_configs_ready()
                if not ok_at:
                    logger.warning(
                        "Config Notion de Atendimentos/Mensagens ainda não pronta."
                    )

                # Sincroniza a mensagem (criação ou atualização)
                sync_metadata = get_or_create_mensagem_sync(instance.id)
                sync_metadata.prepare_notion_data()
                sync_metadata.save()

                # Assegura que o atendimento pai tenha external_id antes de criar a mensagem
                if instance.atendimento:
                    at_sync = get_or_create_atendimento_sync(
                        instance.atendimento.id
                    )
                    at_op = "create" if not at_sync.external_id else "update"
                    at_sync.prepare_notion_data()
                    at_sync.save()
                    async_task(
                        schedule_sync_operation,
                        "Atendimento",
                        instance.atendimento.id,
                        at_op,
                    )

                # Define operação para a Mensagem e agenda via cluster
                op = "create" if created else "update"
                async_task(
                    schedule_sync_operation,
                    "Mensagem",
                    instance.id,
                    op,
                )
                logger.info(
                    f"Mensagem {op.lower()}izada: #{instance.id} (agendada via cluster)"
                )

                # Sempre atualizar o atendimento após a mensagem para espelhar relação
                if instance.atendimento:
                    async_task(
                        schedule_sync_operation,
                        "Atendimento",
                        instance.atendimento.id,
                        "update",
                    )
                    logger.info(
                        f"Atendimento #{instance.atendimento.id} atualizado para espelhar 'Mensagens Relacionadas'"
                    )
            except Exception as e:
                logger.error(
                    f"Erro pós-commit ao processar Mensagem #{instance.id}: {e}",
                    exc_info=True,
                )

        transaction.on_commit(_after_commit)
    except Exception as e:
        logger.error(
            f"Erro ao processar signal de Mensagem #{instance.id}: {e}",
            exc_info=True,
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

        # Construir bases via cluster (Django Q)
        try:
            async_task(cluster_bootstrap_clientes_minimal)
            logger.info(
                "Bootstraps de Clientes/Contatos agendados no cluster."
            )
            # Revalidar (retorna False até concluir)
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


def ensure_operacional_configs_ready() -> bool:
    """Garante que as configs Operacionais (Departamentos/Atendentes) existam.

    Comentário (PT-BR):
    - Retorna True se ambas as configs estão prontas para sync.
    - Caso contrário, constrói as databases via construtor assíncrono
      e salva no `NotionDatabaseConfig`.
    """
    try:
        dep_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_operacional_departamento"
        ).first()
        at_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_operacional_atendente"
        ).first()

        if (
            dep_cfg
            and at_cfg
            and dep_cfg.is_ready_for_sync()
            and at_cfg.is_ready_for_sync()
        ):
            return True

        try:
            # Agenda o bootstrap operacional no cluster
            async_task(cluster_bootstrap_operacional_minimal)
            logger.info("Bootstraps Operacionais agendados no cluster.")

            # Revalidar (retorna False até concluir)
            dep_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_departamento"
            ).first()
            at_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_atendente"
            ).first()
            return bool(
                dep_cfg
                and at_cfg
                and dep_cfg.is_ready_for_sync()
                and at_cfg.is_ready_for_sync()
            )
        except Exception as exc:
            logger.error(
                f"Erro ao construir bases Notion (Operacional): {exc}"
            )
            return False
    except Exception as outer:
        logger.error(
            f"Falha ao verificar/garantir configs Operacionais: {outer}"
        )
        return False


def ensure_atendimentos_configs_ready() -> bool:
    """Garante que configs de Atendimentos/Mensagens existam e estejam prontas.

    Comentário (PT-BR):
    - Retorna True se ambas as configs estão prontas para sincronização.
    - Caso contrário, constrói databases mínimas via serviço de bootstrap e
      salva no `NotionDatabaseConfig`, revalidando ao final.
    """
    try:
        at_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_atendimentos_atendimento"
        ).first()
        msg_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_atendimentos_mensagem"
        ).first()

        if (
            at_cfg
            and msg_cfg
            and at_cfg.is_ready_for_sync()
            and msg_cfg.is_ready_for_sync()
        ):
            logger.info(
                "Configs de Atendimentos/Mensagens já prontas para sync."
            )
            return True

        try:
            # Agenda o bootstrap de Atendimentos/Mensagens no cluster
            async_task(cluster_bootstrap_atendimentos_minimal)
            logger.info(
                ("Bootstraps de Atendimentos/Mensagens agendados no cluster.")
            )

            # Revalidar (retorna False até concluir)
            at_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_atendimentos_atendimento"
            ).first()
            msg_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_atendimentos_mensagem"
            ).first()
            ready = bool(
                at_cfg
                and msg_cfg
                and at_cfg.is_ready_for_sync()
                and msg_cfg.is_ready_for_sync()
            )
            logger.info(
                (
                    "Prontidão após bootstrap: atendimentos_ready={} "
                    "mensagens_ready={}"
                ).format(
                    bool(at_cfg and at_cfg.is_ready_for_sync()),
                    bool(msg_cfg and msg_cfg.is_ready_for_sync()),
                )
            )
            return ready
        except Exception as exc:
            logger.error(
                f"Erro ao construir bases Notion (Atendimentos): {exc}"
            )
            return False
    except Exception as outer:
        logger.error(
            f"Falha ao verificar/garantir configs Atendimentos: {outer}"
        )
        return False


def ensure_fluxo_etapas_movimentos_configs_ready() -> bool:
    """Garante configs para Fluxo/Etapas/Movimentos prontas para sync.

    Comentário (PT-BR):
    - Depende das bases Operacionais (Departamentos/Atendentes) e
      de Atendimentos, pois Movimentos relaciona-se com ambas.
    - Se Etapas/Movimentos não existirem, cria databases mínimas e
      salva configs via serviço de bootstrap.
    """
    try:
        # Garantir bases necessárias antes
        ok_ops = ensure_operacional_configs_ready()
        ok_at = ensure_atendimentos_configs_ready()
        if not (ok_ops and ok_at):
            logger.warning(
                "Operacional/Atendimentos não prontos; tentando bootstrap "
                "de Fluxo/Etapas/Movimentos mesmo assim."
            )

        et_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_operacional_etapa_fluxo"
        ).first()
        mv_cfg = NotionDatabaseConfig.objects.filter(
            slug="ui_operacional_movimento_fluxo"
        ).first()

        if (
            et_cfg
            and mv_cfg
            and et_cfg.is_ready_for_sync()
            and mv_cfg.is_ready_for_sync()
        ):
            return True

        try:
            # Agenda bootstrap de Fluxo/Etapas/Movimentos no cluster
            async_task(cluster_bootstrap_fluxo_etapas_movimentos_minimal)
            logger.info(
                ("Bootstraps de Fluxo/Etapas/Movimentos agendados no cluster.")
            )

            # Revalida após bootstrap
            et_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_etapa_fluxo"
            ).first()
            mv_cfg = NotionDatabaseConfig.objects.filter(
                slug="ui_operacional_movimento_fluxo"
            ).first()
            return bool(
                et_cfg
                and mv_cfg
                and et_cfg.is_ready_for_sync()
                and mv_cfg.is_ready_for_sync()
            )
        except Exception as exc:
            logger.error(
                (
                    "Erro ao construir bases Notion (Fluxo/Etapas/"
                    "Movimentos): {}"
                ).format(exc)
            )
            return False
    except Exception as outer:
        logger.error(
            (
                "Falha ao garantir configs Notion (Fluxo/Etapas/Movimentos): "
                "{}"
            ).format(outer)
        )
        return False


def _table_exists(table_name: str) -> bool:
    """Verifica se uma tabela existe no banco atual.

    Comentário:
    - Usa introspecção do Django para evitar consultas em
      tabelas inexistentes que abortam a transação.
    """
    try:
        return table_name in connection.introspection.table_names()
    except Exception as err:
        logger.warning(
            "Falha ao verificar existência da tabela '{}': {}",
            table_name,
            str(err),
        )
        return False


def safe_get_or_create_fluxo_sync(
    fluxo_id: int,
) -> Optional[FluxoAtendimentoSync]:
    """Obtém/cria FluxoAtendimentoSync apenas se a tabela existir."""
    if not _table_exists("notion_sync_fluxo_atendimento"):
        logger.warning(
            (
                "Tabela 'notion_sync_fluxo_atendimento' ausente; "
                "pulando criação de espelho do Fluxo #{}"
            ).format(fluxo_id)
        )
        return None
    return get_or_create_fluxo_sync(fluxo_id)


def safe_get_or_create_etapa_sync(
    etapa_id: int,
) -> Optional[EtapaFluxoSync]:
    """Obtém/cria EtapaFluxoSync apenas se a tabela existir."""
    if not _table_exists("notion_sync_etapa_fluxo"):
        logger.warning(
            (
                "Tabela 'notion_sync_etapa_fluxo' ausente; "
                "pulando criação de espelho da Etapa #{}"
            ).format(etapa_id)
        )
        return None
    return get_or_create_etapa_sync(etapa_id)


def safe_get_or_create_movimento_sync(
    movimento_id: int,
) -> Optional[MovimentoFluxoSync]:
    """Obtém/cria MovimentoFluxoSync apenas se a tabela existir."""
    if not _table_exists("notion_sync_movimento_fluxo"):
        logger.warning(
            (
                "Tabela 'notion_sync_movimento_fluxo' ausente; "
                "pulando criação de espelho do Movimento #{}"
            ).format(movimento_id)
        )
        return None
    return get_or_create_movimento_sync(movimento_id)


def safe_get_or_create_departamento_sync(
    departamento_id: int,
) -> Optional[DepartamentoSync]:
    """Obtém/cria DepartamentoSync apenas se a tabela existir."""
    if not _table_exists("notion_sync_departamento"):
        logger.warning(
            (
                "Tabela 'notion_sync_departamento' ausente; "
                "pulando criação de espelho do Departamento #{}"
            ).format(departamento_id)
        )
        return None
    return get_or_create_departamento_sync(departamento_id)


def cluster_bootstrap_clientes_minimal() -> None:
    """Executa bootstrap mínimo de Clientes/Contatos no cluster."""
    try:
        from .services.bootstrap_clientes import (
            NotionClientesBootstrapService,
        )

        bootstrap = NotionClientesBootstrapService()
        async_to_sync(bootstrap.construct_minimal)()
        logger.info("Bootstraps de Clientes/Contatos concluídos no cluster.")
    except Exception as err:
        logger.error(
            ("Falha no bootstrap de Clientes/Contatos (cluster): {}").format(
                err
            )
        )


def cluster_bootstrap_operacional_minimal() -> None:
    """Executa bootstrap mínimo de Operacional no cluster."""
    try:
        from .services.bootstrap_operacional import (
            NotionOperacionalBootstrapService,
        )

        bootstrap = NotionOperacionalBootstrapService()
        async_to_sync(bootstrap.construct_minimal)()
        logger.info("Bootstraps Operacionais concluídos no cluster.")
    except Exception as err:
        logger.error(
            "Falha no bootstrap Operacional (cluster): {}".format(err)
        )


def cluster_bootstrap_atendimentos_minimal() -> None:
    """Executa bootstrap mínimo de Atendimentos/Mensagens no cluster."""
    try:
        from .services.bootstrap_atendimentos import (
            NotionAtendimentosBootstrapService,
        )

        bootstrap = NotionAtendimentosBootstrapService()
        async_to_sync(bootstrap.construct_minimal)()
        logger.info(
            ("Bootstraps de Atendimentos/Mensagens concluídos no cluster.")
        )
    except Exception as err:
        logger.error(
            (
                "Falha no bootstrap de Atendimentos/Mensagens (cluster): {}"
            ).format(err)
        )


@receiver(pre_delete, sender=FluxoAtendimento)
def on_fluxo_pre_delete(
    sender: type[FluxoAtendimento], instance: FluxoAtendimento, **kwargs: Any
) -> None:
    """
    Signal disparado antes de excluir um Fluxo de Atendimento.

    - Arquiva a página no Notion (se houver `external_id`).
    - Agenda atualização do Departamento vinculado para remover relação.
    """
    logger.info(f"FluxoAtendimento para exclusão: {instance.nome}")

    try:
        sync_record = FluxoAtendimentoSync.objects.filter(
            fluxo_id=instance.id
        ).first()

        if sync_record and sync_record.external_id:
            service = NotionSyncService()
            service.delete_record(
                "FluxoAtendimento", str(sync_record.external_id)
            )
            logger.info(
                (
                    "FluxoAtendimento #{} arquivado no Notion "
                    "(external_id: {})"
                ).format(instance.id, sync_record.external_id)
            )
        else:
            logger.warning(
                (
                    "FluxoAtendimento #{} não possui external_id "
                    "para arquivar no Notion"
                ).format(instance.id)
            )

        # Atualiza Departamento relacionado para refletir remoção do Fluxo
        try:
            dep_id = getattr(instance, "departamento_id", None)
            if dep_id:
                dep_sync = get_or_create_departamento_sync(int(dep_id))
                dep_sync.prepare_notion_data()
                dep_sync.save()
                async_task(
                    schedule_sync_operation,
                    "Departamento",
                    int(dep_id),
                    "update",
                )
        except Exception as e:
            logger.error(
                (
                    "Erro ao atualizar Departamento após exclusão do "
                    "FluxoAtendimento #{}: {}"
                ).format(instance.id, e)
            )

    except Exception as exc:
        logger.error(
            ("Erro ao processar exclusão de FluxoAtendimento #{}: {}").format(
                instance.id, exc
            )
        )


def cluster_bootstrap_fluxo_etapas_movimentos_minimal() -> None:
    """Executa bootstrap mínimo de Fluxo/Etapas/Movimentos no cluster."""
    try:
        from .services.bootstrap_fluxo_etapas_movimentos import (
            NotionFluxoEtapasMovimentosBootstrapService,
        )

        bootstrap = NotionFluxoEtapasMovimentosBootstrapService()
        async_to_sync(bootstrap.construct_minimal)()
        logger.info(
            ("Bootstraps de Fluxo/Etapas/Movimentos concluídos no cluster.")
        )
    except Exception as err:
        logger.error(
            (
                "Falha no bootstrap de Fluxo/Etapas/Movimentos (cluster): {}"
            ).format(err)
        )
