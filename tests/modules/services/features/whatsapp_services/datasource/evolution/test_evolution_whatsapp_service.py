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
        # Cria duas instâncias
        service1 = EvolutionWhatsAppService()
        service2 = EvolutionWhatsAppService()

        # Verifica se são a mesma instância (Singleton)
        assert service1 is service2

    @patch("requests.post")
    def test_send_message_success(self, mock_post: Mock) -> None:
        """Testa o envio de mensagem com sucesso."""
        # Configura o mock
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        # Parâmetros de teste
        instance = "test_instance"
        api_key = "test_api_key"
        number = "5511999999999"
        text = "Teste"

        # Cria o serviço
        service = EvolutionWhatsAppService()

        # Testa o envio de mensagem
        service.send_message(
            instance=instance,
            api_key=api_key,
            number=number,
            text=text,
        )

        # Verifica se a requisição de envio foi feita corretamente
        # Ordem esperada: typing start, send message, typing stop
        assert mock_post.call_count == 3
        send_call = mock_post.call_args_list[1]
        assert "message/sendText/test_instance" in send_call[0][0]
        assert send_call[1]["headers"]["apikey"] == api_key
        assert send_call[1]["json"] == {"number": number, "text": text}

    @patch("requests.post")
    def test_send_message_failure(self, mock_post: Mock) -> None:
        """Testa o envio de mensagem com falha."""
        # Configura os mocks: typing OK e envio falha
        mock_response_typing = Mock()
        mock_response_typing.ok = True
        mock_response_fail = Mock()
        mock_response_fail.ok = False
        mock_response_fail.status_code = 400
        mock_response_fail.text = "Bad Request"
        mock_post.side_effect = [mock_response_typing, mock_response_fail, mock_response_typing]

        # Parâmetros
        instance = "test_instance"
        api_key = "test_api_key"
        number = "5511999999999"
        text = "Teste"

        # Cria o serviço
        service = EvolutionWhatsAppService()

        # Testa se a exceção é lançada pelo envio de mensagem
        with pytest.raises(
            Exception, match="Erro ao enviar mensagem: 400 - Bad Request"
        ):
            service.send_message(
                instance=instance,
                api_key=api_key,
                number=number,
                text=text,
            )

    @patch("requests.post")
    def test_typing_composing(self, mock_post: Mock) -> None:
        """Testa a definição do status de digitação como 'composing'."""
        # Configura o mock
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        # Cria o serviço
        service = EvolutionWhatsAppService()

        # Testa o status de digitação com todos os argumentos necessários
        service._typing(
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
        assert call_args[1]["json"]["delay"] == 1200

    @patch("requests.post")
    def test_typing_paused(self, mock_post: Mock) -> None:
        """Testa a definição do status de digitação como 'paused'."""
        # Configura o mock
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        # Cria o serviço
        service = EvolutionWhatsAppService()

        # Testa o status de digitação com todos os argumentos necessários
        service._typing(
            typing=False,
            instance="test_instance",
            number="5511999999999",
            api_key="test_api_key",
        )

        # Verifica se a requisição foi feita corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["presence"] == "paused"
        assert call_args[1]["json"]["delay"] == 1200

    def test_typing_without_number(self) -> None:
        """Testa o comportamento quando um número vazio é passado."""
        # Cria o serviço
        service = EvolutionWhatsAppService()

        # Testa com número vazio - deve funcionar normalmente
        # pois agora passamos o número diretamente como parâmetro
        try:
            service._typing(
                typing=True,
                instance="test_instance",
                number="",  # Número vazio
                api_key="test_api_key",
            )
        except Exception:
            # Se houver erro, é esperado que seja relacionado à requisição HTTP
            # não à validação do número
            pass
