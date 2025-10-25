"""
Models do app notion_sync para integração com plataforma Notion.

Este módulo implementa a estrutura de dados necessária para sincronização
bidirecional entre models Django e databases/pages do Notion, seguindo
a arquitetura de shadow models e mapeamento de dados.
"""
import re
from datetime import datetime
from typing import Any, Type, override

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Import pgvector for vector support
try:
    from pgvector.django import VectorExtension, VectorField
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback for when pgvector is not available
    class VectorField(models.Field):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    class VectorExtension:
        pass


class SyncConfig(models.Model):
    """
    Configurações gerais de sincronização.

    Armazena configurações globais que afetam todo o sistema de
    sincronização com o Notion.
    """

    key: models.CharField = models.CharField(
        max_length=100,
        unique=True,
        help_text="Chave única da configuração"
    )

    value: models.TextField = models.TextField(
        help_text="Valor da configuração"
    )

    description: models.TextField = models.TextField(
        blank=True,
        help_text="Descrição da configuração"
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação"
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização"
    )

    class Meta:
        verbose_name = "Configuração de Sincronização"
        verbose_name_plural = "Configurações de Sincronização"
        ordering = ["key"]
        db_table = "notion_sync_config"

    @override
    def __str__(self) -> str:
        return f"{self.key}: {self.value}"

    def get_value(self, default: Any = None) -> Any:
        """
        Retorna o valor convertido da configuração.

        Args:
            default: Valor padrão caso não exista.

        Returns:
            Valor convertido ou default.
        """
        # Implementação básica - pode ser expandida para tipos específicos
        return self.value or default

    def set_value(self, value: Any) -> None:
        """
        Define o valor da configuração.

        Args:
            value: Novo valor.
        """
        self.value = str(value)
        self.save()


class NotionDatabaseConfig(models.Model):
    """
    Configuração central dos artefatos do Notion.

    Cada instância representa uma database ou página no Notion que será
    sincronizada com um modelo Django específico.

    Funciona como o coração da integração, centralizando todos os
    IDs e configurações necessárias para a comunicação com a API Notion.
    """

    # Identificação Única
    slug: models.CharField = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Identificador único para referência no código"
    )

    name: models.CharField = models.CharField(
        max_length=200,
        help_text="Nome descritivo da database/página no Notion"
    )

    description: models.TextField = models.TextField(
        blank=True,
        help_text="Descrição detalhada do uso desta configuração"
    )

    # Configuração Notion (API 2025-09-03)
    notion_database_id: models.UUIDField = models.UUIDField(
        help_text="ID da database no Notion (formato UUID)"
    )

    data_source_id: models.UUIDField = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID do data source (API v2025-09-03)"
    )

    notion_page_id: models.UUIDField = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID da página principal (opcional, para hierarquias)"
    )

    # Mapeamento Django
    django_model: models.CharField = models.CharField(
        max_length=100,
        help_text="Modelo Django correspondente (app.Model)"
    )

    django_app_label: models.CharField = models.CharField(
        max_length=50,
        help_text="App Django onde o modelo está definido"
    )

    notion_schema: models.JSONField = models.JSONField(
        default=dict,
        help_text="Schema completo das propriedades do Notion"
    )

    field_mappings: models.JSONField = models.JSONField(
        default=dict,
        help_text="Mapeamento campo_django → campo_notion"
    )

    # Configurações de Sincronização
    sync_enabled: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Habilita/desabilita sincronização"
    )

    sync_direction: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('bidirectional', 'Bidirecional'),
            ('django_to_notion', 'Django → Notion'),
            ('notion_to_django', 'Notion → Django'),
        ],
        default='bidirectional',
        help_text="Direção da sincronização"
    )

    sync_priority: models.IntegerField = models.IntegerField(
        default=5,
        choices=[
            (1, 'Baixa'),
            (3, 'Média'),
            (5, 'Normal'),
            (7, 'Alta'),
            (10, 'Crítica'),
        ],
        help_text="Prioridade na fila de sincronização"
    )

    auto_sync: models.BooleanField = models.BooleanField(
        default=True,
        help_text="Sincroniza automaticamente após alterações"
    )

    batch_sync_enabled: models.BooleanField = models.BooleanField(
        default=False,
        help_text="Permite sincronização em lote"
    )

    batch_size: models.IntegerField = models.IntegerField(
        default=50,
        help_text="Tamanho do lote para sincronização em batch"
    )

    # Controle
    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True
    )

    metadata: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais e configurações customizadas"
    )

    class Meta:
        verbose_name = "Configuração Notion"
        verbose_name_plural = "Configurações Notion"
        ordering = ['sync_priority', 'slug']
        db_table = "notion_database_config"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['django_model']),
            models.Index(fields=['sync_enabled']),
            models.Index(fields=['sync_priority']),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.name} ({self.django_model})"

    def get_django_model_class(self) -> Type[models.Model]:
        """
        Retorna a classe do modelo Django configurado.

        Returns:
            Classe do modelo Django.

        Raises:
            ValueError: Se o modelo não for encontrado.
        """
        try:
            return apps.get_model(
                self.django_app_label,
                self.django_model.split('.')[-1]
            )
        except LookupError as exc:
            raise ValueError(f"Modelo {self.django_model} não encontrado") from exc

    def is_ready_for_sync(self) -> bool:
        """
        Verifica se está pronto para sincronização.

        Returns:
            True se pronto para sincronizar.
        """
        return (
            self.sync_enabled and
            self.notion_database_id and
            self.data_source_id
        )

    @classmethod
    def get_database_id(cls, model_name: str) -> str | None:
        """
        Obtém o database ID para um modelo Django (método legado).

        Args:
            model_name: Nome do modelo Django.

        Returns:
            Database ID do Notion ou None se não encontrado.
        """
        try:
            config = cls.objects.filter(
                django_model__icontains=model_name,
                sync_enabled=True
            ).first()
            return str(config.notion_database_id) if config else None
        except cls.DoesNotExist:
            return None

    @classmethod
    def set_database(
        cls,
        model_name: str,
        database_id: str,
        database_name: str,
        properties_schema: dict[str, Any] | None = None
    ) -> "NotionDatabaseConfig":
        """
        Define ou atualiza a configuração de database para um modelo (método legado).

        Args:
            model_name: Nome do modelo Django.
            database_id: ID do database no Notion.
            database_name: Nome do database no Notion.
            properties_schema: Schema das propriedades.

        Returns:
            Instância da configuração criada ou atualizada.
        """
        # Extrai app_label do model_name se no formato app.Model
        if '.' in model_name:
            app_label, model = model_name.split('.', 1)
        else:
            app_label = 'unknown'
            model = model_name

        slug = f"{app_label}_{model.lower()}"

        config, created = cls.objects.update_or_create(
            slug=slug,
            defaults={
                "name": database_name,
                "notion_database_id": database_id,
                "django_model": model_name,
                "django_app_label": app_label,
                "notion_schema": properties_schema or {},
                "sync_enabled": True,
            }
        )
        return config


class NotionObjectMapping(models.Model):
    """
    Mapeamento entre objetos Django e páginas do Notion.

    Armazena o relacionamento entre registros locais e suas
    representações no Notion para localização rápida.
    """

    # Identificação
    local_model: models.CharField = models.CharField(
        max_length=100,
        help_text="Modelo Django (app.Model)"
    )

    local_id: models.IntegerField = models.IntegerField(
        help_text="ID do registro local"
    )

    external_id: models.CharField = models.CharField(
        max_length=36,
        db_index=True,
        help_text="ID da página no Notion"
    )

    # Configuração
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='object_mappings',
        help_text="Configuração utilizada"
    )

    # Controle
    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Mapeamento Notion"
        verbose_name_plural = "Mapeamentos Notion"
        unique_together = ['local_model', 'local_id']
        db_table = "notion_object_mapping"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['local_model', 'local_id']),
            models.Index(fields=['config']),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.local_model}#{self.local_id} → {self.external_id[:8]}..."

    @classmethod
    def get_by_external_id(cls, external_id: str) -> "NotionObjectMapping | None":
        """
        Obtém mapeamento pelo ID externo.

        Args:
            external_id: ID no Notion.

        Returns:
            Instância do mapeamento ou None.
        """
        try:
            return cls.objects.get(external_id=external_id)
        except cls.DoesNotExist:
            return None


class SyncLog(models.Model):
    """
    Log detalhado de operações de sincronização.

    Registra todas as tentativas de sincronização com sucesso,
    erros e informações detalhadas para debugging.
    """

    # Operação
    operation_type: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('create', 'Criação'),
            ('update', 'Atualização'),
            ('delete', 'Exclusão'),
            ('sync', 'Sincronização'),
        ],
        help_text="Tipo da operação"
    )

    model_name: models.CharField = models.CharField(
        max_length=100,
        help_text="Modelo Django (app.Model)"
    )

    object_id: models.IntegerField = models.IntegerField(
        help_text="ID do objeto local"
    )

    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        help_text="ID do objeto no Notion"
    )

    # Status
    status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('processing', 'Processando'),
            ('success', 'Sucesso'),
            ('error', 'Erro'),
            ('cancelled', 'Cancelado'),
        ],
        default='pending',
        help_text="Status da operação"
    )

    message: models.TextField = models.TextField(
        blank=True,
        help_text="Mensagem descritiva"
    )

    error_details: models.JSONField = models.JSONField(
        null=True,
        blank=True,
        help_text="Detalhes do erro (JSON)"
    )

    request_data: models.JSONField = models.JSONField(
        null=True,
        blank=True,
        help_text="Dados enviados na requisição"
    )

    response_data: models.JSONField = models.JSONField(
        null=True,
        blank=True,
        help_text="Dados recebidos na resposta"
    )

    # Configuração
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sync_logs',
        help_text="Configuração utilizada"
    )

    # Timing
    started_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Início da operação"
    )

    completed_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Término da operação"
    )

    duration_ms: models.IntegerField = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duração em milissegundos"
    )

    metadata: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais"
    )

    created_at: models.DateTimeField = models.DateTimeField(
        default=timezone.now,
        help_text="Data de criação do log"
    )

    class Meta:
        verbose_name = "Log de Sincronização"
        verbose_name_plural = "Logs de Sincronização"
        ordering = ['-created_at']
        db_table = "notion_sync_log"
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['status']),
            models.Index(fields=['external_id']),
            models.Index(fields=['started_at']),
            models.Index(fields=['model_name', 'status']),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.operation_type} {self.model_name}#{self.object_id} - {self.status}"

    def status_emoji(self) -> str:
        """
        Retorna emoji representativo do status.

        Returns:
            Emoji do status.
        """
        emojis = {
            'pending': '⏳',
            'processing': '🔄',
            'success': '✅',
            'error': '❌',
            'cancelled': '🚫',
        }
        return emojis.get(self.status, '❓')

    def get_context_info(self) -> str:
        """
        Retorna informações de contexto do log.

        Returns:
            String com informações contextuais.
        """
        parts = [f"{self.operation_type}"]
        if self.external_id:
            parts.append(f"ID: {self.external_id[:8]}...")
        if self.duration_ms:
            parts.append(f"{self.duration_ms}ms")
        return " - ".join(parts)

    def log_operation(
        self,
        operation_type: str,
        model_name: str,
        object_id: int,
        status: str = 'pending',
        message: str = '',
        external_id: str | None = None,
        config: NotionDatabaseConfig | None = None
    ) -> None:
        """
        Registra uma operação de sincronização (método legado).

        Args:
            operation_type: Tipo da operação.
            model_name: Nome do modelo.
            object_id: ID do objeto.
            status: Status inicial.
            message: Mensagem descritiva.
            external_id: ID externo.
            config: Configuração utilizada.
        """
        self.operation_type = operation_type
        self.model_name = model_name
        self.object_id = object_id
        self.status = status
        self.message = message
        self.external_id = external_id
        self.config = config
        self.started_at = timezone.now()
        self.save()


class ContatoSyncManager(models.Manager):
    """
    Manager customizado para ContatoSync com métodos de consulta específicos.
    """

    def pending_sync(self) -> "models.QuerySet[ContatoSync]":
        """
        Retorna contatos pendentes de sincronização.

        Returns:
            QuerySet com contatos pendentes.
        """
        return self.filter(
            sync_status__in=['pending', 'error'],
            config__sync_enabled=True
        )

    def with_sync_errors(self) -> "models.QuerySet[ContatoSync]":
        """
        Retorna contatos com erros de sincronização.

        Returns:
            QuerySet com contatos com erros.
        """
        return self.filter(
            sync_status='error',
            sync_error__isnull=False
        )

    def needs_sync(self) -> "models.QuerySet[ContatoSync]":
        """
        Retorna contatos que precisam ser sincronizados.

        Returns:
            QuerySet com contatos que precisam de sync.
        """
        from django.db.models import Q

        return self.filter(
            Q(sync_status__in=['pending', 'error']) |
            Q(
                sync_status='synced',
                last_sync_at__lt=models.F('contato__updated_at')
            ),
            config__sync_enabled=True
        )


class ContatoSync(models.Model):
    """
    Espelho do modelo Contato para integração com Notion.

    Contém dados pré-processados e formatados para compatibilidade
    com as propriedades do Notion, incluindo o ID externo para
    localização exata.
    """

    # Relação com Modelo Original
    contato = models.OneToOneField(
        "clientes.Contato",
        on_delete=models.CASCADE,
        related_name='notion_sync',
        help_text="Referência ao contato original"
    )

    # ID Externo (Principal para Localização)
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion (UUID sem dashes)"
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='contato_syncs',
        help_text="Configuração Notion para este modelo"
    )

    # Dados Pré-processados (Formatados para Notion)
    nome_formatado: models.CharField = models.CharField(
        max_length=200,
        help_text="Nome já formatado e validado para o Notion"
    )

    nome_formatado: models.CharField = models.CharField(
        max_length=200,
        help_text="Nome já formatado e validado para o Notion"
    )

    email_normalizado: models.EmailField = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
        help_text="Email validado e normalizado"
    )

    telefone_formatado: models.CharField = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Telefone no formato internacional (+55XX999999999)"
    )

    principal: models.BooleanField = models.BooleanField(
        default=False,
        help_text="É contato principal do cliente?"
    )

    tags_formatadas: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags formatadas para select/multi-select do Notion"
    )

    notion_properties: models.JSONField = models.JSONField(
        default=dict,
        help_text="Propriedades completas formatadas para API Notion"
    )

    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro'),
            ('disabled', 'Desabilitado'),
        ],
        default='pending',
        help_text="Status atual da sincronização"
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora da última sincronização"
    )

    sync_error: models.TextField = models.TextField(
        null=True,
        blank=True,
        help_text="Detalhes do último erro de sincronização"
    )

    retry_count: models.IntegerField = models.IntegerField(
        default=0,
        help_text="Número de tentativas de sincronização"
    )

    sync_metadata: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais sobre a sincronização"
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    # Manager
    objects = ContatoSyncManager()

    class Meta:
        verbose_name = "Contato Sync"
        verbose_name_plural = "Contatos Sync"
        ordering = ['contato__nome_contato']
        db_table = "notion_sync_contato"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['contato']),
            models.Index(fields=['last_sync_at']),
            models.Index(fields=['sync_status', 'config']),
        ]

    @override
    def __str__(self) -> str:
        nome = self.contato.nome_contato or 'Sem Nome'
        external = self.external_id or 'No ID'
        return f"{nome} ({external})"

    def prepare_notion_data(self) -> None:
        """
        Prepara e formata os dados para sincronização com Notion.

        Este método utiliza o mapper para transformar os dados do contato
        no formato esperado pelo Notion, incluindo formatação de telefones,
        normalização de emails e preparação de tags.
        """
        try:
            from .services.mappers.contato_mapper import ContatoMapper

            # Usa mapper para transformar dados
            self.notion_properties = ContatoMapper.to_notion_properties(self)

            # Formata campos específicos
            self.nome_formatado = self._format_name(self.contato.nome_contato)

            if self.contato.email:
                self.email_normalizado = self.contato.email.lower().strip()

            if self.contato.telefone:
                self.telefone_formatado = self._format_phone(self.contato.telefone)

            # Prepara tags (se existirem no metadados)
            tags = self.contato.metadados.get('tags', []) if self.contato.metadados else []
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            elif not isinstance(tags, list):
                tags = []

            self.tags_formatadas = [
                tag.strip().title()
                for tag in tags
                if tag.strip()
            ]

            # Detecta se é contato principal
            self.principal = self._is_principal_contact()

        except ImportError:
            # Fallback se mapper não estiver disponível
            self._prepare_notion_data_fallback()

    def _prepare_notion_data_fallback(self) -> None:
        """
        Método fallback para preparação de dados sem mapper.
        """
        self.nome_formatado = self._format_name(self.contato.nome_contato)

        if self.contato.email:
            self.email_normalizado = self.contato.email.lower().strip()

        if self.contato.telefone:
            self.telefone_formatado = self._format_phone(self.contato.telefone)

        self.principal = self._is_principal_contact()

        # Propriedades básicas para Notion
        self.notion_properties = {
            'Nome': {
                'title': [
                    {'text': {'content': self.nome_formatado}}
                ]
            }
        }

        if self.email_normalizado:
            self.notion_properties['Email'] = {
                'email': self.email_normalizado
            }

        if self.telefone_formatado:
            self.notion_properties['Telefone'] = {
                'phone_number': self.telefone_formatado
            }

    def _format_name(self, name: str | None) -> str:
        """
        Formata o nome para o padrão do Notion.

        Args:
            name: Nome original.

        Returns:
            Nome formatado.
        """
        if not name:
            return "Sem Nome"
        return name.strip().title()

    def _format_phone(self, phone: str) -> str:
        """
        Formata telefone para padrão internacional.

        Args:
            phone: Telefone original.

        Returns:
            Telefone formatado.
        """
        # Remove tudo que não é dígito
        digits = re.sub(r'\D', '', phone)

        # Verifica se tem código do Brasil
        if digits.startswith('55') and len(digits) > 11:
            return f"+{digits[:2]} {digits[2:4]} {digits[4:-4]} {digits[-4:]}"
        elif len(digits) == 11:  # Celular com 9
            return f"+55 {digits[0:2]} {digits[2:7]} {digits[7:]}"
        elif len(digits) == 10:  # Fixo
            return f"+55 {digits[0:2]} {digits[2:6]} {digits[6:]}"
        else:
            return phone  # Retorna original se não conseguir formatar

    def _is_principal_contact(self) -> bool:
        """
        Verifica se é o contato principal do cliente.

        Returns:
            True se for contato principal.
        """
        if not self.contato.clientes.exists():
            return False

        # Se há apenas um contato, é principal
        cliente = self.contato.clientes.first()
        if cliente and cliente.contatos.count() == 1:
            return True

        # Verifica se está marcado como principal nos metadados
        principal_flag = self.contato.metadados.get('principal', False) if self.contato.metadados else False
        return bool(principal_flag)

    def needs_sync(self) -> bool:
        """
        Verifica se precisa sincronizar.

        Returns:
            True se precisar sincronizar.
        """
        if not self.config.sync_enabled:
            return False

        if self.sync_status == 'syncing':
            return False

        # Verifica se houve alterações após último sync
        if self.last_sync_at and self.contato.ultima_interacao > self.last_sync_at:
            return True

        return self.sync_status in ['pending', 'error']

    def mark_as_synced(self, external_id: str) -> None:
        """
        Marca o contato como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado no Notion.
        """
        self.external_id = external_id
        self.sync_status = 'synced'
        self.last_sync_at = timezone.now()
        self.sync_error = None
        self.retry_count = 0
        self.save()

    def mark_as_failed(self, error_message: str) -> None:
        """
        Marca o contato como falha na sincronização.

        Args:
            error_message: Mensagem de erro da falha.
        """
        self.sync_status = 'error'
        self.sync_error = error_message
        self.retry_count += 1
        self.save()

    # Property methods para compatibilidade
    @property
    def is_synced(self) -> bool:
        """Verifica se está sincronizado (compatibilidade)."""
        return self.sync_status == 'synced'

    @property
    def sync_age_hours(self) -> int:
        """Idade da última sincronização em horas."""
        if not self.last_sync_at:
            return 999
        delta = timezone.now() - self.last_sync_at
        return int(delta.total_seconds() // 3600)

    @property
    def has_sync_errors(self) -> bool:
        """Verifica se há erros de sincronização."""
        return self.sync_status == 'error' and bool(self.sync_error)

    @property
    def notion_url(self) -> str:
        """URL da página no Notion."""
        if not self.external_id:
            return "#"
        return f"https://notion.so/{self.config.notion_page_id or self.config.notion_database_id}?p={self.external_id}"


class ClienteSync(models.Model):
    """
    Espelho do modelo Cliente para integração com Notion.

    Contém dados pré-processados e formatados para compatibilidade
    com as propriedades do Notion.
    """

    # Relação com Modelo Original
    cliente = models.OneToOneField(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name='notion_sync',
        help_text="Referência ao cliente original"
    )

    # ID Externo
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion"
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='cliente_syncs',
        help_text="Configuração Notion para este modelo"
    )

    # Dados Pré-processados
    nome_fantasia_formatado: models.CharField = models.CharField(
        max_length=200,
        help_text="Nome fantasia formatado"
    )

    nome_fantasia_formatado: models.CharField = models.CharField(
        max_length=200,
        help_text="Nome fantasia formatado"
    )

    razao_social_formatada: models.CharField = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Razão social formatada"
    )

    cnpj_formatado: models.CharField = models.CharField(
        max_length=18,
        null=True,
        blank=True,
        help_text="CNPJ formatado (apenas dígitos)"
    )

    telefone_formatado: models.CharField = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Telefone formatado"
    )

    endereco_completo: models.TextField = models.TextField(
        null=True,
        blank=True,
        help_text="Endereço completo formatado"
    )

    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro'),
            ('disabled', 'Desabilitado'),
        ],
        default='pending',
        help_text="Status atual da sincronização"
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora da última sincronização"
    )

    sync_error: models.TextField = models.TextField(
        null=True,
        blank=True,
        help_text="Detalhes do último erro de sincronização"
    )

    retry_count: models.IntegerField = models.IntegerField(
        default=0,
        help_text="Número de tentativas de sincronização"
    )

    notion_properties: models.JSONField = models.JSONField(
        default=dict,
        help_text="Propriedades completas formatadas para API Notion"
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Cliente Sync"
        verbose_name_plural = "Clientes Sync"
        ordering = ['cliente__nome_fantasia']
        db_table = "notion_sync_cliente"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['cliente']),
            models.Index(fields=['last_sync_at']),
        ]

    @override
    def __str__(self) -> str:
        return f"{self.cliente.nome_fantasia} ({self.external_id or 'No ID'})"

    def prepare_notion_data(self) -> None:
        """
        Prepara e formata os dados para sincronização com Notion.
        """
        try:
            from .services.mappers.cliente_mapper import ClienteMapper

            # Usa mapper para transformar dados
            self.notion_properties = ClienteMapper.to_notion_properties(self)

            # Formata campos específicos
            self.nome_fantasia_formatado = self.cliente.nome_fantasia.strip().title()

            if self.cliente.razao_social:
                self.razao_social_formatada = self.cliente.razao_social.strip().title()

            if self.cliente.cnpj:
                self.cnpj_formatado = re.sub(r'\D', '', self.cliente.cnpj)

            if self.cliente.telefone:
                self.telefone_formatado = self._format_phone(self.cliente.telefone)

            # Prepara endereço completo
            self.endereco_completo = self.cliente.get_endereco_completo()

        except ImportError:
            # Fallback se mapper não estiver disponível
            self._prepare_notion_data_fallback()

    def _prepare_notion_data_fallback(self) -> None:
        """
        Método fallback para preparação de dados sem mapper.
        """
        self.nome_fantasia_formatado = self.cliente.nome_fantasia.strip().title()

        if self.cliente.razao_social:
            self.razao_social_formatada = self.cliente.razao_social.strip().title()

        if self.cliente.cnpj:
            self.cnpj_formatado = re.sub(r'\D', '', self.cliente.cnpj)

        if self.cliente.telefone:
            self.telefone_formatado = self._format_phone(self.cliente.telefone)

        self.endereco_completo = self.cliente.get_endereco_completo()

        # Propriedades básicas para Notion
        self.notion_properties = {
            'Nome Fantasia': {
                'title': [
                    {'text': {'content': self.nome_fantasia_formatado}}
                ]
            }
        }

        if self.razao_social_formatada:
            self.notion_properties['Razão Social'] = {
                'rich_text': [
                    {'text': {'content': self.razao_social_formatada}}
                ]
            }

        if self.cnpj_formatado:
            self.notion_properties['CNPJ'] = {
                'rich_text': [
                    {'text': {'content': self.cnpj_formatado}}
                ]
            }

    def _format_phone(self, phone: str) -> str:
        """
        Formata telefone para padrão internacional.

        Args:
            phone: Telefone original.

        Returns:
            Telefone formatado.
        """
        digits = re.sub(r'\D', '', phone)

        if digits.startswith('55') and len(digits) > 11:
            return f"+{digits[:2]} {digits[2:4]} {digits[4:-4]} {digits[-4:]}"
        elif len(digits) == 11:
            return f"+55 {digits[0:2]} {digits[2:7]} {digits[7:]}"
        elif len(digits) == 10:
            return f"+55 {digits[0:2]} {digits[2:6]} {digits[6:]}"
        else:
            return phone

    def needs_sync(self) -> bool:
        """
        Verifica se precisa sincronizar.

        Returns:
            True se precisar sincronizar.
        """
        if not self.config.sync_enabled:
            return False

        if self.sync_status == 'syncing':
            return False

        # Verifica se houve alterações após último sync
        if self.last_sync_at and self.cliente.ultima_atualizacao > self.last_sync_at:
            return True

        return self.sync_status in ['pending', 'error']

    def mark_as_synced(self, external_id: str) -> None:
        """
        Marca o cliente como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado no Notion.
        """
        self.external_id = external_id
        self.sync_status = 'synced'
        self.last_sync_at = timezone.now()
        self.sync_error = None
        self.retry_count = 0
        self.save()

    def mark_as_failed(self, error_message: str) -> None:
        """
        Marca o cliente como falha na sincronização.

        Args:
            error_message: Mensagem de erro da falha.
        """
        self.sync_status = 'error'
        self.sync_error = error_message
        self.retry_count += 1
        self.save()


# Models simplificados para outros tipos (conforme plano)
class DepartamentoSync(models.Model):
    """
    Espelho do modelo Departamento para integração com Notion.
    """

    departamento = models.OneToOneField(
        "operacional.Departamento",
        on_delete=models.CASCADE,
        related_name='notion_sync',
        help_text="Referência ao departamento original"
    )

    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True
    )

    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='departamento_syncs'
    )

    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro'),
        ],
        default='pending'
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Departamento Sync"
        verbose_name_plural = "Departamentos Sync"
        db_table = "notion_sync_departamento"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
        ]


class AtendenteSync(models.Model):
    """
    Espelho do modelo Atendente para integração com Notion.
    """

    atendente = models.OneToOneField(
        "operacional.AtendenteHumano",
        on_delete=models.CASCADE,
        related_name='notion_sync',
        help_text="Referência ao atendente original"
    )

    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True
    )

    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='atendente_syncs'
    )

    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro'),
        ],
        default='pending'
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Atendente Sync"
        verbose_name_plural = "Atendentes Sync"
        db_table = "notion_sync_atendente"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
        ]


class MensagemSync(models.Model):
    """
    Espelho do modelo Mensagem para integração com Notion.
    """

    mensagem = models.OneToOneField(
        "atendimentos.Mensagem",
        on_delete=models.CASCADE,
        related_name='notion_sync',
        help_text="Referência à mensagem original"
    )

    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True
    )

    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='mensagem_syncs'
    )

    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro'),
        ],
        default='pending'
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True
    )

    updated_at: models.DateTimeField = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Mensagem Sync"
        verbose_name_plural = "Mensagens Sync"
        db_table = "notion_sync_mensagem"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
        ]
