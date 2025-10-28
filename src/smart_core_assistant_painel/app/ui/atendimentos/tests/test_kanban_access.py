import pytest
from django.urls import reverse
from django.contrib.auth.models import User

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    AtendenteHumano,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato


@pytest.mark.django_db
def test_non_member_cannot_access_other_department(client):
    d1 = Departamento.objects.create(
        nome="Depto A",
        ativo=True,
        api_key="key-a",
        telefone_instancia="5511999999001",
    )
    d2 = Departamento.objects.create(
        nome="Depto B",
        ativo=True,
        api_key="key-b",
        telefone_instancia="5511999999002",
    )

    user = User.objects.create_user(username="userA", password="pass")
    AtendenteHumano.objects.create(
        nome="Agente A",
        usuario_sistema="userA",
        departamento=d1,
        ativo=True,
        disponivel=True,
    )

    assert client.login(username="userA", password="pass")

    # Access own department OK
    url_d1 = reverse(
        "atendimentos:kanban_departamento", kwargs={"departamento_id": d1.id}
    )
    resp1 = client.get(url_d1)
    assert resp1.status_code == 200
    assert f"Kanban - {d1.nome}" in resp1.content.decode()

    # Access other department denied
    url_d2 = reverse(
        "atendimentos:kanban_departamento", kwargs={"departamento_id": d2.id}
    )
    resp2 = client.get(url_d2)
    assert resp2.status_code == 403


@pytest.mark.django_db
def test_manager_can_access_all_departments(client):
    d1 = Departamento.objects.create(
        nome="Depto A",
        ativo=True,
        api_key="key-a",
        telefone_instancia="5511999999001",
    )
    d2 = Departamento.objects.create(
        nome="Depto B",
        ativo=True,
        api_key="key-b",
        telefone_instancia="5511999999002",
    )

    user = User.objects.create_user(username="manager", password="pass")
    # manager may or may not be an atendente; not required for permission
    assert client.login(username="manager", password="pass")

    # Assign manager role via rolepermissions
    from rolepermissions.roles import assign_role

    assign_role(user, "gerente")

    url_d2 = reverse(
        "atendimentos:kanban_departamento", kwargs={"departamento_id": d2.id}
    )
    resp = client.get(url_d2)
    assert resp.status_code == 200
    content = resp.content.decode()
    # Dropdown should list active departments
    assert f'<option value="{d1.id}"' in content
    assert f'<option value="{d2.id}"' in content


@pytest.mark.django_db
def test_transfer_blocked_for_non_member(client):
    d1 = Departamento.objects.create(
        nome="Depto A",
        ativo=True,
        api_key="key-a",
        telefone_instancia="5511999999001",
    )
    d2 = Departamento.objects.create(
        nome="Depto B",
        ativo=True,
        api_key="key-b",
        telefone_instancia="5511999999002",
    )
    user = User.objects.create_user(username="userA", password="pass")
    agente_a = AtendenteHumano.objects.create(
        nome="Agente A",
        usuario_sistema="userA",
        departamento=d1,
        ativo=True,
        disponivel=True,
    )
    contato = Contato.objects.create(
        nome_contato="Cliente X", telefone="5511998887777"
    )
    atendimento = Atendimento.objects.create(
        contato=contato,
        departamento=d1,
        assunto="Teste",
        status=StatusAtendimento.AGUARDANDO_ATENDENTE,
    )

    assert client.login(username="userA", password="pass")

    url_d1 = reverse(
        "atendimentos:kanban_departamento", kwargs={"departamento_id": d1.id}
    )
    # Attempt to transfer to d2 (not allowed)
    resp = client.post(
        url_d1,
        data={
            "action": "transfer",
            "atendimento_id": atendimento.id,
            "target_departamento_id": d2.id,
        },
    )
    assert resp.status_code in (302, 200)  # redirect back to kanban
    atendimento.refresh_from_db()
    assert atendimento.departamento_id == d1.id


@pytest.mark.django_db
def test_partial_modal_lists_only_allowed_departments(client):
    d1 = Departamento.objects.create(
        nome="Depto A",
        ativo=True,
        api_key="key-a",
        telefone_instancia="5511999999001",
    )
    d2 = Departamento.objects.create(
        nome="Depto B",
        ativo=True,
        api_key="key-b",
        telefone_instancia="5511999999002",
    )
    user = User.objects.create_user(username="userA", password="pass")
    AtendenteHumano.objects.create(
        nome="Agente A",
        usuario_sistema="userA",
        departamento=d1,
        ativo=True,
        disponivel=True,
    )
    contato = Contato.objects.create(
        nome_contato="Cliente X", telefone="5511998887777"
    )
    atendimento = Atendimento.objects.create(
        contato=contato,
        departamento=d1,
        assunto="Teste",
        status=StatusAtendimento.AGUARDANDO_ATENDENTE,
    )

    assert client.login(username="userA", password="pass")

    url_d1 = reverse(
        "atendimentos:kanban_departamento", kwargs={"departamento_id": d1.id}
    )
    resp = client.get(
        url_d1, data={"partial": "1", "atendimento_id": atendimento.id}
    )
    assert resp.status_code == 200
    content = resp.content.decode()
    # Should include d1 option and not include d2 for non-manager
    assert f'<option value="{d1.id}"' in content
    assert f'<option value="{d2.id}"' not in content
