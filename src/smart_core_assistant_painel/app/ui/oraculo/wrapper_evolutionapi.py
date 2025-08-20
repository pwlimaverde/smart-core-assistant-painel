"""Wrapper para a API de evolução.

Este módulo fornece uma classe base e subclasses para interagir com a
Evolution API para enviar mensagens do WhatsApp.
"""

from typing import Any, Dict, Optional
from urllib.parse import urlencode, urljoin

import requests


class BaseEvolutionAPI:
    """Classe base para interagir com a Evolution API."""

    def __init__(self) -> None:
        """Inicializa a classe base da API."""
        self._BASE_URL = "http://evolution-api:8080"
        self._API_KEY = {"5588921729550": "B6D711FCDE4D4FD5936544120E713976"}

    def _send_request(
        self,
        path: str,
        method: str = "GET",
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params_url: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Envia uma requisição para a Evolution API.

        Args:
            path (str): O caminho do endpoint.
            method (str): O método HTTP (GET, POST, etc.).
            body (Optional[Dict[str, Any]]): O corpo da requisição.
            headers (Optional[Dict[str, str]]): Cabeçalhos adicionais.
            params_url (Optional[Dict[str, Any]]): Parâmetros de URL.

        Returns:
            requests.Response: A resposta da requisição.

        Raises:
            ValueError: Se a chave de API não for encontrada para a instância.
        """
        method.upper()
        url = self._mount_url(path, params_url or {})

        if headers is None:
            headers = {}

        headers.setdefault("Content-Type", "application/json")

        instance = self._get_instance(path)
        api_key = self._API_KEY.get(instance)
        if api_key is None:
            raise ValueError(f"API key não encontrada para instância: {instance}")
        headers["apikey"] = api_key
        request_method = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }.get(method)

        if request_method is None:
            raise ValueError(f"Método HTTP não suportado: {method}")

        return request_method(url, headers=headers, json=body)

    def _mount_url(self, path: str, params_url: Dict[str, Any]) -> str:
        """Monta a URL completa para a requisição.

        Args:
            path (str): O caminho do endpoint.
            params_url (Dict[str, Any]): Parâmetros de URL.

        Returns:
            str: A URL completa.
        """
        parameters = ""
        if isinstance(params_url, dict):
            parameters = urlencode(params_url)

        url = urljoin(self._BASE_URL, path)
        if parameters:
            url = url + "?" + parameters

        return url

    def _get_instance(self, path: str) -> str:
        """Extrai a instância do caminho da URL.

        Args:
            path (str): O caminho do endpoint.

        Returns:
            str: O nome da instância.
        """
        return path.strip("/").split("/")[-1]


class SendMessage(BaseEvolutionAPI):
    """Classe para enviar mensagens através da Evolution API."""

    def send_message(self, instance: str, body: Dict[str, Any]) -> requests.Response:
        """Envia uma mensagem de texto.

        Args:
            instance (str): O nome da instância.
            body (Dict[str, Any]): O corpo da mensagem.

        Returns:
            requests.Response: A resposta da requisição.
        """
        path = f"/message/sendText/{instance}/"
        return self._send_request(path, method="POST", body=body)
