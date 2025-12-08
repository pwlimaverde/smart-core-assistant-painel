from datetime import datetime
from typing import Any

from django.db import models


class EvolutionInstance(models.Model):
    """[INT-EVO-001] Representa uma instância conectada na Evolution API.

    Gestão de Instâncias Evolution.

    Attributes:
        id: Identificador único da instância no banco de dados.
        name: Nome amigável da instância.
        instance_id: ID da instância na Evolution API.
        api_key: Chave de API para autenticação.
        server_url: URL do servidor da Evolution API.
        phone_number: Número de telefone associado à instância.
        active: Indica se a instância está ativa.
        created_at: Data e hora de criação do registro.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
    name: models.CharField[str] = models.CharField(max_length=100)
    instance_id: models.CharField[str | None] = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    api_key: models.CharField[str] = models.CharField(max_length=100)

    phone_number: models.CharField[str | None] = models.CharField(
        max_length=20, blank=True, null=True
    )
    active: models.BooleanField[bool] = models.BooleanField(default=True)
    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "evolution_sync_instance"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # type: ignore[override]
        return self.name


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
    contact: models.ForeignKey["clientes.Contato"] = models.ForeignKey(
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
        name: Nome da pessoa ou entidade.
        phone_number: Número de telefone (normalizado).
        active: Indica se o registro está ativo.
        created_at: Data e hora de criação.
    """

    id: models.AutoField = models.AutoField(primary_key=True)
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
