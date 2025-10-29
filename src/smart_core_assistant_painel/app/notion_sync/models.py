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
from django.db import models
from django.utils import timezone


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
        help_text="Identificador único para referência no código",
    )

    name: models.CharField = models.CharField(
        max_length=200,
        help_text="Nome descritivo da database/página no Notion",
    )

    description: models.TextField = models.TextField(
        blank=True, help_text="Descrição detalhada do uso desta configuração"
    )

    # Configuração Notion (API 2025-09-03)
    notion_database_id: models.UUIDField = models.UUIDField(
        help_text="ID da database no Notion (formato UUID)"
    )

    data_source_id: models.UUIDField = models.UUIDField(
        null=True, blank=True, help_text="ID do data source (API v2025-09-03)"
    )

    notion_page_id: models.UUIDField = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID da página principal (opcional, para hierarquias)",
    )

    # Mapeamento Django
    django_model: models.CharField = models.CharField(
        max_length=100, help_text="Modelo Django correspondente (app.Model)"
    )

    django_app_label: models.CharField = models.CharField(
        max_length=50, help_text="App Django onde o modelo está definido"
    )

    notion_schema: models.JSONField = models.JSONField(
        default=dict, help_text="Schema completo das propriedades do Notion"
    )

    field_mappings: models.JSONField = models.JSONField(
        default=dict, help_text="Mapeamento campo_django → campo_notion"
    )

    # Configurações de Sincronização
    sync_enabled: models.BooleanField = models.BooleanField(
        default=True, help_text="Habilita/desabilita sincronização"
    )

    sync_direction: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("bidirectional", "Bidirecional"),
            ("django_to_notion", "Django → Notion"),
            ("notion_to_django", "Notion → Django"),
        ],
        default="bidirectional",
        help_text="Direção da sincronização",
    )

    sync_priority: models.IntegerField = models.IntegerField(
        default=5,
        choices=[
            (1, "Baixa"),
            (3, "Média"),
            (5, "Normal"),
            (7, "Alta"),
            (10, "Crítica"),
        ],
        help_text="Prioridade na fila de sincronização",
    )

    auto_sync: models.BooleanField = models.BooleanField(
        default=True, help_text="Sincroniza automaticamente após alterações"
    )

    batch_sync_enabled: models.BooleanField = models.BooleanField(
        default=False, help_text="Permite sincronização em lote"
    )

    batch_size: models.IntegerField = models.IntegerField(
        default=50, help_text="Tamanho do lote para sincronização em batch"
    )

    # Controle
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True
    )

    metadata: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais e configurações customizadas",
    )

    class Meta:
        verbose_name = "Configuração Notion"
        verbose_name_plural = "Configurações Notion"
        ordering = ["sync_priority", "slug"]
        db_table = "notion_database_config"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["django_model"]),
            models.Index(fields=["sync_enabled"]),
            models.Index(fields=["sync_priority"]),
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
                self.django_app_label, self.django_model.split(".")[-1]
            )
        except LookupError as exc:
            raise ValueError(
                f"Modelo {self.django_model} não encontrado"
            ) from exc

    def is_ready_for_sync(self) -> bool:
        """
        Verifica se está pronto para sincronização.

        Returns:
            True se pronto para sincronizar.
        """
        return (
            self.sync_enabled
            and self.notion_database_id
            and self.data_source_id
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
                django_model__icontains=model_name, sync_enabled=True
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
        properties_schema: dict[str, Any] | None = None,
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
        if "." in model_name:
            app_label, model = model_name.split(".", 1)
        else:
            app_label = "unknown"
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
            },
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
        max_length=100, help_text="Modelo Django (app.Model)"
    )

    local_id: models.IntegerField = models.IntegerField(
        help_text="ID do registro local"
    )

    external_id: models.CharField = models.CharField(
        max_length=36, db_index=True, help_text="ID da página no Notion"
    )

    # Configuração
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name="object_mappings",
        help_text="Configuração utilizada",
    )

    # Controle
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True
    )

    class Meta:
        verbose_name = "Mapeamento Notion"
        verbose_name_plural = "Mapeamentos Notion"
        unique_together = ["local_model", "local_id"]
        db_table = "notion_object_mapping"
        indexes = [
            models.Index(fields=["external_id"]),
            models.Index(fields=["local_model", "local_id"]),
            models.Index(fields=["config"]),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"{self.local_model}#{self.local_id} → {self.external_id[:8]}..."
        )

    @classmethod
    def get_by_external_id(
        cls, external_id: str
    ) -> "NotionObjectMapping | None":
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
        related_name="notion_sync",
        help_text="Referência ao contato original",
    )

    # ID Externo (Principal para Localização)
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion (UUID sem dashes)",
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name="contato_syncs",
        help_text="Configuração Notion para este modelo",
    )

    # Dados Pré-processados (Formatados para Notion)
    nome_formatado: models.CharField = models.CharField(
        max_length=200, help_text="Nome já formatado e validado para o Notion"
    )

    email_normalizado: models.EmailField = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
        help_text="Email validado e normalizado",
    )

    telefone_formatado: models.CharField = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Telefone no formato internacional (+55XX999999999)",
    )

    principal: models.BooleanField = models.BooleanField(
        default=False, help_text="É contato principal do cliente?"
    )

    tags_formatadas: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags formatadas para select/multi-select do Notion",
    )

    slug_formatado: models.SlugField = models.SlugField(
        max_length=250, blank=True, default="", help_text="Slug formatado para URL"
    )

    notion_properties: models.JSONField = models.JSONField(
        default=dict,
        help_text="Propriedades completas formatadas para API Notion",
    )

    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendente"),
            ("syncing", "Sincronizando"),
            ("synced", "Sincronizado"),
            ("error", "Erro"),
            ("disabled", "Desabilitado"),
        ],
        default="pending",
        help_text="Status atual da sincronização",
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True, help_text="Data/hora da última sincronização"
    )

    sync_error: models.TextField = models.TextField(
        null=True,
        blank=True,
        help_text="Detalhes do último erro de sincronização",
    )

    retry_count: models.IntegerField = models.IntegerField(
        default=0, help_text="Número de tentativas de sincronização"
    )

    sync_metadata: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais sobre a sincronização",
    )

    metadados: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais para sincronização",
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contato Sync"
        verbose_name_plural = "Contatos Sync"
        ordering = ["contato__nome_contato"]
        db_table = "notion_sync_contato"
        indexes = [
            models.Index(fields=["external_id"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["contato"]),
            models.Index(fields=["last_sync_at"]),
            models.Index(fields=["sync_status", "config"]),
        ]

    @override
    def __str__(self) -> str:
        nome = self.contato.nome_contato or "Sem Nome"
        external = self.external_id or "No ID"
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
                self.telefone_formatado = self._format_phone(
                    self.contato.telefone
                )

            # Prepara tags (se existirem no metadados)
            tags = (
                self.contato.metadados.get("tags", [])
                if self.contato.metadados
                else []
            )
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            elif not isinstance(tags, list):
                tags = []

            self.tags_formatadas = [
                tag.strip().title() for tag in tags if tag.strip()
            ]

            # Detecta se é contato principal
            self.principal = self._is_principal_contact()

            # Prepara slug formatado
            if self.contato.slug:
                self.slug_formatado = self.contato.slug
            elif self.nome_formatado:
                # Gera slug a partir do nome formatado como fallback
                self.slug_formatado = (
                    self.nome_formatado.lower().replace(" ", "-")
                )

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
            "Nome": {"title": [{"text": {"content": self.nome_formatado}}]}
        }

        if self.email_normalizado:
            self.notion_properties["Email"] = {"email": self.email_normalizado}

        if self.telefone_formatado:
            self.notion_properties["Telefone"] = {
                "phone_number": self.telefone_formatado
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
        digits = re.sub(r"\D", "", phone)

        # Verifica se tem código do Brasil
        if digits.startswith("55") and len(digits) > 11:
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
        principal_flag = (
            self.contato.metadados.get("principal", False)
            if self.contato.metadados
            else False
        )
        return bool(principal_flag)

    def needs_sync(self) -> bool:
        """
        Verifica se precisa sincronizar.

        Returns:
            True se precisar sincronizar.
        """
        if not self.config.sync_enabled:
            return False

        if self.sync_status == "syncing":
            return False

        # Verifica se houve alterações após último sync
        if (
            self.last_sync_at
            and self.contato.ultima_interacao > self.last_sync_at
        ):
            return True

        return self.sync_status in ["pending", "error"]

    def mark_as_synced(self, external_id: str | None = None) -> None:
        """
        Marca o contato como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado no Notion (opcional para updates).
        """
        if external_id:
            self.external_id = external_id
        self.sync_status = "synced"
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
        self.sync_status = "error"
        self.sync_error = error_message
        self.retry_count += 1
        self.save()

    # Property methods para compatibilidade
    @property
    def is_synced(self) -> bool:
        """Verifica se está sincronizado (compatibilidade)."""
        return self.sync_status == "synced"

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
        return self.sync_status == "error" and bool(self.sync_error)

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
        related_name="notion_sync",
        help_text="Referência ao cliente original",
    )

    # ID Externo
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion",
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name="cliente_syncs",
        help_text="Configuração Notion para este modelo",
    )

    # Dados Pré-processados
    nome_fantasia_formatado: models.CharField = models.CharField(
        max_length=200, help_text="Nome fantasia formatado"
    )

    razao_social_formatada: models.CharField = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Razão social formatada",
    )

    cnpj_formatado: models.CharField = models.CharField(
        max_length=18,
        null=True,
        blank=True,
        help_text="CNPJ formatado (apenas dígitos)",
    )

    telefone_formatado: models.CharField = models.CharField(
        max_length=20, null=True, blank=True, help_text="Telefone formatado"
    )

    endereco_completo: models.TextField = models.TextField(
        null=True, blank=True, help_text="Endereço completo formatado"
    )

    slug_formatado: models.SlugField = models.SlugField(
        max_length=250, blank=True, default="", help_text="Slug formatado para URL"
    )

    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendente"),
            ("syncing", "Sincronizando"),
            ("synced", "Sincronizado"),
            ("error", "Erro"),
            ("disabled", "Desabilitado"),
        ],
        default="pending",
        help_text="Status atual da sincronização",
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True, help_text="Data/hora da última sincronização"
    )

    sync_error: models.TextField = models.TextField(
        null=True,
        blank=True,
        help_text="Detalhes do último erro de sincronização",
    )

    retry_count: models.IntegerField = models.IntegerField(
        default=0, help_text="Número de tentativas de sincronização"
    )

    notion_properties: models.JSONField = models.JSONField(
        default=dict,
        help_text="Propriedades completas formatadas para API Notion",
    )

    metadados: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais para sincronização",
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente Sync"
        verbose_name_plural = "Clientes Sync"
        ordering = ["cliente__nome_fantasia"]
        db_table = "notion_sync_cliente"
        indexes = [
            models.Index(fields=["external_id"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["cliente"]),
            models.Index(fields=["last_sync_at"]),
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
            self.nome_fantasia_formatado = (
                self.cliente.nome_fantasia.strip().title()
            )

            if self.cliente.razao_social:
                self.razao_social_formatada = (
                    self.cliente.razao_social.strip().title()
                )

            if self.cliente.cnpj:
                self.cnpj_formatado = re.sub(r"\D", "", self.cliente.cnpj)

            if self.cliente.telefone:
                self.telefone_formatado = self._format_phone(
                    self.cliente.telefone
                )

            # Prepara endereço completo
            self.endereco_completo = self.cliente.get_endereco_completo()

            # Prepara slug formatado
            if self.cliente.slug:
                self.slug_formatado = self.cliente.slug
            else:
                # Gera slug a partir do nome fantasia como fallback
                self.slug_formatado = (
                    self.nome_fantasia_formatado.lower().replace(" ", "-")
                )

        except ImportError:
            # Fallback se mapper não estiver disponível
            self._prepare_notion_data_fallback()

    def _prepare_notion_data_fallback(self) -> None:
        """
        Método fallback para preparação de dados sem mapper.
        """
        self.nome_fantasia_formatado = (
            self.cliente.nome_fantasia.strip().title()
        )

        if self.cliente.razao_social:
            self.razao_social_formatada = (
                self.cliente.razao_social.strip().title()
            )

        if self.cliente.cnpj:
            self.cnpj_formatado = re.sub(r"\D", "", self.cliente.cnpj)

        if self.cliente.telefone:
            self.telefone_formatado = self._format_phone(self.cliente.telefone)

        self.endereco_completo = self.cliente.get_endereco_completo()

        # Propriedades básicas para Notion
        self.notion_properties = {
            "Nome Fantasia": {
                "title": [{"text": {"content": self.nome_fantasia_formatado}}]
            }
        }

        if self.razao_social_formatada:
            self.notion_properties["Razão Social"] = {
                "rich_text": [
                    {"text": {"content": self.razao_social_formatada}}
                ]
            }

        if self.cnpj_formatado:
            self.notion_properties["CNPJ"] = {
                "rich_text": [{"text": {"content": self.cnpj_formatado}}]
            }

        # Endereço completo
        if self.endereco_completo:
            self.notion_properties["Endereço"] = {
                "rich_text": [{"text": {"content": self.endereco_completo}}]
            }

        # Componentes do endereço
        if self.cliente.bairro:
            self.notion_properties["Bairro"] = {
                "rich_text": [{"text": {"content": self.cliente.bairro}}]
            }

        if self.cliente.cidade:
            self.notion_properties["Cidade"] = {
                "rich_text": [{"text": {"content": self.cliente.cidade}}]
            }

        if self.cliente.uf:
            self.notion_properties["UF"] = {
                "rich_text": [{"text": {"content": self.cliente.uf.upper()}}]
            }

        # Status Ativo
        self.notion_properties["Ativo"] = {"checkbox": bool(self.cliente.ativo)}

    def _format_phone(self, phone: str) -> str:
        """
        Formata telefone para padrão internacional.

        Args:
            phone: Telefone original.

        Returns:
            Telefone formatado.
        """
        digits = re.sub(r"\D", "", phone)

        if digits.startswith("55") and len(digits) > 11:
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

        if self.sync_status == "syncing":
            return False

        # Verifica se houve alterações após último sync
        if (
            self.last_sync_at
            and self.cliente.ultima_atualizacao > self.last_sync_at
        ):
            return True

        return self.sync_status in ["pending", "error"]

    def mark_as_synced(self, external_id: str | None = None) -> None:
        """
        Marca o cliente como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado no Notion (opcional para updates).
        """
        if external_id:
            self.external_id = external_id
        self.sync_status = "synced"
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
        self.sync_status = "error"
        self.sync_error = error_message
        self.retry_count += 1
        self.save()


class DepartamentoSync(models.Model):
    """
    Espelho do modelo Departamento para integração com Notion.

    Contém dados pré-processados e formatados para compatibilidade
    com as propriedades do Notion.
    """

    # Relação com Modelo Original
    departamento = models.OneToOneField(
        "operacional.Departamento",
        on_delete=models.CASCADE,
        related_name="notion_sync",
        help_text="Referência ao departamento original",
    )

    # ID Externo
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion",
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name="departamento_syncs",
        help_text="Configuração Notion para este modelo",
    )

    # Dados Pré-processados
    nome_formatado: models.CharField = models.CharField(
        max_length=100, help_text="Nome formatado"
    )

    slug_formatado: models.SlugField = models.SlugField(
        max_length=120, help_text="Slug formatado para URL"
    )

    descricao_formatada: models.TextField = models.TextField(
        null=True, blank=True, help_text="Descrição formatada"
    )

    status_formatado: models.CharField = models.CharField(
        max_length=20,
        default="Ativo",
        help_text="Status formatado (Ativo/Inativo)",
    )

    count_atendentes: models.IntegerField = models.IntegerField(
        default=0, help_text="Número de atendentes no departamento"
    )

    especialidades_formatadas: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Especialidades formatadas para multi-select do Notion",
    )

    # Campos de Controle de Sincronização
    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendente"),
            ("syncing", "Sincronizando"),
            ("synced", "Sincronizado"),
            ("error", "Erro"),
            ("disabled", "Desabilitado"),
        ],
        default="pending",
        help_text="Status atual da sincronização",
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True, help_text="Data/hora da última sincronização"
    )

    sync_error: models.TextField = models.TextField(
        null=True,
        blank=True,
        help_text="Detalhes do último erro de sincronização",
    )

    retry_count: models.IntegerField = models.IntegerField(
        default=0, help_text="Número de tentativas de sincronização"
    )

    notion_properties: models.JSONField = models.JSONField(
        default=dict,
        help_text="Propriedades completas formatadas para API Notion",
    )

    metadados: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais para sincronização",
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Departamento Sync"
        verbose_name_plural = "Departamentos Sync"
        ordering = ["departamento__nome"]
        db_table = "notion_sync_departamento"
        indexes = [
            models.Index(fields=["external_id"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["departamento"]),
            models.Index(fields=["last_sync_at"]),
            models.Index(fields=["sync_status", "config"]),
        ]

    @override
    def __str__(self) -> str:
        nome = self.departamento.nome or "Sem Nome"
        external = self.external_id or "No ID"
        return f"{nome} ({external})"

    def prepare_notion_data(self) -> None:
        """
        Prepara e formata os dados para sincronização com Notion.
        """
        try:
            from .services.mappers.departamento_mapper import (
                DepartamentoMapper,
            )

            # Usa mapper para transformar dados
            self.notion_properties = DepartamentoMapper.to_notion_properties(
                self
            )

            # Formata campos específicos
            self.nome_formatado = self.departamento.nome.strip().title()
            self.slug_formatado = (
                self.departamento.slug
                or self.nome_formatado.lower().replace(" ", "-")
            )

            if self.departamento.descricao:
                self.descricao_formatada = self.departamento.descricao.strip()

            # Formata status
            self.status_formatado = (
                "Ativo" if self.departamento.ativo else "Inativo"
            )

            # Conta atendentes ativos
            self.count_atendentes = self.departamento.atendentes.filter(
                ativo=True
            ).count()

            # Prepara especialidades a partir da configuração
            especialidades = []
            if (
                self.departamento.configuracoes
                and "especialidades" in self.departamento.configuracoes
            ):
                especs = self.departamento.configuracoes["especialidades"]
                if isinstance(especs, list):
                    especialidades = [
                        espec.strip().title()
                        for espec in especs
                        if espec.strip()
                    ]
                elif isinstance(especs, str):
                    especialidades = [
                        espec.strip().title()
                        for espec in especs.split(",")
                        if espec.strip()
                    ]

            self.especialidades_formatadas = especialidades

            # Armazena dados atuais nos metadados para detecção de mudanças futuras
            if not self.metadados:
                self.metadados = {}
            self.metadados["last_synced_data"] = {
                "nome": self.departamento.nome,
                "descricao": self.departamento.descricao,
                "ativo": self.departamento.ativo,
            }

        except ImportError:
            # Fallback se mapper não estiver disponível
            self._prepare_notion_data_fallback()

    def _prepare_notion_data_fallback(self) -> None:
        """
        Método fallback para preparação de dados sem mapper.
        """
        self.nome_formatado = self.departamento.nome.strip().title()
        self.slug_formatado = (
            self.departamento.slug
            or self.nome_formatado.lower().replace(" ", "-")
        )

        if self.departamento.descricao:
            self.descricao_formatada = self.departamento.descricao.strip()

        self.status_formatado = (
            "Ativo" if self.departamento.ativo else "Inativo"
        )
        self.count_atendentes = self.departamento.atendentes.filter(
            ativo=True
        ).count()

        # Propriedades básicas para Notion
        self.notion_properties = {
            "Nome": {"title": [{"text": {"content": self.nome_formatado}}]},
            "Ativo": {"checkbox": bool(self.departamento.ativo)},
        }

        if self.descricao_formatada:
            self.notion_properties["Descrição"] = {
                "rich_text": [{"text": {"content": self.descricao_formatada}}]
            }

    def needs_sync(self) -> bool:
        """
        Verifica se precisa sincronizar.

        Returns:
            True se precisar sincronizar.
        """
        if not self.config.sync_enabled:
            return False

        if self.sync_status == "syncing":
            return False

        # Verifica se houve alterações após último sync
        if self.last_sync_at:
            # Verifica data de criação (para novos registros)
            if self.departamento.data_criacao > self.last_sync_at:
                return True
            # Departamento não tem updated_at, então verificamos mudança no campo ativo
            # Verifica se mudou o campo ativo (compara com valor formatado atual)
            if self.status_formatado != (
                "Ativo" if self.departamento.ativo else "Inativo"
            ):
                return True
            # Verifica se houve mudança em outros campos importantes
            # Comparando valores atuais com os últimos sincronizados (se disponíveis nos metadados)
            if hasattr(self, "metadados") and self.metadados:
                last_synced_data = self.metadados.get("last_synced_data", {})
                if (
                    last_synced_data.get("nome") != self.departamento.nome
                    or last_synced_data.get("descricao")
                    != self.departamento.descricao
                ):
                    return True

        return self.sync_status in ["pending", "error"]

    def mark_as_synced(self, external_id: str | None = None) -> None:
        """
        Marca o departamento como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado no Notion (opcional para updates).
        """
        if external_id:
            self.external_id = external_id
        self.sync_status = "synced"
        self.last_sync_at = timezone.now()
        self.sync_error = None
        self.retry_count = 0
        self.save()

    def mark_as_failed(self, error_message: str) -> None:
        """
        Marca o departamento como falha na sincronização.

        Args:
            error_message: Mensagem de erro da falha.
        """
        self.sync_status = "error"
        self.sync_error = error_message
        self.retry_count += 1
        self.save()

    # Property methods para compatibilidade
    @property
    def is_synced(self) -> bool:
        """Verifica se está sincronizado (compatibilidade)."""
        return self.sync_status == "synced"

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
        return self.sync_status == "error" and bool(self.sync_error)

    @property
    def notion_url(self) -> str:
        """URL da página no Notion."""
        if not self.external_id:
            return "#"
        return f"https://notion.so/{self.config.notion_page_id or self.config.notion_database_id}?p={self.external_id}"


class AtendenteSync(models.Model):
    """
    Espelho do modelo Atendente para integração com Notion.

    Contém dados pré-processados e formatados para compatibilidade
    com as propriedades do Notion, incluindo relacionamento com Departamento.
    """

    # Relação com Modelo Original
    atendente = models.OneToOneField(
        "operacional.Atendente",
        on_delete=models.CASCADE,
        related_name="notion_sync",
        help_text="Referência ao atendente original",
    )

    # ID Externo
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion",
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name="atendente_syncs",
        help_text="Configuração Notion para este modelo",
    )

    # Relacionamento com Departamento (para consulta otimizada)
    departamento_sync = models.ForeignKey(
        DepartamentoSync,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atendentes_sync",
        help_text="Referência ao sync do departamento (cache)",
    )

    # Dados Pré-processados
    slug_formatado: models.SlugField = models.SlugField(
        max_length=250, blank=True, default="", help_text="Slug formatado para URL"
    )

    nome_formatado: models.CharField = models.CharField(
        max_length=100, help_text="Nome formatado"
    )

    cargo_formatado: models.CharField = models.CharField(
        max_length=100, help_text="Cargo formatado"
    )

    departamento_nome: models.CharField = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Nome do departamento (cache)",
    )

    email_formatado: models.EmailField = models.EmailField(
        max_length=254, null=True, blank=True, help_text="Email normalizado"
    )

    telefone_formatado: models.CharField = models.CharField(
        max_length=20, null=True, blank=True, help_text="Telefone formatado"
    )

    status_formatado: models.CharField = models.CharField(
        max_length=20,
        default="Ativo",
        help_text="Status formatado (Ativo/Inativo)",
    )

    disponibilidade_formatada: models.CharField = models.CharField(
        max_length=20,
        default="Disponível",
        help_text="Disponibilidade formatada",
    )

    carga_atual: models.IntegerField = models.IntegerField(
        default=0, help_text="Carga atual de atendimentos"
    )

    capacidade_maxima: models.IntegerField = models.IntegerField(
        default=5, help_text="Capacidade máxima de atendimentos"
    )

    especialidades_formatadas: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text="Especialidades formatadas para multi-select do Notion",
    )

    # Campos de Controle de Sincronização
    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendente"),
            ("syncing", "Sincronizando"),
            ("synced", "Sincronizado"),
            ("error", "Erro"),
            ("disabled", "Desabilitado"),
        ],
        default="pending",
        help_text="Status atual da sincronização",
    )

    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True, help_text="Data/hora da última sincronização"
    )

    sync_error: models.TextField = models.TextField(
        null=True,
        blank=True,
        help_text="Detalhes do último erro de sincronização",
    )

    retry_count: models.IntegerField = models.IntegerField(
        default=0, help_text="Número de tentativas de sincronização"
    )

    notion_properties: models.JSONField = models.JSONField(
        default=dict,
        help_text="Propriedades completas formatadas para API Notion",
    )

    metadados: models.JSONField = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados adicionais para sincronização",
    )

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atendente Sync"
        verbose_name_plural = "Atendentes Sync"
        ordering = ["atendente__nome"]
        db_table = "notion_sync_atendente"
        indexes = [
            models.Index(fields=["external_id"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["atendente"]),
            models.Index(fields=["departamento_sync"]),
            models.Index(fields=["last_sync_at"]),
            models.Index(fields=["sync_status", "config"]),
        ]

    @override
    def __str__(self) -> str:
        nome = self.atendente.nome or "Sem Nome"
        external = self.external_id or "No ID"
        return f"{nome} ({external})"

    def prepare_notion_data(self) -> None:
        """
        Prepara e formata os dados para sincronização com Notion.
        """
        try:
            from .services.mappers.atendente_mapper import (
                AtendenteMapper,
            )

            # Usa mapper para transformar dados
            self.notion_properties = (
                AtendenteMapper.to_notion_properties(self)
            )

            # Formata campos específicos
            self.nome_formatado = self.atendente.nome.strip().title()
            self.cargo_formatado = self.atendente.cargo.strip().title()

            # Prepara slug formatado
            if self.atendente.slug:
                self.slug_formatado = self.atendente.slug
            else:
                # Gera slug a partir do nome formatado como fallback
                self.slug_formatado = (
                    self.nome_formatado.lower().replace(" ", "-")
                )

            # Cache do departamento
            if self.atendente.departamento:
                self.departamento_nome = self.atendente.departamento.nome
                # Busca sync do departamento
                try:
                    self.departamento_sync = DepartamentoSync.objects.get(
                        departamento=self.atendente.departamento
                    )
                except DepartamentoSync.DoesNotExist:
                    self.departamento_sync = None
            else:
                self.departamento_nome = None
                self.departamento_sync = None

            if self.atendente.email:
                self.email_formatado = self.atendente.email.lower().strip()

            if self.atendente.telefone:
                self.telefone_formatado = self._format_phone(
                    self.atendente.telefone
                )

            # Formata status
            self.status_formatado = (
                "Ativo" if self.atendente.ativo else "Inativo"
            )
            self.disponibilidade_formatada = (
                "Disponível" if self.atendente.disponivel else "Indisponível"
            )

            # Calcula carga atual
            self.carga_atual = self.atendente.get_atendimentos_ativos()
            self.capacidade_maxima = (
                self.atendente.max_atendimentos_simultaneos
            )

            # Prepara especialidades
            especialidades = []
            if self.atendente.especialidades:
                if isinstance(self.atendente.especialidades, list):
                    especialidades = [
                        espec.strip().title()
                        for espec in self.atendente.especialidades
                        if espec.strip()
                    ]
                elif isinstance(self.atendente.especialidades, str):
                    especialidades = [
                        espec.strip().title()
                        for espec in self.atendente.especialidades.split(",")
                        if espec.strip()
                    ]

            self.especialidades_formatadas = especialidades

            # Armazena dados atuais nos metadados para detecção de mudanças futuras
            if not self.metadados:
                self.metadados = {}
            self.metadados["last_synced_data"] = {
                "nome": self.atendente.nome,
                "cargo": self.atendente.cargo,
                "email": self.atendente.email,
                "ativo": self.atendente.ativo,
                "disponivel": self.atendente.disponivel,
                "departamento_id": self.atendente.departamento_id,
            }

        except ImportError:
            # Fallback se mapper não estiver disponível
            self._prepare_notion_data_fallback()

    def _prepare_notion_data_fallback(self) -> None:
        """
        Método fallback para preparação de dados sem mapper.
        """
        self.nome_formatado = self.atendente.nome.strip().title()
        self.cargo_formatado = self.atendente.cargo.strip().title()

        if self.atendente.departamento:
            self.departamento_nome = self.atendente.departamento.nome

        if self.atendente.email:
            self.email_formatado = self.atendente.email.lower().strip()

        if self.atendente.telefone:
            self.telefone_formatado = self._format_phone(
                self.atendente.telefone
            )

        self.status_formatado = "Ativo" if self.atendente.ativo else "Inativo"
        self.disponibilidade_formatada = (
            "Disponível" if self.atendente.disponivel else "Indisponível"
        )

        self.carga_atual = self.atendente.get_atendimentos_ativos()
        self.capacidade_maxima = self.atendente.max_atendimentos_simultaneos

        # Propriedades básicas para Notion
        self.notion_properties = {
            "Nome": {"title": [{"text": {"content": self.nome_formatado}}]},
            "Cargo": {
                "rich_text": [{"text": {"content": self.cargo_formatado}}]
            },
            "Ativo": {"checkbox": bool(self.atendente.ativo)},
            "Disponível": {"checkbox": bool(self.atendente.disponivel)},
            "Capacidade Máxima": {"number": self.capacidade_maxima},
        }

        if self.email_formatado:
            self.notion_properties["Email"] = {"email": self.email_formatado}

        if self.telefone_formatado:
            self.notion_properties["Telefone"] = {
                "phone_number": self.telefone_formatado
            }

    def _format_phone(self, phone: str) -> str:
        """
        Formata telefone para padrão internacional.

        Args:
            phone: Telefone original.

        Returns:
            Telefone formatado.
        """
        # Remove tudo que não é dígito
        digits = re.sub(r"\D", "", phone)

        # Verifica se tem código do Brasil
        if digits.startswith("55") and len(digits) > 11:
            return f"+{digits[:2]} {digits[2:4]} {digits[4:-4]} {digits[-4:]}"
        elif len(digits) == 11:  # Celular com 9
            return f"+55 {digits[0:2]} {digits[2:7]} {digits[7:]}"
        elif len(digits) == 10:  # Fixo
            return f"+55 {digits[0:2]} {digits[2:6]} {digits[6:]}"
        else:
            return phone  # Retorna original se não conseguir formatar

    def needs_sync(self) -> bool:
        """
        Verifica se precisa sincronizar.

        Returns:
            True se precisar sincronizar.
        """
        if not self.config.sync_enabled:
            return False

        if self.sync_status == "syncing":
            return False

        # Verifica se houve alterações após último sync
        if self.last_sync_at:
            # Verifica data de criação (para novos registros)
            if self.atendente.data_cadastro > self.last_sync_at:
                return True
            # Verifica data de última atividade
            if self.atendente.ultima_atividade > self.last_sync_at:
                return True
            # Verifica se mudou o campo ativo (compara com valor formatado atual)
            if self.status_formatado != (
                "Ativo" if self.atendente.ativo else "Inativo"
            ):
                return True
            # Verifica se houve mudança em outros campos importantes
            # Comparando valores atuais com os últimos sincronizados (se disponíveis nos metadados)
            if hasattr(self, "metadados") and self.metadados:
                last_synced_data = self.metadados.get("last_synced_data", {})
                if (
                    last_synced_data.get("nome") != self.atendente.nome
                    or last_synced_data.get("cargo") != self.atendente.cargo
                    or last_synced_data.get("email") != self.atendente.email
                    or last_synced_data.get("disponivel")
                    != self.atendente.disponivel
                    or last_synced_data.get("departamento_id")
                    != self.atendente.departamento_id
                ):
                    return True

        return self.sync_status in ["pending", "error"]

    def mark_as_synced(self, external_id: str | None = None) -> None:
        """
        Marca o atendente como sincronizado com sucesso.

        Args:
            external_id: ID do registro criado no Notion (opcional para updates).
        """
        if external_id:
            self.external_id = external_id
        self.sync_status = "synced"
        self.last_sync_at = timezone.now()
        self.sync_error = None
        self.retry_count = 0
        self.save()

    def mark_as_failed(self, error_message: str) -> None:
        """
        Marca o atendente como falha na sincronização.

        Args:
            error_message: Mensagem de erro da falha.
        """
        self.sync_status = "error"
        self.sync_error = error_message
        self.retry_count += 1
        self.save()

    # Property methods para compatibilidade
    @property
    def is_synced(self) -> bool:
        """Verifica se está sincronizado (compatibilidade)."""
        return self.sync_status == "synced"

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
        return self.sync_status == "error" and bool(self.sync_error)

    @property
    def notion_url(self) -> str:
        """URL da página no Notion."""
        if not self.external_id:
            return "#"
        return f"https://notion.so/{self.config.notion_page_id or self.config.notion_database_id}?p={self.external_id}"


class AtendimentoSync(models.Model):
    """
    Espelho do modelo Atendimento para integração com Notion.
    """

    # Relação com Modelo Original
    atendimento = models.OneToOneField(
        "atendimentos.Atendimento",
        on_delete=models.CASCADE,
        related_name="notion_sync",
        help_text="Referência ao atendimento original",
    )

    # ID Externo
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion",
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name="atendimento_syncs",
        help_text="Configuração Notion para este modelo",
    )

    # Relacionamentos com outros Syncs (para consulta otimizada e mappers)
    contato_sync = models.ForeignKey(
        ContatoSync,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atendimentos_sync",
        help_text="Referência ao sync do contato",
    )
    departamento_sync = models.ForeignKey(
        DepartamentoSync,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atendimentos_sync",
        help_text="Referência ao sync do departamento",
    )
    atendente_sync = models.ForeignKey(
        "AtendenteSync",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atendimentos_sync",
        help_text="Referência ao sync do atendente",
    )

    # Dados Pré-processados
    protocolo_formatado: models.CharField = models.CharField(
        max_length=50, help_text="Protocolo formatado para ser o título no Notion"
    )
    status_formatado: models.CharField = models.CharField(
        max_length=50, help_text="Status formatado para o campo Select do Notion"
    )
    prioridade_formatada: models.CharField = models.CharField(
        max_length=50, help_text="Prioridade formatada para o campo Select do Notion"
    )
    tags_formatadas: models.JSONField = models.JSONField(
        default=list, blank=True, help_text="Tags para o campo Multi-select do Notion"
    )
    sla_status: models.CharField = models.CharField(
        max_length=20, blank=True, help_text="Status calculado do SLA (Ex: OK, Vencido)"
    )

    # Campos de Controle de Sincronização
    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendente"),
            ("syncing", "Sincronizando"),
            ("synced", "Sincronizado"),
            ("error", "Erro"),
            ("disabled", "Desabilitado"),
        ],
        default="pending",
        help_text="Status atual da sincronização",
    )
    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True, help_text="Data/hora da última sincronização"
    )
    sync_error: models.TextField = models.TextField(
        null=True, blank=True, help_text="Detalhes do último erro de sincronização"
    )
    retry_count: models.IntegerField = models.IntegerField(
        default=0, help_text="Número de tentativas de sincronização"
    )
    notion_properties: models.JSONField = models.JSONField(
        default=dict, help_text="Propriedades completas formatadas para API Notion"
    )
    metadados: models.JSONField = models.JSONField(
        default=dict, blank=True, help_text="Metadados adicionais para sincronização"
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atendimento Sync"
        verbose_name_plural = "Atendimentos Sync"
        ordering = ["-atendimento__data_inicio"]
        db_table = "notion_sync_atendimento"
        indexes = [
            models.Index(fields=["external_id"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["atendimento"]),
            models.Index(fields=["contato_sync"]),
            models.Index(fields=["departamento_sync"]),
            models.Index(fields=["atendente_sync"]),
        ]

    @override
    def __str__(self) -> str:
        protocolo = self.atendimento.protocolo or f"#{self.atendimento.id}"
        external = self.external_id or "No ID"
        return f"{protocolo} ({external})"

    def prepare_notion_data(self) -> None:
        """Prepara e formata os dados para sincronização com Notion."""
        try:
            from .services.mappers.atendimento_mapper import AtendimentoMapper
            self.notion_properties = AtendimentoMapper.to_notion_properties(self)

            # Atualiza cache de relacionamentos
            if self.atendimento.contato:
                self.contato_sync, _ = ContatoSync.objects.get_or_create(contato=self.atendimento.contato)
            if self.atendimento.departamento:
                self.departamento_sync, _ = DepartamentoSync.objects.get_or_create(departamento=self.atendimento.departamento)
            if self.atendimento.atendente_humano:
                self.atendente_sync, _ = AtendenteSync.objects.get_or_create(atendente=self.atendimento.atendente_humano)

        except ImportError:
            # Lidar com o caso de o mapper ainda não existir
            pass

    def needs_sync(self) -> bool:
        """Verifica se o atendimento precisa ser sincronizado."""
        if not self.config.sync_enabled or self.sync_status == "syncing":
            return False
        if self.last_sync_at and self.atendimento.data_ultima_mensagem > self.last_sync_at:
            return True
        return self.sync_status in ["pending", "error"]

    def mark_as_synced(self, external_id: str | None = None) -> None:
        if external_id:
            self.external_id = external_id
        self.sync_status = "synced"
        self.last_sync_at = timezone.now()
        self.sync_error = None
        self.retry_count = 0
        self.save()

    def mark_as_failed(self, error_message: str) -> None:
        self.sync_status = "error"
        self.sync_error = error_message
        self.retry_count += 1
        self.save()


class MensagemSync(models.Model):
    """
    Espelho do modelo Mensagem para integração com Notion.
    """

    # Relação com Modelo Original
    mensagem = models.OneToOneField(
        "atendimentos.Mensagem",
        on_delete=models.CASCADE,
        related_name="notion_sync",
        help_text="Referência à mensagem original",
    )

    # ID Externo
    external_id: models.CharField = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="ID do bloco (ou página) correspondente no Notion",
    )

    # Configuração Relacionada
    config = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name="mensagem_syncs",
        help_text="Configuração Notion para este modelo",
    )

    # Relacionamento com AtendimentoSync
    atendimento_sync = models.ForeignKey(
        AtendimentoSync,
        on_delete=models.CASCADE,
        related_name="mensagens_sync",
        help_text="Referência ao sync do atendimento pai",
    )

    # Dados Pré-processados
    conteudo_formatado: models.TextField = models.TextField(
        help_text="Conteúdo formatado e truncado para o Notion"
    )
    remetente_formatado: models.CharField = models.CharField(
        max_length=100, help_text="Nome formatado do remetente"
    )

    # Campos de Controle de Sincronização
    sync_status: models.CharField = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendente"),
            ("syncing", "Sincronizando"),
            ("synced", "Sincronizado"),
            ("error", "Erro"),
            ("disabled", "Desabilitado"),
        ],
        default="pending",
        help_text="Status atual da sincronização",
    )
    last_sync_at: models.DateTimeField = models.DateTimeField(
        null=True, blank=True, help_text="Data/hora da última sincronização"
    )
    sync_error: models.TextField = models.TextField(
        null=True, blank=True, help_text="Detalhes do último erro de sincronização"
    )
    retry_count: models.IntegerField = models.IntegerField(
        default=0, help_text="Número de tentativas de sincronização"
    )
    notion_properties: models.JSONField = models.JSONField(
        default=dict, help_text="Propriedades completas formatadas para API Notion"
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mensagem Sync"
        verbose_name_plural = "Mensagens Sync"
        ordering = ["mensagem__timestamp"]
        db_table = "notion_sync_mensagem"
        indexes = [
            models.Index(fields=["external_id"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["mensagem"]),
            models.Index(fields=["atendimento_sync"]),
        ]

    @override
    def __str__(self) -> str:
        return f"Mensagem #{self.mensagem.id} do Atendimento #{self.atendimento_sync.atendimento.id}"

    def prepare_notion_data(self) -> None:
        """Prepara e formata os dados para sincronização com Notion."""
        try:
            from .services.mappers.mensagem_mapper import MensagemMapper
            self.notion_properties = MensagemMapper.to_notion_properties(self)

            # Garante que o atendimento_sync está linkado
            if not self.atendimento_sync and self.mensagem.atendimento:
                self.atendimento_sync, _ = AtendimentoSync.objects.get_or_create(atendimento=self.mensagem.atendimento)

        except ImportError:
            # Lidar com o caso de o mapper ainda não existir
            pass

    def needs_sync(self) -> bool:
        """Verifica se a mensagem precisa ser sincronizada."""
        # Mensagens são geralmente imutáveis após a criação
        return self.sync_status in ["pending", "error"]

    def mark_as_synced(self, external_id: str | None = None) -> None:
        if external_id:
            self.external_id = external_id
        self.sync_status = "synced"
        self.last_sync_at = timezone.now()
        self.sync_error = None
        self.retry_count = 0
        self.save()

    def mark_as_failed(self, error_message: str) -> None:
        self.sync_status = "error"
        self.sync_error = error_message
        self.retry_count += 1
        self.save()
