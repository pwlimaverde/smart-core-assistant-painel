from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError

# Assuming the models are in the correct path.
# Adjust the import path according to your project structure.
from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
    inicializar_atendimento_whatsapp,
    processar_mensagem_por_contato,
    processar_mensagem_whatsapp,
)
from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    Departamento,
    EtapaFluxo,
    FluxoAtendimento,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_departamento():
    """Fixture for a mock Departamento."""
    departamento = MagicMock(spec=Departamento)
    departamento.id = 1
    departamento.nome = "Comercial"
    return departamento


@pytest.fixture
def mock_fluxo(mock_departamento):
    """Fixture for a mock FluxoAtendimento."""
    fluxo = MagicMock(spec=FluxoAtendimento)
    fluxo.id = 1
    fluxo.nome = "Vendas"
    fluxo.departamento = mock_departamento
    fluxo.departamento_id = mock_departamento.id
    return fluxo


@pytest.fixture
def mock_etapa_fila(mock_fluxo):
    """Fixture for a mock EtapaFluxo of type FILA."""
    etapa = MagicMock(spec=EtapaFluxo)
    etapa.id = 1
    etapa.nome = "Fila de Vendas"
    etapa.fluxo = mock_fluxo
    etapa.fluxo_id = mock_fluxo.id
    etapa.tipo_etapa = (
        "fila"  # Using string to avoid import issue from TipoEtapa
    )
    etapa.ordem = 1
    return etapa


@pytest.fixture
def mock_etapa_atendimento(mock_fluxo):
    """Fixture for a mock EtapaFluxo of type ATENDIMENTO."""
    etapa = MagicMock(spec=EtapaFluxo)
    etapa.id = 2
    etapa.nome = "Em Negociação"
    etapa.fluxo = mock_fluxo
    etapa.fluxo_id = mock_fluxo.id
    etapa.tipo_etapa = (
        "em_atendimento"  # Using string to avoid import issue from TipoEtapa
    )
    etapa.ordem = 2
    return etapa


@pytest.fixture
def mock_contato():
    """Fixture for a mock Contato."""
    contato = MagicMock(spec=Contato)
    contato.id = 1
    contato.telefone = "5511999998888"
    contato.nome_contato = "Cliente Teste"
    return contato


@pytest.fixture
def mock_atendente(mock_departamento):
    """Fixture for a mock Atendente."""
    atendente = MagicMock(spec=Atendente)
    atendente.id = 1
    atendente.nome = "Atendente Teste"
    atendente.departamento = mock_departamento
    atendente.departamento_id = mock_departamento.id
    return atendente


@pytest.fixture
def atendimento_instance(mock_contato):
    """Fixture for a basic Atendimento instance."""
    atendimento = Atendimento(contato=mock_contato)
    # Mock the save method to avoid database hits in all tests
    atendimento.save = MagicMock()
    return atendimento


class TestAtendimentoModel:
    def test_clean_validations_ok(
        self,
        atendimento_instance,
        mock_departamento,
        mock_fluxo,
        mock_etapa_fila,
    ):
        """Tests the clean method validations of the Atendimento model."""
        atendimento = atendimento_instance
        atendimento.departamento = mock_departamento
        atendimento.fluxo_atendimento = mock_fluxo
        atendimento.etapa_atual = mock_etapa_fila

        # This should pass without raising a ValidationError
        atendimento.clean()

    @patch(
        "smart_core_assistant_painel.app.operacional.models.EtapaFluxo.objects.select_related"
    )
    def test_clean_validations_etapa_departamento_mismatch(
        self,
        mock_select_related,
        atendimento_instance,
        mock_departamento,
        mock_fluxo,
        mock_etapa_fila,
    ):
        """Tests validation for etapa_atual belonging to the wrong departamento."""
        atendimento = atendimento_instance
        atendimento.departamento_id = mock_departamento.id
        atendimento.fluxo_atendimento_id = mock_fluxo.id
        atendimento.etapa_atual_id = mock_etapa_fila.id

        other_departamento = MagicMock(spec=Departamento, id=2)
        mock_fluxo.departamento_id = other_departamento.id
        mock_etapa_fila.fluxo = mock_fluxo

        # Make the mock return the etapa with a different department's flux
        mock_select_related.return_value.filter.return_value.first.return_value = mock_etapa_fila

        with pytest.raises(
            ValidationError,
            match="A etapa selecionada não pertence ao departamento escolhido.",
        ):
            atendimento.clean()

    @patch(
        "smart_core_assistant_painel.app.operacional.models.FluxoAtendimento.objects.only"
    )
    def test_clean_validations_fluxo_departamento_mismatch(
        self,
        mock_fluxo_only,
        atendimento_instance,
        mock_departamento,
        mock_fluxo,
        mock_etapa_fila,
    ):
        """Tests validation for fluxo_atendimento belonging to the wrong departamento."""
        atendimento = atendimento_instance
        atendimento.departamento_id = mock_departamento.id
        atendimento.fluxo_atendimento_id = mock_fluxo.id
        atendimento.etapa_atual = (
            None  # remove etapa to isolate the fluxo check
        )
        atendimento.etapa_atual_id = None

        other_departamento = MagicMock(spec=Departamento, id=2)
        mock_fluxo.departamento_id = other_departamento.id

        mock_fluxo_only.return_value.filter.return_value.first.return_value = (
            mock_fluxo
        )

        with pytest.raises(
            ValidationError,
            match="O fluxo selecionado não pertence ao departamento escolhido.",
        ):
            atendimento.clean()

    @patch(
        "smart_core_assistant_painel.app.operacional.models.EtapaFluxo.objects.only"
    )
    def test_clean_validations_etapa_fluxo_mismatch(
        self,
        mock_etapa_only,
        atendimento_instance,
        mock_departamento,
        mock_fluxo,
        mock_etapa_fila,
    ):
        """Tests validation for etapa_atual belonging to the wrong fluxo_atendimento."""
        atendimento = atendimento_instance
        atendimento.departamento = mock_departamento
        atendimento.fluxo_atendimento = mock_fluxo
        atendimento.etapa_atual_id = mock_etapa_fila.id

        other_fluxo = MagicMock(spec=FluxoAtendimento, id=2)
        mock_etapa_fila.fluxo_id = other_fluxo.id

        mock_etapa_only.return_value.filter.return_value.first.return_value = (
            mock_etapa_fila
        )

        with pytest.raises(
            ValidationError,
            match="A etapa selecionada não pertence ao fluxo escolhido.",
        ):
            atendimento.clean()

    def test_finalizar_atendimento(self, atendimento_instance):
        """Tests the finalizar_atendimento method."""
        atendimento = atendimento_instance
        atendimento.finalizar_atendimento()
        assert atendimento.status == "resolvido"
        assert atendimento.data_fim is not None
        assert any(
            "Atendimento finalizado" in h["observacao"]
            for h in atendimento.historico_status
        )

    def test_change_status(self, atendimento_instance):
        """Tests the change_status method."""
        atendimento = atendimento_instance
        atendimento.change_status(
            StatusAtendimento.PENDENCIA, "Aguardando documento"
        )
        assert atendimento.status == StatusAtendimento.PENDENCIA
        assert any(
            "Aguardando documento" in h["observacao"]
            for h in atendimento.historico_status
        )

    def test_assign_to_agent(self, atendimento_instance, mock_atendente):
        """Tests the assign_to_agent method."""
        atendimento = atendimento_instance
        # Ensure initial state
        atendimento.bot_pode_atender = True

        atendimento.assign_to_agent(mock_atendente, "Atribuindo para análise")

        assert atendimento.atendente_humano == mock_atendente
        assert atendimento.status == StatusAtendimento.EM_ATENDIMENTO
        assert atendimento.departamento_id == mock_atendente.departamento_id
        # assign_to_agent NO LONGER sets bot_pode_atender to False automatically
        assert atendimento.bot_pode_atender is True

        assert any(
            "Atribuindo para análise" in h["observacao"]
            for h in atendimento.historico_status
        )
        mock_atendente.save.assert_called_with(
            update_fields=["data_ultima_atribuicao"]
        )

    def test_assumir_atendimento(self, atendimento_instance, mock_atendente):
        """Tests the assumir_atendimento method."""
        atendimento = atendimento_instance
        atendimento.bot_pode_atender = True

        # Mock Atendente.objects.get
        with patch(
            "smart_core_assistant_painel.app.operacional.models.Atendente.objects.get",
            return_value=mock_atendente,
        ):
            atendimento.assumir_atendimento(mock_atendente.id)

        assert atendimento.atendente_humano == mock_atendente
        assert atendimento.bot_pode_atender is False
        atendimento.save.assert_called()

    def test_unassign_agent(self, atendimento_instance, mock_atendente):
        """Tests the unassign_agent method."""
        atendimento = atendimento_instance
        atendimento.atendente_humano = mock_atendente
        atendimento.unassign_agent()
        assert atendimento.atendente_humano is None
        assert atendimento.status == StatusAtendimento.FILA
        assert any(
            "Desatribuído e retornado à fila" in h["observacao"]
            for h in atendimento.historico_status
        )

    def test_transfer_to_department(
        self, atendimento_instance, mock_departamento
    ):
        """Tests the transfer_to_department method."""
        other_dept = MagicMock(spec=Departamento, id=99, nome="Suporte")
        atendimento_instance.departamento = mock_departamento
        atendimento_instance.bot_pode_atender = True

        atendimento_instance.transfer_to_department(
            other_dept, "Transferindo para o suporte"
        )

        assert atendimento_instance.departamento_id == other_dept.id
        assert atendimento_instance.atendente_humano is None
        assert atendimento_instance.status == StatusAtendimento.FILA
        assert atendimento_instance.bot_pode_atender is False
        assert any(
            "Transferindo para o suporte" in h["observacao"]
            for h in atendimento_instance.historico_status
        )

    @patch(
        "smart_core_assistant_painel.app.atendimentos.models.FluxoAtendimento.objects"
    )
    def test_apply_flow_by_description_success(
        self,
        mock_fluxo_objects,
        atendimento_instance,
        mock_fluxo,
        mock_etapa_fila,
    ):
        """Tests successful application of a flow by its description."""
        mock_fluxo.get_etapa_inicial.return_value = mock_etapa_fila
        mock_fluxo_objects.select_related.return_value.filter.return_value.first.return_value = mock_fluxo

        atendimento_instance.apply_flow_by_description("Vendas - Comercial")

        assert atendimento_instance.departamento == mock_fluxo.departamento
        assert atendimento_instance.fluxo_atendimento == mock_fluxo
        assert atendimento_instance.etapa_atual == mock_etapa_fila
        assert atendimento_instance.status == StatusAtendimento.FILA
        atendimento_instance.save.assert_called()

    @patch(
        "smart_core_assistant_painel.app.atendimentos.models.FluxoAtendimento.objects"
    )
    def test_apply_flow_by_description_not_found(
        self, mock_fluxo_objects, atendimento_instance
    ):
        """Tests apply_flow_by_description when the flow is not found."""
        mock_fluxo_objects.select_related.return_value.filter.return_value.first.return_value = None
        with pytest.raises(
            ValidationError,
            match="Fluxo 'Vendas' no departamento 'Comercial' não encontrado.",
        ):
            atendimento_instance.apply_flow_by_description(
                "Vendas - Comercial"
            )

    def test_contexto_methods(self, atendimento_instance):
        """Tests a round-trip of setting and getting context data."""
        atendimento_instance.atualizar_contexto("user_id", 123)
        assert atendimento_instance.contexto_conversa["user_id"] == 123
        atendimento_instance.save.assert_called()

        retrieved_id = atendimento_instance.get_contexto("user_id")
        assert retrieved_id == 123
        assert (
            atendimento_instance.get_contexto("non_existent_key", "default")
            == "default"
        )


class TestMensagemModel:
    def test_registrar_resposta_bot_success(self, atendimento_instance):
        """Tests successful registration of a bot response."""
        mensagem = Mensagem(atendimento=atendimento_instance, conteudo="Olá")
        mensagem.save = MagicMock()

        mensagem.registrar_resposta_bot("Oi, como posso ajudar?", 0.95)

        assert mensagem.resposta_bot == "Oi, como posso ajudar?"
        assert mensagem.confianca_resposta == 0.95
        assert mensagem.respondida is True
        mensagem.save.assert_called_with(
            update_fields=["resposta_bot", "confianca_resposta", "respondida"]
        )

    def test_registrar_resposta_bot_validations(self, atendimento_instance):
        """Tests validations for registrar_resposta_bot."""
        mensagem = Mensagem(
            atendimento=atendimento_instance, conteudo="Dúvida"
        )

        with pytest.raises(
            ValidationError, match="A resposta do bot não pode ser vazia."
        ):
            mensagem.registrar_resposta_bot("", 0.9)

        with pytest.raises(
            ValidationError,
            match="O parâmetro 'confianca' deve estar entre 0 e 1.",
        ):
            mensagem.registrar_resposta_bot("Resposta", 1.1)

        with pytest.raises(
            ValidationError,
            match="O parâmetro 'confianca' deve ser um número entre 0 e 1.",
        ):
            mensagem.registrar_resposta_bot("Resposta", "invalid_confidence")


@patch("smart_core_assistant_painel.app.atendimentos.models.Contato.objects")
@patch(
    "smart_core_assistant_painel.app.atendimentos.models.Atendimento.objects"
)
class TestAtendimentoFunctions:
    def test_inicializar_atendimento_whatsapp_new_contato(
        self, mock_atendimento_objects, mock_contato_objects
    ):
        """Tests initializing a service for a new WhatsApp contact."""
        mock_contato_objects.get_or_create.return_value = (
            MagicMock(spec=Contato),
            True,
        )
        mock_atendimento_objects.filter.return_value.first.return_value = (
            None  # No active atendimento
        )
        mock_atendimento_objects.create.return_value = MagicMock(
            spec=Atendimento
        )

        contato, atendimento = inicializar_atendimento_whatsapp(
            numero_telefone="5511987654321"
        )

        mock_contato_objects.get_or_create.assert_called_once()
        mock_atendimento_objects.create.assert_called_once()
        assert contato is not None
        assert atendimento is not None

    def test_inicializar_atendimento_whatsapp_existing_active(
        self, mock_atendimento_objects, mock_contato_objects
    ):
        """Tests reusing an existing active atendimento."""
        mock_contato, _ = mock_contato_objects.get_or_create.return_value
        mock_active_atendimento = MagicMock(spec=Atendimento)
        mock_atendimento_objects.filter.return_value.first.return_value = (
            mock_active_atendimento
        )

        contato, atendimento = inicializar_atendimento_whatsapp(
            numero_telefone="5511987654321"
        )

        mock_atendimento_objects.create.assert_not_called()
        assert atendimento == mock_active_atendimento

    @patch(
        "smart_core_assistant_painel.app.atendimentos.models.Mensagem.objects"
    )
    @patch(
        "smart_core_assistant_painel.app.atendimentos.models.buscar_atendimento_ativo"
    )
    def test_processar_mensagem_whatsapp(
        self, mock_buscar_ativo, mock_mensagem_objects
    ):
        """Tests processing a WhatsApp message."""
        mock_atendimento = MagicMock(spec=Atendimento)
        mock_atendimento.id = 1
        mock_atendimento.contato = MagicMock(spec=Contato)
        mock_buscar_ativo.return_value = mock_atendimento
        mock_mensagem_objects.create.return_value = MagicMock(
            spec=Mensagem, id=123
        )

        mensagem_id = processar_mensagem_whatsapp(
            numero_telefone="5511999998888",
            conteudo="Oi, tudo bem?",
            message_type="conversation",
            message_id="wamid.12345",
            from_me=False,
        )

        mock_mensagem_objects.create.assert_called_once()
        created_msg_args = mock_mensagem_objects.create.call_args[1]
        assert created_msg_args["atendimento"] == mock_atendimento
        assert created_msg_args["remetente"] == TipoRemetente.CONTATO
        assert created_msg_args["tipo"] == TipoMensagem.TEXTO_FORMATADO
        assert created_msg_args["tipo"] == TipoMensagem.TEXTO_FORMATADO
        assert mensagem_id == 123

    @patch(
        "smart_core_assistant_painel.app.atendimentos.models.Mensagem.objects"
    )
    @patch(
        "smart_core_assistant_painel.app.atendimentos.models.buscar_atendimento_ativo_por_contato"
    )
    @patch(
        "smart_core_assistant_painel.app.atendimentos.models.Contato.objects"
    )
    def test_processar_mensagem_por_contato_human_message(
        self, mock_contato_objects, mock_buscar_ativo, mock_mensagem_objects
    ):
        """Tests processing a message from a human agent."""
        mock_contato = MagicMock(spec=Contato)
        mock_contato_objects.filter.return_value.first.return_value = (
            mock_contato
        )

        mock_atendimento = MagicMock(spec=Atendimento)
        mock_atendimento.id = 1
        mock_atendimento.bot_pode_atender = True
        mock_buscar_ativo.return_value = mock_atendimento

        mock_mensagem_objects.create.return_value = MagicMock(
            spec=Mensagem, id=456
        )

        processar_mensagem_por_contato(
            contato_id=1,
            conteudo="Olá, sou o atendente.",
            message_type="text",
            message_id="wamid.999",
            from_me=True,
        )

        # Verify bot_pode_atender is set to False
        assert mock_atendimento.bot_pode_atender is False
        # Verify save was called with update_fields
        mock_atendimento.save.assert_called_with(
            update_fields=["bot_pode_atender"]
        )

        # Verify message creation
        mock_mensagem_objects.create.assert_called_once()
        created_msg_args = mock_mensagem_objects.create.call_args[1]
        assert created_msg_args["remetente"] == TipoRemetente.ATENDENTE_HUMANO
