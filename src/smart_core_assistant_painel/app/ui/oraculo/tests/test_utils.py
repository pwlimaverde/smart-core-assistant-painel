"""Testes para as funções utilitárias do Oráculo."""

import pytest
import json
from unittest.mock import patch, MagicMock, call
from django.utils import timezone
from smart_core_assistant_painel.app.ui.oraculo import utils
from smart_core_assistant_painel.modules.ai_engine import MessageData
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.domain.interface.analise_previa_mensagem import AnalisePreviaMensagem
from smart_core_assistant_painel.app.ui.oraculo.models import Atendimento, Contato, Mensagem, TipoRemetente


def create_message_data(**kwargs):
    """Cria uma instância de MessageData com valores padrão para testes."""
    defaults = {
        "instance": "test_instance",
        "api_key": "test_key",
        "numero_telefone": "123456789",
        "from_me": False,
        "conteudo": "Olá, mundo!",
        "message_type": "text",
        "message_id": "msg123",
        "metadados": None,
        "nome_perfil_whatsapp": "Teste",
    }
    defaults.update(kwargs)
    return MessageData(**defaults)


class TestWaBuffer:
    """Testes para as funções de buffer do WhatsApp."""

    @patch("smart_core_assistant_painel.app.ui.oraculo.utils.cache")
    @patch("smart_core_assistant_painel.app.ui.oraculo.utils.SERVICEHUB")
    def test_set_wa_buffer(self, mock_service_hub, mock_cache):
        """Testa se a mensagem é adicionada ao buffer no cache."""
        mock_cache.get.return_value = []
        mock_service_hub.TIME_CACHE = 60
        message = create_message_data(numero_telefone="12345", conteudo="teste")

        utils.set_wa_buffer(message)

        mock_cache.get.assert_called_once_with("wa_buffer_12345", [])
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert args[0] == "wa_buffer_12345"
        assert args[1] == [message]
        assert "timeout" in kwargs
        assert kwargs["timeout"] == 180

    @patch("smart_core_assistant_painel.app.ui.oraculo.utils.cache")
    def test_clear_wa_buffer(self, mock_cache):
        """Testa se o buffer e o timer são removidos do cache."""
        phone = "12345"
        utils.clear_wa_buffer(phone)
        expected_calls = [
            call.delete("wa_buffer_12345"),
            call.delete("wa_timer_12345"),
        ]
        mock_cache.assert_has_calls(expected_calls, any_order=True)


class TestCompileMessageData:
    """Testes para a função _compile_message_data_list."""

    def test_compile_single_message(self):
        message = create_message_data(conteudo="conteudo 1", metadados={"m1": "v1"})
        result = utils._compile_message_data_list([message])
        assert result.conteudo == "conteudo 1"
        assert result.metadados == {"m1": "v1"}

    def test_compile_multiple_messages(self):
        messages = [
            create_message_data(conteudo="conteudo 1", metadados={"m1": "v1"}),
            create_message_data(conteudo="conteudo 2", metadados={"m2": "v2"}),
        ]
        result = utils._compile_message_data_list(messages)
        assert result.conteudo == "conteudo 1\nconteudo 2"
        assert result.metadados == {"m1": "v1", "m2": "v2"}

    def test_compile_with_empty_content(self):
        messages = [
            create_message_data(conteudo="conteudo 1"),
            create_message_data(conteudo="  "),
            create_message_data(conteudo=None),
        ]
        result = utils._compile_message_data_list(messages)
        assert result.conteudo == "conteudo 1"

    def test_compile_empty_list_raises_error(self):
        with pytest.raises(ValueError):
            utils._compile_message_data_list([])

    def test_compile_invalid_type_raises_error(self):
        with pytest.raises(ValueError):
            utils._compile_message_data_list("not a list")


@patch("smart_core_assistant_painel.app.ui.oraculo.utils.clear_wa_buffer")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils._analisar_conteudo_mensagem")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils.processar_mensagem_whatsapp")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils._compile_message_data_list")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils.cache")
class TestSendMessageResponse:
    """Testes para a função send_message_response."""

    def test_send_message_empty_buffer(self, mock_cache, mock_compile, mock_processar, mock_analisar, mock_clear):
        mock_cache.get.return_value = []
        utils.send_message_response("some_phone")
        mock_compile.assert_not_called()

    @patch("smart_core_assistant_painel.app.ui.oraculo.models.Mensagem.objects.get")
    @patch("smart_core_assistant_painel.app.ui.oraculo.utils._pode_bot_responder_atendimento", return_value=True)
    @patch("smart_core_assistant_painel.app.ui.oraculo.models.Treinamentos.build_similarity_context", return_value="")
    @patch("smart_core_assistant_painel.app.ui.oraculo.utils.SERVICEHUB")
    def test_send_message_success(self, mock_service_hub, mock_similarity, mock_pode_responder, mock_msg_get, mock_cache, mock_compile, mock_processar, mock_analisar, mock_clear):
        phone = "12345"
        message_data = create_message_data(numero_telefone=phone)
        mock_cache.get.return_value = [message_data]
        mock_compile.return_value = message_data
        mock_processar.return_value = 1
        
        # Configurar mock da mensagem com conteúdo real
        mock_mensagem = MagicMock()
        mock_mensagem.conteudo = "Olá, mundo!"
        mock_mensagem.atendimento = MagicMock()
        mock_msg_get.return_value = mock_mensagem

        utils.send_message_response(phone)

        mock_service_hub.whatsapp_service.send_message.assert_called_once()
        mock_clear.assert_called_once_with(phone)

    @patch("smart_core_assistant_painel.app.ui.oraculo.models.Mensagem.objects.get", side_effect=utils.Mensagem.DoesNotExist)
    def test_send_message_mensagem_not_found(self, mock_msg_get, mock_cache, mock_compile, mock_processar, mock_analisar, mock_clear):
        phone = "12345"
        message_data = create_message_data(numero_telefone=phone)
        mock_cache.get.return_value = [message_data]
        mock_compile.return_value = message_data
        mock_processar.return_value = 999

        utils.send_message_response(phone)
        mock_analisar.assert_not_called()


@patch("smart_core_assistant_painel.app.ui.oraculo.utils.mensagem_bufferizada.send")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils.SERVICEHUB")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils.cache")
class TestSchedMessageResponse:
    """Testes para a função sched_message_response."""

    def test_sched_message_timer_not_set(self, mock_cache, mock_service_hub, mock_signal_send):
        mock_cache.get.return_value = None
        mock_service_hub.TIME_CACHE = 60
        phone = "12345"
        utils.sched_message_response(phone)
        mock_cache.get.assert_called_once_with("wa_timer_12345")
        mock_cache.set.assert_called_once_with("wa_timer_12345", True, timeout=180)
        mock_signal_send.assert_called_once_with(sender="oraculo", phone=phone)

    def test_sched_message_timer_is_set(self, mock_cache, mock_service_hub, mock_signal_send):
        mock_cache.get.return_value = True
        phone = "12345"
        utils.sched_message_response(phone)
        mock_cache.get.assert_called_once_with("wa_timer_12345")
        mock_cache.set.assert_not_called()
        mock_signal_send.assert_not_called()


class TestPodeBotResponder:
    """Testes para a função _pode_bot_responder_atendimento."""

    def test_pode_responder_sem_atendente_e_sem_msg_humana(self):
        mock_atendimento = MagicMock(spec=Atendimento)
        mock_atendimento.atendente_humano = None
        mock_atendimento.mensagens.filter.return_value.exists.return_value = False
        assert utils._pode_bot_responder_atendimento(mock_atendimento) is True

    def test_nao_pode_responder_com_atendente(self):
        mock_atendimento = MagicMock(spec=Atendimento)
        mock_atendimento.atendente_humano = "alguem"
        assert utils._pode_bot_responder_atendimento(mock_atendimento) is False

    def test_nao_pode_responder_com_msg_humana(self):
        mock_atendimento = MagicMock(spec=Atendimento)
        mock_atendimento.atendente_humano = None
        mock_atendimento.mensagens.filter.return_value.exists.return_value = True
        assert utils._pode_bot_responder_atendimento(mock_atendimento) is False

    def test_atendimento_nulo(self):
        assert utils._pode_bot_responder_atendimento(None) is False

    def test_erro_na_verificacao(self):
        mock_atendimento = MagicMock(spec=Atendimento)
        mock_atendimento.mensagens.filter.side_effect = Exception("DB Error")
        assert utils._pode_bot_responder_atendimento(mock_atendimento) is False


@patch("smart_core_assistant_painel.app.ui.oraculo.utils.FeaturesCompose")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils.Mensagem.objects.get")
@patch("smart_core_assistant_painel.app.ui.oraculo.models.Atendimento.objects.filter")
class TestAnalisarConteudoMensagem:
    """Testes para a função _analisar_conteudo_mensagem."""

    def test_analise_com_sucesso(self, mock_filter, mock_msg_get, mock_features_compose):
        mock_atendimento = MagicMock(spec=Atendimento, id=1)
        mock_mensagem = MagicMock(spec=Mensagem, atendimento=mock_atendimento)
        mock_msg_get.return_value = mock_mensagem
        mock_atendimento.carregar_historico_mensagens.return_value = {"conteudo_mensagens": ["oi"]}
        mock_features_compose.analise_previa_mensagem.return_value = AnalisePreviaMensagem(intent=[{"saudacao": "oi"}], entities=[])

        with patch("smart_core_assistant_painel.app.ui.oraculo.utils._processar_entidades_contato") as mock_proc_entidades:
            utils._analisar_conteudo_mensagem(1)

            mock_atendimento.carregar_historico_mensagens.assert_called_once_with(excluir_mensagem_id=1)
            mock_features_compose.analise_previa_mensagem.assert_called_once()
            mock_mensagem.save.assert_called_once()
            mock_proc_entidades.assert_called_once()

    def test_chama_apresentacao_se_novo_atendimento(self, mock_filter, mock_msg_get, mock_features_compose):
        mock_atendimento = MagicMock(spec=Atendimento, id=1)
        mock_mensagem = MagicMock(spec=Mensagem, atendimento=mock_atendimento)
        mock_msg_get.return_value = mock_mensagem
        mock_atendimento.carregar_historico_mensagens.return_value = {}
        mock_filter.return_value.exclude.return_value.exists.return_value = False

        utils._analisar_conteudo_mensagem(1)
        mock_features_compose.mensagem_apresentacao.assert_called_once()

    def test_nao_chama_apresentacao_se_atendimento_antigo(self, mock_filter, mock_msg_get, mock_features_compose):
        mock_atendimento = MagicMock(spec=Atendimento, id=1)
        mock_mensagem = MagicMock(spec=Mensagem, atendimento=mock_atendimento)
        mock_msg_get.return_value = mock_mensagem
        mock_atendimento.carregar_historico_mensagens.return_value = {}
        mock_filter.return_value.exclude.return_value.exists.return_value = True

        utils._analisar_conteudo_mensagem(1)
        mock_features_compose.mensagem_apresentacao.assert_not_called()


@patch("smart_core_assistant_painel.app.ui.oraculo.utils.SERVICEHUB")
class TestObterEntidadesMetadadosValidas:
    """Testes para a função _obter_entidades_metadados_validas."""

    def test_com_entidades_validas(self, mock_service_hub):
        mock_service_hub.VALID_ENTITY_TYPES = json.dumps({
            "entity_types": {
                "dados_pessoais": {"nome_contato": "Nome", "cpf": "CPF", "email": "Email"},
                "localizacao": {"cidade": "Cidade", "estado": "Estado"}
            }
        })
        expected = {"cpf", "email", "cidade", "estado"}
        assert utils._obter_entidades_metadados_validas() == expected

    def test_com_json_invalido(self, mock_service_hub):
        mock_service_hub.VALID_ENTITY_TYPES = "json_invalido"
        assert utils._obter_entidades_metadados_validas() == set()

    def test_sem_entidades(self, mock_service_hub):
        mock_service_hub.VALID_ENTITY_TYPES = "{}"
        assert utils._obter_entidades_metadados_validas() == set()


@patch("smart_core_assistant_painel.app.ui.oraculo.utils._obter_entidades_metadados_validas")
@patch("smart_core_assistant_painel.app.ui.oraculo.utils.FeaturesCompose")
class TestProcessarEntidadesContato:
    """Testes para a função _processar_entidades_contato."""

    def test_atualiza_nome_e_metadados(self, mock_features_compose, mock_obter_entidades):
        mock_obter_entidades.return_value = {"cpf", "email"}
        mock_contato = MagicMock(spec=Contato, nome_contato="Antigo", metadados={})
        mock_mensagem = MagicMock(spec=Mensagem, atendimento=MagicMock(spec=Atendimento, contato=mock_contato))

        entities = [{"nome_contato": "Novo Nome"}, {"cpf": "123"}, {"ignored": "value"}]
        utils._processar_entidades_contato(mock_mensagem, entities)

        assert mock_contato.nome_contato == "Novo Nome"
        assert mock_contato.metadados == {"cpf": "123"}
        mock_contato.save.assert_called_once()

    def test_nao_atualiza_nome_menor(self, mock_features_compose, mock_obter_entidades):
        mock_obter_entidades.return_value = set()
        mock_contato = MagicMock(spec=Contato, nome_contato="NomeLongo", metadados={})
        mock_mensagem = MagicMock(spec=Mensagem, atendimento=MagicMock(spec=Atendimento, contato=mock_contato))

        entities = [{"nome_contato": "Curto"}]
        utils._processar_entidades_contato(mock_mensagem, entities)

        assert mock_contato.nome_contato == "NomeLongo"
        mock_contato.save.assert_not_called()
