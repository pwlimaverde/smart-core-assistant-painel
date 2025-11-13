"""Testes para o signal de criação de etapas padrão.

Verifica se, ao criar um novo `FluxoAtendimento` em departamentos
permitidos, as etapas padrão são garantidas automaticamente.
"""

from __future__ import annotations

from typing import List

import pytest

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
)


@pytest.mark.django_db
def test_default_etapas_created_for_atendimento() -> None:
    """Garante etapas padrão ao criar fluxo no departamento Atendimento."""
    dep, _ = Departamento.objects.get_or_create(nome="Atendimento")

    fluxo = FluxoAtendimento.objects.create(
        departamento=dep,
        nome="Fluxo Teste",
    )

    etapas: List[EtapaFluxo] = list(
        EtapaFluxo.objects.filter(fluxo=fluxo).order_by("ordem")
    )
    nomes: List[str] = [e.nome for e in etapas]

    # Deve criar no mínimo as 5 etapas padrão
    assert len(etapas) >= 5
    assert "Fila de Atendimento" in nomes
    assert "Em Atendimento" in nomes
    assert "Resolvido" in nomes
    assert "Pendência" in nomes
    assert "Cancelado" in nomes