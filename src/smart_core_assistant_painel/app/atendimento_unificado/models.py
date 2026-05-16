"""Modelos do app Workspace de Atendimento Unificado.

Princípio de independência (não-negociável conforme plano):

- **ZERO alteração** em tabelas legadas. Toda persistência criada por este
  app vai para tabelas `atu_*` próprias.
- FKs lógicas (BigIntegerField) substituem ForeignKey cross-app para
  evitar acoplamento e permitir migrations isoladas em DB do tenant.

E.1 entrega apenas `LeituraAtendimento` (não-lido por atendente).
E.2 acrescentará `CampoPersonalizado` e `ValorCampoAtendimento`.
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

    FKs são lógicas (BigIntegerField) e sem constraint cross-app,
    seguindo o mesmo critério adotado pelo `evolution_sync` quando
    referencia entidades do `clientes` no banco de tenant.
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
        verbose_name = "Leitura de Atendimento"
        verbose_name_plural = "Leituras de Atendimentos"
        db_table = "atu_leitura_atendimento"
        unique_together = [("atendimento_id", "atendente_id")]
        indexes = [
            models.Index(
                fields=["atendimento_id", "ultima_leitura_at"],
                name="atu_leit_atend_ultima_idx",
            ),
            models.Index(
                fields=["atendente_id", "ultima_leitura_at"],
                name="atu_leit_atend_at_idx",
            ),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"LeituraAtendimento(atendimento={self.atendimento_id}, "
            f"atendente={self.atendente_id}, at={self.ultima_leitura_at})"
        )
