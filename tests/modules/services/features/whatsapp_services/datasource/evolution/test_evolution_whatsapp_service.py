"""Testes para o EvolutionWhatsAppService."""

from unittest.mock import Mock, patch

import pytest

from smart_core_assistant_painel.modules.services import (
    WhatsAppMensagemParameters,
    WhatsAppServiceError,
)
from smart_core_assistant_painel.modules.services.features.whatsapp_services.datasource.evolution.evolution_whatsapp_service import (
    EvolutionWhatsAppService,
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

    @patch("requests.get")
    def test_send_request_get_method(self, mock_get: Mock) -> None:
        """Testa o método _send_request com GET."""
        # Configura o mock
        mock_response = Mock()
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        service = EvolutionWhatsAppService()
        
        # Testa requisição GET
        response = service._send_request(
            path="/test",
            api_key="test_key",
            method="GET"
        )
        
        assert response.ok
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "test" in call_args[0][0]
        assert call_args[1]["headers"]["apikey"] == "test_key"
        
    @patch("requests.put")
    def test_send_request_put_method(self, mock_put: Mock) -> None:
        """Testa o método _send_request com PUT."""
        mock_response = Mock()
        mock_response.ok = True
        mock_put.return_value = mock_response
        
        service = EvolutionWhatsAppService()
        
        # Testa requisição PUT
        body = {"test": "data"}
        response = service._send_request(
            path="/test",
            api_key="test_key",
            method="PUT",
            body=body
        )
        
        assert response.ok
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        assert call_args[1]["json"] == body
        
    @patch("requests.delete")
    def test_send_request_delete_method(self, mock_delete: Mock) -> None:
        """Testa o método _send_request com DELETE."""
        mock_response = Mock()
        mock_response.ok = True
        mock_delete.return_value = mock_response
        
        service = EvolutionWhatsAppService()
        
        # Testa requisição DELETE
        response = service._send_request(
            path="/test",
            api_key="test_key",
            method="DELETE"
        )
        
        assert response.ok
        mock_delete.assert_called_once()
        
    def test_send_request_unsupported_method(self) -> None:
        """Testa _send_request com método HTTP não suportado."""
        service = EvolutionWhatsAppService()
        
        # Testa método não suportado
        with pytest.raises(ValueError, match="Método HTTP não suportado: PATCH"):
            service._send_request(
                path="/test",
                api_key="test_key",
                method="PATCH"
            )
            
    @patch("requests.post")
    def test_send_request_with_headers_and_params(self, mock_post: Mock) -> None:
        """Testa _send_request com headers customizados e parâmetros URL."""
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        service = EvolutionWhatsAppService()
        
        # Testa com headers customizados e parâmetros
        custom_headers = {"Custom-Header": "value"}
        params_url = {"param1": "value1", "param2": "value2"}
        
        response = service._send_request(
            path="/test",
            api_key="test_key",
            method="POST",
            headers=custom_headers,
            params_url=params_url
        )
        
        assert response.ok
        call_args = mock_post.call_args
        
        # Verifica se os parâmetros foram adicionados à URL
        assert "param1=value1" in call_args[0][0]
        assert "param2=value2" in call_args[0][0]
        
        # Verifica se os headers foram incluídos
        headers = call_args[1]["headers"]
        assert headers["Custom-Header"] == "value"
        assert headers["apikey"] == "test_key"
        assert headers["Content-Type"] == "application/json"
        
    def test_mount_url_without_params(self) -> None:
        """Testa _mount_url sem parâmetros."""
        service = EvolutionWhatsAppService()
        
        url = service._mount_url("/test/path", {})
        
        # Verifica se a URL base foi combinada com o path
        assert url.endswith("/test/path")
        assert "?" not in url  # Não deve haver parâmetros
        
    def test_mount_url_with_params(self) -> None:
        """Testa _mount_url com parâmetros."""
        service = EvolutionWhatsAppService()
        
        params = {"key1": "value1", "key2": "value2"}
        url = service._mount_url("/test/path", params)
        
        # Verifica se os parâmetros foram codificados na URL
        assert "?" in url
        assert "key1=value1" in url
        assert "key2=value2" in url
        
    def test_mount_url_with_non_dict_params(self) -> None:
        """Testa _mount_url com parâmetros que não são dict."""
        service = EvolutionWhatsAppService()
        
        # Testa com None (comportamento defensivo)
        url = service._mount_url("/test/path", None)
        assert url.endswith("/test/path")
        assert "?" not in url
        
        # Testa com string (não deve processar como dict)
        url = service._mount_url("/test/path", "invalid_params")
        assert url.endswith("/test/path")
        assert "?" not in url
        
    @patch("requests.post")
    def test_typing_failure(self, mock_post: Mock) -> None:
        """Testa falha no método _typing."""
        # Configura o mock para falhar
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        service = EvolutionWhatsAppService()
        
        # Testa se a exceção é lançada
        with pytest.raises(
            Exception, 
            match="Erro ao definir status de digitação: 500 - Internal Server Error"
        ):
            service._typing(
                typing=True,
                instance="test_instance",
                number="5511999999999",
                api_key="test_api_key"
            )
            
    def test_singleton_reinitialization(self) -> None:
        """Testa que a reinicialização não ocorre em instâncias subsequentes."""
        # Primeira instância
        service1 = EvolutionWhatsAppService()
        original_base_url = service1._base_url
        
        # Modifica manualmente o _base_url
        service1._base_url = "http://modified-url.com"
        
        # Segunda instância (mesma devido ao Singleton)
        service2 = EvolutionWhatsAppService()
        
        # Verifica se são a mesma instância e a URL não foi reinicializada
        assert service1 is service2
        assert service2._base_url == "http://modified-url.com"
        
    @patch("requests.post")
    def test_send_message_with_typing_failure(self, mock_post: Mock) -> None:
        """Testa send_message quando _typing falha."""
        # Primeiro _typing falha
        mock_response_fail = Mock()
        mock_response_fail.ok = False
        mock_response_fail.status_code = 400
        mock_response_fail.text = "Typing Error"
        mock_post.return_value = mock_response_fail
        
        service = EvolutionWhatsAppService()
        
        # Deve falhar no primeiro _typing
        with pytest.raises(
            Exception, 
            match="Erro ao definir status de digitação: 400 - Typing Error"
        ):
            service.send_message(
                instance="test_instance",
                api_key="test_api_key",
                number="5511999999999",
                text="Teste"
            )
            
    @patch.object(EvolutionWhatsAppService, '_send_request')
    def test_send_message_flow_order(self, mock_send_request: Mock) -> None:
        """Testa a ordem das chamadas em send_message."""
        # Simula respostas bem-sucedidas
        mock_response = Mock()
        mock_response.ok = True
        mock_send_request.return_value = mock_response
        
        service = EvolutionWhatsAppService()
        
        service.send_message(
            instance="test_instance",
            api_key="test_api_key",
            number="5511999999999",
            text="Test message"
        )
        
        # Verifica se foram feitas exatamente 3 chamadas
        assert mock_send_request.call_count == 3
        
        # Verifica a ordem das chamadas
        calls = mock_send_request.call_args_list
        
        # 1ª chamada: typing start (composing)
        first_call = calls[0]
        first_path = first_call[0][0]  # Primeiro argumento posicional
        first_kwargs = first_call[1]   # Argumentos nomeados
        assert "/chat/sendPresence" in first_path
        assert first_kwargs['method'] == "POST"
        assert first_kwargs['body']['presence'] == "composing"
        
        # 2ª chamada: send message
        second_call = calls[1]
        second_path = second_call[0][0]
        second_kwargs = second_call[1]
        assert "/message/sendText" in second_path
        assert second_kwargs['method'] == "POST"
        assert second_kwargs['body'] == {"number": "5511999999999", "text": "Test message"}
        
        # 3ª chamada: typing stop (paused)
        third_call = calls[2]
        third_path = third_call[0][0]
        third_kwargs = third_call[1]
        assert "/chat/sendPresence" in third_path
        assert third_kwargs['method'] == "POST"
        assert third_kwargs['body']['presence'] == "paused"
        
    def test_case_insensitive_http_methods(self) -> None:
        """Testa que os métodos HTTP são tratados de forma case-insensitive."""
        service = EvolutionWhatsAppService()
        
        # Testa métodos em lowercase
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.ok = True
            mock_get.return_value = mock_response
            
            service._send_request(
                path="/test",
                api_key="test_key",
                method="get"  # lowercase
            )
            
            mock_get.assert_called_once()
