from urllib.parse import urlencode, urljoin

import requests


class BaseEvolutionAPI:
    def __init__(self):
        self._BASE_URL = "http://evolution-api:8080"
        self._API_KEY = {"5588921729550": "B6D711FCDE4D4FD5936544120E713976"}

    def _send_request(self, path, method="GET", body=None, headers={}, params_url={}):
        method.upper()
        url = self._mount_url(path, params_url)

        if not isinstance(headers, dict):
            headers = {}

        headers.setdefault("Content-Type", "application/json")

        instance = self._get_instance(path)
        headers["apikey"] = self._API_KEY.get(instance)
        request = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }.get(method)

        return request(url, headers=headers, json=body)

    def _mount_url(self, path, params_url):
        parameters = ""
        if isinstance(params_url, dict):
            parameters = urlencode(params_url)

        url = urljoin(self._BASE_URL, path)
        if parameters:
            url = url + "?" + parameters

        return url

    def _get_instance(self, path):
        return path.strip("/").split("/")[-1]


class SendMessage(BaseEvolutionAPI):
    def send_message(self, instance, body):
        path = f"/message/sendText/{instance}/"
        return self._send_request(path, method="POST", body=body)
