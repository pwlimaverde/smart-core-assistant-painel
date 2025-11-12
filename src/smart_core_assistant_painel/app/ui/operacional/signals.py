"""Signals do app Operacional.

Cria automaticamente etapas padrão quando um novo `FluxoAtendimento` é
registrado. Comentários em Português conforme padrões do projeto.
"""

from __future__ import annotations

from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EtapaFluxo, FluxoAtendimento, TipoEtapa


@receiver(
    post_save,
    sender=FluxoAtendimento,
    dispatch_uid="operacional.create_default_etapas_fluxo",
)
def create_default_etapas_fluxo(
    sender: Any, instance: FluxoAtendimento, created: bool, **kwargs: Any
) -> None:
    """Cria etapas padrão ao registrar um novo fluxo.

    Regras solicitadas:
    - 1ª etapa: "Fila de Atendimento" (ordem 0, cor #B0C4DE, FILA)
    - 2ª etapa: "Resolvido" (ordem 1000, cor #66CDAA, FINALIZACAO)
    - 3ª etapa: "Pendência" (ordem 999, cor #FFFACD, ESPERA)
    - 4ª etapa: "Cancelado" (ordem 1001, cor #FA8072, FINALIZACAO)

    Os demais campos permanecem com valores padrões definidos no model.
    Idempotente por usar `get_or_create` com chave (fluxo, ordem).
    """

    if not created:
        # Comentário: apenas para novos fluxos
        return

    # Comentário: o projeto possui fluxos em vários departamentos.
    # Para evitar interferências em testes e cenários onde as etapas
    # são criadas manualmente, limitamos a criação automática aos
    # departamentos padrão "Operacional" e "Atendimento".
    dept_nome: str = getattr(instance.departamento, "nome", "")
    allowed_departments: set[str] = {"Operacional", "Atendimento"}
    if dept_nome not in allowed_departments:
        return

    etapas_def = (
        {
            "nome": "Fila de Atendimento",
            "ordem": 0,
            "tipo_etapa": TipoEtapa.FILA,
            "cor": "#B0C4DE",
            "descricao": (
                "Lista padrão para agrupamento de novos atendimentos"
            ),
        },
        {
            "nome": "Em Atendimento",
            "ordem": 998,
            "tipo_etapa": TipoEtapa.TRABALHO,
            "cor": "#ADD8E6",
            "descricao": ("Lista padrão para atendimentos em trabalho"),
        },
        {
            "nome": "Resolvido",
            "ordem": 1000,
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "cor": "#66CDAA",
            "descricao": (
                "Lista padrão para agrupamento de atendimentos resolvidos"
            ),
        },
        {
            "nome": "Pendência",
            "ordem": 999,
            "tipo_etapa": TipoEtapa.ESPERA,
            "cor": "#FFFACD",
            "descricao": (
                "Lista padrão para agrupamento de atendimentos com algum "
                "tipo de pendência"
            ),
        },
        {
            "nome": "Cancelado",
            "ordem": 1001,
            "tipo_etapa": TipoEtapa.FINALIZACAO,
            "cor": "#FA8072",
            "descricao": (
                "Lista padrão para agrupamento de atendimentos cancelados"
            ),
        },
    )

    for ed in etapas_def:
        # Comentário: chave de idempotência (fluxo, ordem)
        EtapaFluxo.objects.get_or_create(
            fluxo=instance,
            ordem=ed["ordem"],
            defaults={
                "nome": ed["nome"],
                "descricao": ed["descricao"],
                "tipo_etapa": ed["tipo_etapa"],
                "cor": ed["cor"],
            },
        )
