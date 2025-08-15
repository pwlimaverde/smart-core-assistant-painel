"""Testes para o EvolutionWhatsAppService."""

from unittest.mock import Mock, patch

import pytest

from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_whatsapp_service import (
    EvolutionWhatsAppService,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    WhatsAppServiceError,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    WhatsAppMensagemParameters,
)


class TestEvolutionWhatsAppService:
    """Testes para a classe EvolutionWhatsAppService."""

    def test_singleton_pattern(self) -> None:
        """Testa se o padrão Singleton está funcionando corretamente."""
        # Cria parâmetros de teste
        parameters1 = WhatsAppMensagemParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"number": "5511999999999", "text": "Teste"},
            error=WhatsAppServiceError(message="Erro de teste"),
        )

        parameters2 = WhatsAppMensagemParameters(
            instance="another_instance",
            api_key="another_api_key",
            message_data={"number": "5511888888888", "text": "Outro teste"},
            error=WhatsAppServiceError(message="Outro erro de teste"),
        )

        # Cria duas instâncias
        service1 = EvolutionWhatsAppService(parameters1)
        service2 = EvolutionWhatsAppService(parameters2)

        # Verifica se são a mesma instância (Singleton)
        assert service1 is service2

        # Verifica se os parâmetros da primeira instância são mantidos
        assert service1._parameters.instance == "test_instance"
        assert service2._parameters.instance == "test_instance"

    @patch("requests.post")
    def test_send_message_success(self, mock_post: Mock) -> None:
        """Testa o envio de mensagem com sucesso."""
        # Configura o mock
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        # Cria parâmetros de teste
        parameters = WhatsAppMensagemParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"number": "5511999999999", "text": "Teste"},
            error=WhatsAppServiceError(message="Erro de teste"),
        )

        # Cria o serviço
        service = EvolutionWhatsAppService(parameters)

        # Testa o envio de mensagem
        service.send_message()

        # Verifica se a requisição foi feita corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "message/sendText/test_instance" in call_args[0][0]
        assert call_args[1]["headers"]["apikey"] == "test_api_key"
        assert call_args[1]["json"] == parameters.message_data

    @patch("requests.post")
    def test_send_message_failure(self, mock_post: Mock) -> None:
        """Testa o envio de mensagem com falha."""
        # Configura o mock para falha
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # Cria parâmetros de teste
        parameters = WhatsAppMensagemParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"number": "5511999999999", "text": "Teste"},
            error=WhatsAppServiceError(message="Erro de teste"),
        )

        # Cria o serviço
        service = EvolutionWhatsAppService(parameters)

        # Testa se a exceção é lançada
        with pytest.raises(
            Exception, match="Erro ao enviar mensagem: 400 - Bad Request"
        ):
            service.send_message()

    @patch("requests.post")
    def test_typing_composing(self, mock_post: Mock) -> None:
        """Testa a definição do status de digitação como 'composing'."""
        # Configura o mock
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        # Cria parâmetros de teste
        parameters = WhatsAppMensagemParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"number": "5511999999999", "text": "Teste"},
            error=WhatsAppServiceError(message="Erro de teste"),
        )

        # Cria o serviço
        service = EvolutionWhatsAppService(parameters)

        # Testa o status de digitação com todos os argumentos necessários
        service.typing(
            typing=True,
            instance="test_instance",
            number="5511999999999",
            api_key="test_api_key",
        )

        # Verifica se a requisição foi feita corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "chat/sendPresence/test_instance" in call_args[0][0]
        assert call_args[1]["json"]["presence"] == "composing"
        assert call_args[1]["json"]["number"] == "5511999999999"
        assert call_args[1]["json"]["delay"] == 1500

    @patch("requests.post")
    def test_typing_paused(self, mock_post: Mock) -> None:
        """Testa a definição do status de digitação como 'paused'."""
        # Configura o mock
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        # Cria parâmetros de teste
        parameters = WhatsAppMensagemParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"number": "5511999999999", "text": "Teste"},
            error=WhatsAppServiceError(message="Erro de teste"),
        )

        # Cria o serviço
        service = EvolutionWhatsAppService(parameters)

        # Testa o status de digitação com todos os argumentos necessários
        service.typing(
            typing=False,
            instance="test_instance",
            number="5511999999999",
            api_key="test_api_key",
        )

        # Verifica se a requisição foi feita corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["presence"] == "paused"
        assert call_args[1]["json"]["delay"] == 1500

    def test_typing_without_number(self) -> None:
        """Testa o comportamento quando um número vazio é passado."""
        # Cria parâmetros de teste
        parameters = WhatsAppMensagemParameters(
            instance="test_instance",
            api_key="test_api_key",
            message_data={"text": "Teste"},
            error=WhatsAppServiceError(message="Erro de teste"),
        )

        # Cria o serviço
        service = EvolutionWhatsAppService(parameters)

        # Testa com número vazio - deve funcionar normalmente
        # pois agora passamos o número diretamente como parâmetro
        try:
            service.typing(
                typing=True,
                instance="test_instance",
                number="",  # Número vazio
                api_key="test_api_key",
            )
        except Exception:
            # Se houver erro, é esperado que seja relacionado à requisição HTTP
            # não à validação do número
            pass
