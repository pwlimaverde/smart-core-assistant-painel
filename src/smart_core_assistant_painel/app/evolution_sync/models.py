from datetime import datetime
from typing import Any

from django.db import models


class APIVersion(models.TextChoices):
    """[INT-EVO-VER-001] Versão da Evolution API usada pela instância."""

    V2 = "v2", "Evolution API v2 (Baileys)"
    GO = "go", "Evolution Go"


class MediaStorageBackend(models.TextChoices):
    """[INT-EVO-VER-002] Backend de storage de mídia configurado no servidor Evolution Go."""

    NONE = "none", "Sem storage (download on-demand)"
    S3 = "s3", "S3 / MinIO no servidor Evolution"


class EvolutionInstance(models.Model):
    """[INT-EVO-001] Representa uma instância conectada na Evolution API.

    Gestão de Instâncias Evolution.

    Attributes:
        id: Identificador único da instância no banco de dados.
        tenant_id: UUID do Tenant proprietário (armazenado como campo simples,
            sem FK, para evitar constraints cross-database).
        name: Nome amigável da instância.
        instance_id: ID da instância na Evolution API.
        api_key: Chave de API / token de autenticação da instância.
        server_url: URL do servidor da Evolution API.
        phone_number: Número de telefone associado à instância.
        active: Indica se a instância está ativa.
        connection_state: Estado da conexão WhatsApp (open, close, unknown).
        last_state_check: Data/hora da última verificação de estado.
        created_at: Data e hora de criação do registro.
        api_version: Versão da Evolution API (``v2`` ou ``go``).
            Feature flag que seleciona o adapter correto via
            ``get_evolution_adapter(instance.api_version)``.
        media_storage_backend: Indica se o servidor Evolution Go tem S3/MinIO
            configurado. Quando ``s3``, o payload do webhook já traz
            ``data.message.mediaUrl`` e não é necessário chamar
            ``downloadmedia`` ou ``getBase64FromMediaMessage``.
        subscribed_events: Lista de eventos assinados no ``/instance/connect``
            do Evolution Go. Vazia em instâncias v2 (events configurados
            via ``/webhook/set``).
        last_connection_state: Último estado de conexão recebido via webhook
            evento ``CONNECTION`` (atualizado pelo webhook; evita polling).
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    # Nota: Usando UUIDField em vez de FK para evitar constraints cross-database
    # O Tenant está no banco 'default', mas EvolutionInstance precisa estar
    # no banco do tenant para manter relação com EvolutionContact->Contato
    tenant_id: models.UUIDField = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="UUID do Tenant proprietário desta instância Evolution",
    )
    name: models.CharField[str] = models.CharField(max_length=100)
    instance_id: models.CharField[str | None] = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    api_key: models.CharField[str] = models.CharField(
        max_length=256,
        help_text="Token de autenticação da instância (instance token em Go, api_key em v2)",
    )
    phone_number: models.CharField[str | None] = models.CharField(
        max_length=20, blank=True, null=True
    )
    active: models.BooleanField[bool] = models.BooleanField(default=True)
    connection_state: models.CharField[str] = models.CharField(
        max_length=20,
        default="unknown",
        help_text="Estado da conexão: open, close, unknown",
    )
    last_state_check: models.DateTimeField[datetime | None] = (
        models.DateTimeField(null=True, blank=True)
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # ------------------------------------------------------------------ #
    # Campos novos: suporte ao Evolution Go (Phase 1)
    # ------------------------------------------------------------------ #
    api_version: models.CharField[str] = models.CharField(
        max_length=5,
        choices=APIVersion.choices,
        default=APIVersion.GO,
        help_text=(
            "Feature flag: seleciona o adapter REST correto. "
            "Altere para 'v2' para rollback imediato sem deploy."
        ),
    )
    media_storage_backend: models.CharField[str] = models.CharField(
        max_length=10,
        choices=MediaStorageBackend.choices,
        default=MediaStorageBackend.S3,
        help_text=(
            "Backend de mídia do servidor Evolution Go. "
            "Se 's3', o webhook já traz mediaUrl — sem chamadas extras. "
            "Se 'none', o painel chama POST /message/downloadmedia como fallback."
        ),
    )
    subscribed_events: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Eventos assinados no POST /instance/connect (Evolution Go). "
            "Ex: ['MESSAGE', 'MESSAGE_UPDATE', 'PRESENCE', 'CONNECTION', 'CONTACTS', 'QRCODE']"
        ),
    )
    last_connection_state: models.CharField[str | None] = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text=(
            "Último estado de conexão recebido via evento CONNECTION do webhook. "
            "Substitui o polling de /instance/connectionState em instâncias Go."
        ),
    )

    class Meta:
        db_table = "evolution_sync_instance"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # type: ignore[override]
        return self.name

    @property
    def is_go(self) -> bool:
        """Retorna True se esta instância usa o Evolution Go adapter."""
        return self.api_version == APIVersion.GO

    @property
    def has_s3(self) -> bool:
        """Retorna True se o servidor tem S3/MinIO configurado."""
        return self.media_storage_backend == MediaStorageBackend.S3


class EvolutionContact(models.Model):
    """[INT-EVO-002] Mapeia um contato do WhatsApp (Evolution) para um Contato do sistema.

    Mapeamento de Contatos (Sync).

    Attributes:
        id: Identificador único do mapeamento.
        contact: Referência ao Contato no sistema principal.
        instance: Referência à instância Evolution associada.
        jid: ID do contato no WhatsApp (JID).
        lid: ID do contato no formato LID (Linked Device).
        addressing_mode: Modo de endereçamento do contato.
        active: Indica se o mapeamento está ativo.
        metadados: Dados adicionais em formato JSON.
        created_at: Data e hora de criação.
        updated_at: Data e hora da última atualização.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    contact: models.ForeignKey[Any] = models.ForeignKey(
        "clientes.Contato",
        on_delete=models.SET_NULL,
        related_name="evolution_links",
        blank=True,
        null=True,
    )
    instance: models.ForeignKey[EvolutionInstance] = models.ForeignKey(
        EvolutionInstance,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    jid: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True
    )
    lid: models.CharField[str | None] = models.CharField(
        max_length=100, blank=True, null=True
    )
    addressing_mode: models.CharField[str | None] = models.CharField(
        max_length=8, blank=True, null=True
    )
    active: models.BooleanField[bool] = models.BooleanField(default=True)
    metadados: models.JSONField[dict[str, Any]] = models.JSONField(
        default=dict, blank=True
    )
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "evolution_sync_contact"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["jid"]),
            models.Index(fields=["lid"]),
            models.Index(fields=["contact"]),
            models.Index(fields=["instance"]),
        ]

    def __str__(self) -> str:  # type: ignore[override]
        ident = self.jid or self.lid or "unknown"
        return f"{self.instance.name} - {ident}"


class WhiteList(models.Model):
    """[INT-EVO-003] Lista de números que não devem gerar interações no sistema.

    Whitelist de Números.

    Attributes:
        id: Identificador único.
        contact: Vínculo opcional com contato já cadastrado no sistema.
        name: Nome da pessoa ou entidade.
        phone_number: Número de telefone (normalizado).
        active: Indica se o registro está ativo.
        created_at: Data e hora de criação.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    contact: models.ForeignKey[Any] = models.ForeignKey(
        "clientes.Contato",
        on_delete=models.SET_NULL,
        related_name="whitelist_entries",
        blank=True,
        null=True,
    )
    name: models.CharField[str] = models.CharField(max_length=100)
    phone_number: models.CharField[str] = models.CharField(
        max_length=20, unique=True
    )
    active: models.BooleanField[bool] = models.BooleanField(default=True)
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "evolution_sync_whitelist"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.phone_number})"
