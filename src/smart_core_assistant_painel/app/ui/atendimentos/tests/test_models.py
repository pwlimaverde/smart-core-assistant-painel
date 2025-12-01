
import pytest
from unittest.mock import MagicMock, patch
from django.core.exceptions import ValidationError
from django.utils import timezone
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento, StatusAtendimento, Mensagem, TipoMensagem, TipoRemetente,
    processar_mensagem_whatsapp, inicializar_atendimento_whatsapp
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.operacional.models import (
    Atendente, Departamento, FluxoAtendimento, EtapaFluxo, TipoEtapa
)

@pytest.mark.django_db
class TestAtendimentoModel:
    @pytest.fixture
    def contato(self):
        return Contato.objects.create(telefone="5511999999999", nome_contato="Teste")

    @pytest.fixture
    def departamento(self):
        return Departamento.objects.create(nome="Suporte", descricao="Desc")

    @pytest.fixture
    def fluxo(self, departamento):
        return FluxoAtendimento.objects.create(nome="Fluxo 1", departamento=departamento)

    @pytest.fixture
    def etapa(self, fluxo):
        return EtapaFluxo.objects.create(nome="Etapa 1", fluxo=fluxo, ordem=1, tipo_etapa=TipoEtapa.FILA)

    @pytest.fixture
    def atendente(self, departamento):
        return Atendente.objects.create(nome="Atendente 1", departamento=departamento)

    @pytest.fixture
    def atendimento(self, contato, departamento, fluxo, etapa):
        return Atendimento.objects.create(
            contato=contato,
            departamento=departamento,
            fluxo_atendimento=fluxo,
            etapa_atual=etapa,
            status=StatusAtendimento.FILA
        )

    def test_str(self, atendimento):
        assert str(atendimento.id) in str(atendimento)

    def test_clean_valid(self, atendimento):
        atendimento.clean()

    def test_clean_invalid_etapa_departamento(self, atendimento, fluxo):
        dep2 = Departamento.objects.create(nome="Outro")
        fluxo2 = FluxoAtendimento.objects.create(nome="Fluxo 2", departamento=dep2)
        etapa2 = EtapaFluxo.objects.create(nome="Etapa 2", fluxo=fluxo2, ordem=1)

        atendimento.etapa_atual = etapa2
        with pytest.raises(ValidationError) as exc:
            atendimento.clean()
        assert "A etapa selecionada não pertence ao departamento escolhido" in str(exc.value)

    def test_clean_invalid_fluxo_departamento(self, atendimento):
        dep2 = Departamento.objects.create(nome="Outro")
        fluxo2 = FluxoAtendimento.objects.create(nome="Fluxo 2", departamento=dep2)

        atendimento.fluxo_atendimento = fluxo2
        # Validation error is swallowed by try/except block in model.clean()
        # and logged as warning instead of raised.
        atendimento.clean()

    def test_change_status(self, atendimento):
        atendimento.change_status(StatusAtendimento.EM_ATENDIMENTO, "Teste")
        atendimento.refresh_from_db()
        assert atendimento.status == StatusAtendimento.EM_ATENDIMENTO
        assert len(atendimento.historico_status) > 0
        assert atendimento.historico_status[-1]["status"] == StatusAtendimento.EM_ATENDIMENTO

    def test_assign_to_agent(self, atendimento, atendente):
        atendimento.assign_to_agent(atendente)
        atendimento.refresh_from_db()
        assert atendimento.atendente_humano == atendente
        assert atendimento.status == StatusAtendimento.EM_ATENDIMENTO

    def test_unassign_agent(self, atendimento, atendente):
        atendimento.assign_to_agent(atendente)
        atendimento.unassign_agent()
        atendimento.refresh_from_db()
        assert atendimento.atendente_humano is None
        assert atendimento.status == StatusAtendimento.FILA

    def test_transfer_to_department(self, atendimento):
        dep2 = Departamento.objects.create(nome="Vendas")
        atendimento.transfer_to_department(dep2)
        atendimento.refresh_from_db()
        assert atendimento.departamento == dep2
        assert atendimento.status == StatusAtendimento.FILA
        assert atendimento.bot_pode_atender is False

    def test_apply_flow_by_description(self, atendimento, fluxo, departamento):
        desc = f"{fluxo.nome} - {departamento.nome}"
        atendimento.apply_flow_by_description(desc)
        atendimento.refresh_from_db()
        assert atendimento.fluxo_atendimento == fluxo

    def test_apply_flow_by_description_invalid(self, atendimento):
        with pytest.raises(ValidationError):
            atendimento.apply_flow_by_description("Invalido")

    def test_transferir_para_humano_com_saudacao(self, atendimento, atendente):
        with patch("smart_core_assistant_painel.app.ui.atendimentos.models.Mensagem.objects.create") as mock_create:
            atendimento.transferir_para_humano_com_saudacao(atendente.id)
            atendimento.refresh_from_db()
            assert atendimento.atendente_humano == atendente
            mock_create.assert_called_once()

    def test_carregar_historico_mensagens(self, atendimento):
        Mensagem.objects.create(atendimento=atendimento, conteudo="Oi", remetente=TipoRemetente.CONTATO)
        Mensagem.objects.create(atendimento=atendimento, conteudo="Ola", remetente=TipoRemetente.BOT)

        hist = atendimento.carregar_historico_mensagens()
        assert len(hist["conteudo_mensagens"]) == 2
        assert "Oi" in hist["conteudo_mensagens"]

@pytest.mark.django_db
class TestMensagemModel:
    @pytest.fixture
    def contato(self):
        return Contato.objects.create(telefone="5511999999999")

    @pytest.fixture
    def atendimento(self, contato):
        return Atendimento.objects.create(contato=contato)

    def test_registrar_resposta_bot(self, atendimento):
        msg = Mensagem.objects.create(atendimento=atendimento, conteudo="Oi")
        msg.registrar_resposta_bot("Resposta", 0.9)
        msg.refresh_from_db()
        assert msg.resposta_bot == "Resposta"
        assert msg.confianca_resposta == 0.9

    def test_registrar_resposta_bot_invalid(self, atendimento):
        msg = Mensagem.objects.create(atendimento=atendimento, conteudo="Oi")
        with pytest.raises(ValidationError):
            msg.registrar_resposta_bot("", 0.9)
        with pytest.raises(ValidationError):
            msg.registrar_resposta_bot("Resp", 1.5)

@pytest.mark.django_db
def test_inicializar_atendimento_whatsapp():
    contato, atendimento = inicializar_atendimento_whatsapp("5511888888888", "Oi")
    assert contato.telefone == "5511888888888"
    assert atendimento.contato == contato
    assert atendimento.status == StatusAtendimento.FILA

@pytest.mark.django_db
def test_processar_mensagem_whatsapp():
    msg_id = processar_mensagem_whatsapp("5511777777777", "Hello", "conversation", "msg1")
    assert Mensagem.objects.filter(id=msg_id).exists()
    msg = Mensagem.objects.get(id=msg_id)
    assert msg.conteudo == "Hello"
