from typing import Any, Dict, Optional
from urllib.parse import urlencode, urljoin

import requests


class BaseEvolutionAPI:
    def __init__(self) -> None:
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
        request = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }.get(method)

        return request(url, headers=headers, json=body)  # type: ignore

    def _mount_url(self, path: str, params_url: Dict[str, Any]) -> str:
        parameters = ""
        if isinstance(params_url, dict):
            parameters = urlencode(params_url)

        url = urljoin(self._BASE_URL, path)
        if parameters:
            url = url + "?" + parameters

        return url

    def _get_instance(self, path: str) -> str:
        return path.strip("/").split("/")[-1]


class SendMessage(BaseEvolutionAPI):
    def send_message(self, instance: str, body: Dict[str, Any]) -> requests.Response:
        path = f"/message/sendText/{instance}/"
        return self._send_request(path, method="POST", body=body)
