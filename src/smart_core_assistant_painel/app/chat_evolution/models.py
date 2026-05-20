"""Modelos do app Chat Evolution.

A persistência física das tabelas é mantida pelo `atendimento_unificado` (para
não quebrar o histórico de migrations). Aqui usamos `managed = False` mapeando
para a tabela real `atu_leitura_atendimento`.
"""

from __future__ import annotations

from datetime import datetime
from typing import override

from django.db import models


class LeituraAtendimento(models.Model):
    """Marca a última vez que um atendente "leu" um atendimento.

    Permite calcular não-lidos sem alterar `Atendimento`:
    ``Mensagem.filter(atendimento_id=..., remetente=CONTATO,
    timestamp__gt=LeituraAtendimento.ultima_leitura_at).count()``.

    FKs são lógicas (BigIntegerField) e sem constraint cross-app.
    """

    id: models.BigAutoField = models.BigAutoField(primary_key=True)
    atendimento_id: models.BigIntegerField[int] = models.BigIntegerField(
        help_text="ID lógico de atendimentos.Atendimento (sem FK cruzada).",
    )
    atendente_id: models.BigIntegerField[int] = models.BigIntegerField(
        help_text="ID lógico de operacional.Atendente (sem FK cruzada).",
    )
    ultima_leitura_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Momento da última leitura do atendimento pelo atendente.",
    )

    class Meta:
        managed = False
        verbose_name = "Leitura de Atendimento"
        verbose_name_plural = "Leituras de Atendimentos"
        db_table = "atu_leitura_atendimento"
        # unique_together and indexes are maintained by the real table

    @override
    def __str__(self) -> str:
        return (
            f"LeituraAtendimento(atendimento={self.atendimento_id}, "
            f"atendente={self.atendente_id}, at={self.ultima_leitura_at})"
        )
