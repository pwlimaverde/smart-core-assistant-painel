
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import MagicMock

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento, Atendente, AppInstance, FluxoAtendimento, EtapaFluxo, MovimentoFluxo,
    TipoEtapa, validate_telefone, validate_api_key, validate_telefone_instancia
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento, StatusAtendimento
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato

@pytest.mark.django_db
class TestOperacionalModels:
    def test_validators(self):
        validate_telefone("5511999999999")
        with pytest.raises(ValidationError):
            validate_telefone("123")

        validate_api_key("12345678")
        with pytest.raises(ValidationError):
            validate_api_key("short")

        validate_telefone_instancia("5511999999999")
        with pytest.raises(ValidationError):
            validate_telefone_instancia("123")

    def test_departamento_save(self):
        dep = Departamento.objects.create(nome="Teste Dep", telefone_instancia="(11) 9999-9999")
        assert dep.slug == "teste-dep"
        assert dep.telefone_instancia == "1199999999"

    def test_departamento_validar_api_key(self):
        dep = Departamento.objects.create(nome="Dep API", api_key="key12345", telefone_instancia="5511999999999", ativo=True)
        data = {"apikey": "key12345", "instance": "5511999999999"}
        assert Departamento.validar_api_key(data) == dep

        assert Departamento.validar_api_key({"apikey": "wrong", "instance": "5511999999999"}) is None

    def test_departamento_fluxo(self):
        dep = Departamento.objects.create(nome="Dep Fluxo")
        assert dep.get_fluxo() is None

        fluxo = dep.ensure_fluxo()
        assert fluxo.departamento == dep
        assert dep.get_fluxo() == fluxo

        fluxo2 = dep.ensure_fluxo()
        assert fluxo2 == fluxo

    def test_atendente_save(self):
        dep = Departamento.objects.create(nome="Dep Atendente")
        fluxo = dep.ensure_fluxo()
        at = Atendente.objects.create(nome="Joao", departamento=dep, fluxo=fluxo, telefone="11999999999")
        assert at.slug == "joao"
        assert at.telefone == "+5511999999999"

    def test_atendente_clean(self):
        # Missing fluxo
        at = Atendente(nome="Maria")
        with pytest.raises(ValidationError):
            at.clean()

    def test_atendente_availability(self):
        dep = Departamento.objects.create(nome="Dep Avail")
        fluxo = dep.ensure_fluxo()
        at = Atendente.objects.create(nome="Pedro", departamento=dep, fluxo=fluxo, max_atendimentos_simultaneos=1)

        assert at.is_available() is True
        assert at.current_load() == 0

        contato = Contato.objects.create(telefone="11888888888")
        atendimento = Atendimento.objects.create(
            contato=contato, departamento=dep, fluxo_atendimento=fluxo,
            atendente_humano=at, status=StatusAtendimento.EM_ATENDIMENTO
        )

        assert at.current_load() == 1
        assert at.is_available() is False

    def test_fluxo_etapas(self):
        dep = Departamento.objects.create(nome="Dep Etapas")
        fluxo = dep.ensure_fluxo()
        # Remove auto-generated steps to ensure clean test state
        fluxo.etapas.all().delete()

        e1 = EtapaFluxo.objects.create(fluxo=fluxo, nome="Fila", ordem=1, tipo_etapa=TipoEtapa.FILA)
        e2 = EtapaFluxo.objects.create(fluxo=fluxo, nome="Trab", ordem=2, tipo_etapa=TipoEtapa.TRABALHO)

        assert fluxo.get_etapa_inicial() == e1
        assert list(fluxo.get_etapas_por_tipo(TipoEtapa.TRABALHO)) == [e2]

    def test_etapa_clean(self):
        dep = Departamento.objects.create(nome="Dep Color")
        fluxo = dep.ensure_fluxo()
        e = EtapaFluxo(fluxo=fluxo, nome="Etapa", ordem=1, cor="FFF")
        e.clean()
        assert e.cor == "#FFFFFF"

    def test_movimento_fluxo(self):
        dep = Departamento.objects.create(nome="Dep Mov")
        fluxo = dep.ensure_fluxo()
        e1 = EtapaFluxo.objects.create(fluxo=fluxo, nome="E1", ordem=1, tipo_etapa=TipoEtapa.FILA)
        e2 = EtapaFluxo.objects.create(fluxo=fluxo, nome="E2", ordem=2, tipo_etapa=TipoEtapa.TRABALHO)
        atendente = Atendente.objects.create(nome="At", departamento=dep, fluxo=fluxo)

        contato = Contato.objects.create(telefone="11777777777")
        atendimento = Atendimento.objects.create(
            contato=contato, departamento=dep, fluxo_atendimento=fluxo, etapa_atual=e1
        )

        mov = MovimentoFluxo.criar_movimento(
            atendimento=atendimento,
            etapa_destino=e2,
            atendente_destino=atendente,
            etapa_origem=e1
        )

        atendimento.refresh_from_db()
        assert atendimento.etapa_atual == e2
        assert atendimento.atendente_humano == atendente
        assert mov.etapa_origem == e1

        assert mov.etapa_destino == e2
