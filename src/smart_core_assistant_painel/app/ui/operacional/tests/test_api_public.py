from __future__ import annotations

import pytest
from django.urls import reverse

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
    TipoEtapa,
)


@pytest.mark.django_db
def test_departamentos_list_returns_active(client: object) -> None:
    Departamento.objects.create(nome="Comercial", slug="comercial")
    Departamento.objects.create(nome="Financeiro", slug="financeiro")

    url = reverse("operacional_api:departamentos")
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert "departamentos" in data
    slugs = [d["slug"] for d in data["departamentos"]]
    assert "comercial" in slugs
    assert "financeiro" in slugs


@pytest.mark.django_db
def test_fluxo_departamento_returns_etapas(client: object) -> None:
    dept = Departamento.objects.create(nome="Comercial", slug="comercial")
    fluxo = FluxoAtendimento.objects.create(
        departamento=dept, nome="Fluxo Comercial"
    )
    EtapaFluxo.objects.create(
        fluxo=fluxo,
        nome="Fila",
        ordem=1,
        cor="#6B7280",
        tipo_etapa=TipoEtapa.FILA,
        permite_atribuicao=False,
    )

    url = reverse(
        "operacional_api:fluxo-departamento",
        kwargs={"departamento_slug": dept.slug},
    )
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["departamento"]["slug"] == "comercial"
    assert data["fluxo"]["nome"] == "Fluxo Comercial"
    assert len(data["etapas"]) == 1
