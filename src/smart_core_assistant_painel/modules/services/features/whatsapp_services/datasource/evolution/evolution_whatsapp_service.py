from abc import ABCMeta
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urljoin

import requests
from loguru import logger

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
    """Serviço para interagir com a API do WhatsApp através do EvolutionAPI.

    Implementa o padrão Singleton para garantir uma única instância.
    """

    def __init__(self) -> None:
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
            path: Caminho da API
            method: Método HTTP (GET, POST, PUT, DELETE)
            body: Corpo da requisição
            headers: Cabeçalhos da requisição
            params_url: Parâmetros da URL

        Returns:
            Resposta da requisição HTTP
        """
        method = method.upper()
        url = self._mount_url(path, params_url or {})

        if headers is None:
            headers = {}

        headers.setdefault("Content-Type", "application/json")
        headers["apikey"] = api_key

        request_method = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }.get(method)

        if request_method is None:
            raise ValueError(f"Método HTTP não suportado: {method}")
        logger.error(f"Requisição: {method} - {url} - {headers} - {body}")
        return request_method(url, headers=headers, json=body)

    def _mount_url(self, path: str, params_url: Dict[str, Any]) -> str:
        """Monta a URL completa com parâmetros.

        Args:
            path: Caminho da API
            params_url: Parâmetros da URL

        Returns:
            URL completa montada
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
        """Envia uma mensagem via WhatsApp através da Evolution API."""
        path = f"/{SERVICEHUB.WHATSAPP_API_SEND_TEXT_URL}/{instance}/"
        body = {
            "number": number,
            "text": text,
        }
        response = self._send_request(path, method="POST", body=body, api_key=api_key)

        if not response.ok:
            raise Exception(
                f"Erro ao enviar mensagem: {response.status_code} - {response.text}"
            )

    def typing(
        self,
        typing: bool,
        instance: str,
        number: str,
        api_key: str,
    ) -> None:
        """Define o status de digitação no WhatsApp.

        Args:
            typing: True para mostrar que está digitando, False para parar
        """
        path = f"/{SERVICEHUB.WHATSAPP_API_START_TYPING_URL}/{instance}/"

        # Formato conforme alguns exemplos da Evolution API: campos no nível raiz
        body = {
            "number": number,
            "presence": "composing" if typing else "paused",
            "delay": 30000,
        }

        response = self._send_request(path, method="POST", body=body, api_key=api_key)
        logger.error(
            f"Resposta da requisição: {response.status_code} - {response.text}"
        )

        if not response.ok:
            raise Exception(
                f"Erro ao definir status de digitação: {response.status_code} - {response.text}"
            )
