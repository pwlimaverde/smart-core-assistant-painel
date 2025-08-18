"""Módulo para integração com a API de WhatsApp Evolution.

Este módulo fornece uma implementação do serviço de WhatsApp (`WhatsAppService`)
utilizando a Evolution API como backend. Ele encapsula a comunicação HTTP,
o envio de mensagens e o controle de status (como "digitando").

Classes:
    _EvolutionWhatsAppServiceMeta: Metaclasse para garantir o padrão Singleton.
    EvolutionWhatsAppService: Serviço principal para interação com a Evolution API.
"""

from abc import ABCMeta
from typing import Any, Dict, Optional, Callable
from urllib.parse import urlencode, urljoin

import requests

from smart_core_assistant_painel.modules.services.features.service_hub import SERVICEHUB
from smart_core_assistant_painel.modules.services.features.whatsapp_services.domain.interface.whatsapp_service import (
    WhatsAppService,
)


class _EvolutionWhatsAppServiceMeta(ABCMeta):
    """Metaclasse para implementar o padrão Singleton com suporte a ABC."""

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class EvolutionWhatsAppService(
    WhatsAppService, metaclass=_EvolutionWhatsAppServiceMeta
):
    """Serviço para interagir com a API do WhatsApp através da Evolution API.

    Esta classe implementa a interface `WhatsAppService` e gerencia a
    comunicação com a API Evolution para enviar mensagens e realizar outras
    ações no WhatsApp. Utiliza o padrão Singleton para garantir uma única
    instância.

    Attributes:
        _base_url (str): A URL base da API Evolution.
        _initialized (bool): Flag para garantir que a inicialização ocorra
                             apenas uma vez.
    """

    def __init__(self) -> None:
        """Inicializa o serviço da Evolution API.

        A inicialização real ocorre apenas na primeira vez que a classe é
        instanciada, devido ao padrão Singleton.
        """
        # Evita reinicialização em instâncias subsequentes do Singleton
        if hasattr(self, "_initialized"):
            return

        self._base_url = SERVICEHUB.WHATSAPP_API_BASE_URL
        self._initialized = True

    def _send_request(
        self,
        path: str,
        api_key: str,
        method: str = "GET",
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params_url: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Envia uma requisição HTTP para a API do Evolution.

        Args:
            path (str): O caminho do endpoint da API (ex: '/messages/send').
            api_key (str): A chave de API para autenticação.
            method (str): O método HTTP a ser utilizado (GET, POST, etc.).
            body (Optional[Dict[str, Any]]): O corpo da requisição para
                                             métodos como POST.
            headers (Optional[Dict[str, str]]): Cabeçalhos HTTP adicionais.
            params_url (Optional[Dict[str, Any]]): Parâmetros para serem
                                                   adicionados à URL.

        Returns:
            requests.Response: O objeto de resposta da requisição HTTP.

        Raises:
            ValueError: Se um método HTTP não suportado for fornecido.
        """
        method = method.upper()
        url = self._mount_url(path, params_url or {})

        if headers is None:
            headers = {}

        headers.setdefault("Content-Type", "application/json")
        headers["apikey"] = api_key

        # Tipar explicitamente os métodos para evitar Any
        request_methods: dict[str, Callable[..., requests.Response]] = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        request_method = request_methods.get(method)

        if request_method is None:
            raise ValueError(f"Método HTTP não suportado: {method}")
        return request_method(url, headers=headers, json=body)

    def _mount_url(self, path: str, params_url: Dict[str, Any]) -> str:
        """Monta a URL completa com base, caminho e parâmetros.

        Args:
            path (str): O caminho do endpoint da API.
            params_url (Dict[str, Any]): Um dicionário de parâmetros a serem
                                         codificados na URL.

        Returns:
            str: A URL final, pronta para a requisição.
        """
        parameters = ""
        if isinstance(params_url, dict):
            parameters = urlencode(params_url)

        url = urljoin(self._base_url, path)
        if parameters:
            url = url + "?" + parameters

        return url

    def send_message(
        self,
        instance: str,
        api_key: str,
        number: str,
        text: str,
    ) -> None:
        """Envia uma mensagem de texto via WhatsApp.

        Simula o status 'digitando' antes de enviar a mensagem para uma
        experiência de usuário mais natural.

        Args:
            instance (str): O nome da instância na API Evolution.
            api_key (str): A chave de API para autenticação.
            number (str): O número de telefone do destinatário.
            text (str): O conteúdo da mensagem de texto.

        Raises:
            Exception: Se ocorrer um erro durante o envio da mensagem,
                       seja ao definir o status 'digitando' ou ao enviar
                       a mensagem em si.
        """
        self._typing(typing=True, instance=instance, number=number, api_key=api_key)
        # Ajuste do endpoint conforme esperado nos testes
        path = f"/message/sendText/{instance}"
        body = {
            "number": number,
            "text": text,
        }
        response = self._send_request(path, method="POST", body=body, api_key=api_key)
        self._typing(typing=False, instance=instance, number=number, api_key=api_key)

        if not response.ok:
            raise Exception(
                f"Erro ao enviar mensagem: {response.status_code} - {response.text}"
            )

    def _typing(
        self,
        typing: bool,
        instance: str,
        number: str,
        api_key: str,
    ) -> None:
        """Define o status 'digitando' no WhatsApp.

        Args:
            typing (bool): Se True, define o status como 'digitando'.
                           Se False, define como 'pausado'.
            instance (str): O nome da instância na API Evolution.
            number (str): O número de telefone do chat.
            api_key (str): A chave de API para autenticação.

        Raises:
            Exception: Se a API retornar um erro ao tentar definir o status.
        """
        # Ajuste do endpoint conforme esperado nos testes
        path = f"/chat/sendPresence/{instance}"

        # Formato conforme alguns exemplos da Evolution API: campos no nível raiz
        body = {
            "number": number,
            "presence": "composing" if typing else "paused",
            "delay": 1200,
        }

        response = self._send_request(path, method="POST", body=body, api_key=api_key)

        if not response.ok:
            raise Exception(
                "Erro ao definir status de digitação: "
                f"{response.status_code} - {response.text}"
            )
