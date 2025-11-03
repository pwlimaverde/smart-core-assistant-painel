from __future__ import annotations

import pytest
from django.urls import reverse

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
    TipoEtapa,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
)


@pytest.mark.django_db
def test_kanban_departamento_returns_columns(client: object) -> None:
    dept = Departamento.objects.create(nome="Comercial", slug="comercial")
    fluxo = FluxoAtendimento.objects.create(
        departamento=dept, nome="Fluxo Comercial"
    )
    etapa_fila = EtapaFluxo.objects.create(
        fluxo=fluxo,
        nome="Fila",
        ordem=1,
        cor="#6B7280",
        tipo_etapa=TipoEtapa.FILA,
        permite_atribuicao=False,
    )
    etapa_trabalho = EtapaFluxo.objects.create(
        fluxo=fluxo,
        nome="Trabalho",
        ordem=2,
        cor="#10B981",
        tipo_etapa=TipoEtapa.TRABALHO,
        permite_atribuicao=True,
    )

    contato = Contato.objects.create(telefone="+5511999999999")
    Atendimento.objects.create(
        contato=contato,
        departamento=dept,
        etapa_atual=etapa_fila,
        assunto="Novo orçamento",
    )
    Atendimento.objects.create(
        contato=contato,
        departamento=dept,
        etapa_atual=etapa_trabalho,
        assunto="Em contato",
    )

    url = reverse(
        "atendimentos_api:kanban-departamento",
        kwargs={"departamento_slug": dept.slug},
    )
    resp = client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["departamento"]["slug"] == "comercial"
    # Duas colunas esperadas
    assert len(data["columns"]) == 2
    counts = [c["count"] for c in data["columns"]]
    assert sum(counts) == 2


@pytest.mark.django_db
def test_atendimento_detail_and_messages(client: object) -> None:
    dept = Departamento.objects.create(nome="Comercial", slug="comercial")
    fluxo = FluxoAtendimento.objects.create(
        departamento=dept, nome="Fluxo Comercial"
    )
    etapa_fila = EtapaFluxo.objects.create(
        fluxo=fluxo,
        nome="Fila",
        ordem=1,
        cor="#6B7280",
        tipo_etapa=TipoEtapa.FILA,
        permite_atribuicao=False,
    )
    contato = Contato.objects.create(telefone="+5511999999998")
    atendimento = Atendimento.objects.create(
        contato=contato,
        departamento=dept,
        etapa_atual=etapa_fila,
        assunto="Consulta",
    )
    Mensagem.objects.create(
        atendimento=atendimento,
        tipo=TipoMensagem.TEXTO_FORMATADO,
        conteudo="Olá",
        remetente=TipoRemetente.CONTATO,
    )
    Mensagem.objects.create(
        atendimento=atendimento,
        tipo=TipoMensagem.TEXTO_FORMATADO,
        conteudo="Posso ajudar?",
        remetente=TipoRemetente.BOT,
    )

    detail_url = reverse(
        "atendimentos_api:atendimento-detalhe",
        kwargs={"atendimento_id": atendimento.id},
    )
    resp_d = client.get(detail_url)
    assert resp_d.status_code == 200
    assert resp_d.json()["atendimento"]["assunto"] == "Consulta"

    msgs_url = reverse(
        "atendimentos_api:mensagens-list",
        kwargs={"atendimento_id": atendimento.id},
    )
    resp_m = client.get(msgs_url)
    assert resp_m.status_code == 200
    msgs = resp_m.json()["mensagens"]
    assert len(msgs) == 2
    assert msgs[0]["conteudo"] == "Olá"
    assert msgs[1]["conteudo"] == "Posso ajudar?"