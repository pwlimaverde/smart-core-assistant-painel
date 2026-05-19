"""[EVO-V2-001] Adapter para a Evolution API v2 (Baileys).

Implementação concreta que mantém compatibilidade com servidores Evolution v2.
Coexiste com o `EvolutionGoAdapter` durante a janela de cutover; seleccionado
automaticamente quando ``EvolutionInstance.api_version == "v2"``.
"""

from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode, urljoin

import requests


class EvolutionV2Adapter:
    """[EVO-V2-002] Adapter para Evolution API v2 (Baileys).

    Mantém a implementação original de `EvolutionWhatsAppService` adaptada
    à interface `EvolutionAPIInterface`.  Todos os callers devem obter esta
    instância via `get_evolution_adapter("v2")`.
    """

    # ------------------------------------------------------------------
    # Utilitários HTTP internos
    # ------------------------------------------------------------------

    def _send_request(
        self,
        base_url: str,
        path: str,
        api_key: str,
        method: str = "GET",
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params_url: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """Envia uma requisição HTTP para a API do Evolution v2."""
        method = method.upper()
        url = self._mount_url(base_url, path, params_url or {})

        if headers is None:
            headers = {}

        headers.setdefault("Content-Type", "application/json")
        headers["apikey"] = api_key

        request_methods: dict[str, Callable[..., requests.Response]] = {
            "GET": requests.get,
            "POST": requests.post,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        request_method = request_methods.get(method)

        if request_method is None:
            raise ValueError(f"Método HTTP não suportado: {method}")

        response = request_method(url, headers=headers, json=body)
        return response

    def _mount_url(
        self, base_url: str, path: str, params_url: Dict[str, Any]
    ) -> str:
        """Monta a URL completa com base, caminho e parâmetros."""
        parameters = ""
        if isinstance(params_url, dict):
            parameters = urlencode(params_url)

        url = urljoin(base_url, path)
        if parameters:
            url = url + "?" + parameters
        return url

    # ------------------------------------------------------------------
    # Mensageria
    # ------------------------------------------------------------------

    def send_text(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
        text: str,
        quoted: "dict | None" = None,
    ) -> dict:
        """Envia mensagem de texto via Evolution v2.

        Simula presença 'digitando' antes do envio.

        Args:
            instance: Nome da instância na Evolution API.
            api_key: Chave de API da instância.
            base_url: URL base do servidor Evolution.
            number: Número de destino.
            text: Conteúdo da mensagem.
            quoted: Dados da mensagem citada (não suportado em v2 nativo,
                    ignorado silenciosamente).

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        self._typing(
            typing=True,
            instance=instance,
            number=number,
            api_key=api_key,
            base_url=base_url,
        )

        path = f"/message/sendText/{instance}"
        body: dict[str, Any] = {"number": number, "text": text}

        response = self._send_request(
            base_url, path, api_key=api_key, method="POST", body=body
        )

        self._typing(
            typing=False,
            instance=instance,
            number=number,
            api_key=api_key,
            base_url=base_url,
        )

        if not response.ok:
            raise Exception(
                f"Erro ao enviar mensagem: {response.status_code} - {response.text}"
            )
        return response.json()

    def send_media(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
        file_url: str,
        kind: str,
        caption: str = "",
        filename: str = "",
    ) -> dict:
        """Envia mensagem de mídia via Evolution v2.

        Args:
            instance: Nome da instância.
            api_key: Chave de API.
            base_url: URL base.
            number: Número de destino.
            file_url: URL pública do arquivo.
            kind: Tipo de mídia (``image``, ``video``, ``audio``, ``document``).
            caption: Legenda opcional.
            filename: Nome do arquivo (para documentos).

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        path = f"/message/sendMedia/{instance}"
        body: dict[str, Any] = {
            "number": number,
            "mediatype": kind,
            "media": file_url,
            "caption": caption,
            "fileName": filename,
        }
        response = self._send_request(
            base_url, path, api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao enviar mídia: {response.status_code} - {response.text}"
            )
        return response.json()

    def send_audio(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
        audio_url: str,
        ptt: bool = True,
    ) -> dict:
        """Envia áudio (PTT) via v2 usando sendMedia com kind=audio.

        Args:
            instance: Nome da instância.
            api_key: Chave de API.
            base_url: URL base.
            number: Número de destino.
            audio_url: URL do arquivo de áudio.
            ptt: Se True, envia como nota de voz (PTT).

        Returns:
            dict com a resposta da API.
        """
        return self.send_media(
            instance=instance,
            api_key=api_key,
            base_url=base_url,
            number=number,
            file_url=audio_url,
            kind="audio",
        )

    def send_reaction(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
        message_id: str,
        emoji: str,
        from_me: bool = False,
    ) -> dict:
        """Reações não suportadas nativamente em v2. Retorna dict vazio."""
        return {}

    def mark_read(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
        message_ids: list[str],
    ) -> dict:
        """Mark-read não suportado nativamente em v2. Retorna dict vazio."""
        return {}

    def set_presence(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
        state: str,
        is_audio: bool = False,
    ) -> dict:
        """Define presença via v2 (`/chat/sendPresence/{instance}`).

        Args:
            instance: Nome da instância.
            api_key: Chave de API.
            base_url: URL base.
            number: Número do chat.
            state: Estado (``composing``, ``paused``, ``recording``).
            is_audio: Ignorado em v2.

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        path = f"/chat/sendPresence/{instance}"
        body: dict[str, Any] = {
            "number": number,
            "presence": state,
            "delay": 1200,
        }
        response = self._send_request(
            base_url, path, api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao definir presença: {response.status_code} - {response.text}"
            )
        return response.json()

    def get_profile_picture(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
    ) -> str:
        """Obtém URL da foto de perfil via v2 (`/chat/fetchProfilePictureUrl`).

        Args:
            instance: Nome da instância.
            api_key: Chave de API.
            base_url: URL base.
            number: Número do contato.

        Returns:
            URL da foto de perfil (string vazia se não disponível).
        """
        path = f"/chat/fetchProfilePictureUrl/{instance}"
        body: dict[str, Any] = {"number": number}
        try:
            response = self._send_request(
                base_url, path, api_key=api_key, method="POST", body=body
            )
            if response.ok:
                return str(response.json().get("profilePictureUrl", ""))
        except Exception:
            pass
        return ""

    # ------------------------------------------------------------------
    # Gestão de instâncias
    # ------------------------------------------------------------------

    def fetch_instances(
        self,
        base_url: str,
        api_key: str,
    ) -> List[Dict[str, Any]]:
        """Lista instâncias via v2 (`GET /instance/fetchInstances`).

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.

        Returns:
            Lista de dicts com dados das instâncias.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url, "/instance/fetchInstances", api_key=api_key
        )
        if not response.ok:
            raise Exception(
                f"Erro ao listar instâncias: {response.status_code} - {response.text}"
            )
        return response.json()

    def create_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
        token: "str | None" = None,
    ) -> dict:
        """Cria instância via v2 com webhook configurado no body.

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome da instância.
            token: Ignorado em v2 (sem suporte a token fixo no create).

        Returns:
            dict com dados da instância criada.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: Dict[str, Any] = {
            "instanceName": name,
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True,
        }
        response = self._send_request(
            base_url, "/instance/create", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao criar instância: {response.status_code} - {response.text}"
            )
        return response.json()

    def connect_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
        webhook_url: str,
        subscribe: list[str],
    ) -> dict:
        """Conecta instância e configura webhook via v2.

        Em v2 o connect gera o QR e o webhook é configurado via endpoint
        separado (`/webhook/set/{name}`).

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome da instância.
            webhook_url: URL do webhook do painel.
            subscribe: Lista de eventos (compatibilidade com interface — em v2
                       o webhook é configurado separadamente).

        Returns:
            dict com pairingCode, code (QR base64) e count.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        # 1) configura webhook
        self.set_webhook(
            base_url=base_url,
            api_key=api_key,
            instance_name=name,
            webhook_url=webhook_url,
        )
        # 2) gera QR
        response = self._send_request(
            base_url, f"/instance/connect/{name}", api_key=api_key
        )
        if not response.ok:
            raise Exception(
                f"Erro ao conectar instância: {response.status_code} - {response.text}"
            )
        return response.json()

    def get_qr_code(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> dict:
        """Obtém QR Code via v2 (retornado pelo /instance/connect).

        Em v2 o QR já vem no connect; este método chama connect novamente
        como fallback.

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome da instância.

        Returns:
            dict com dados do QR.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url, f"/instance/connect/{name}", api_key=api_key
        )
        if not response.ok:
            raise Exception(
                f"Erro ao obter QR: {response.status_code} - {response.text}"
            )
        return response.json()

    def get_status(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> dict:
        """Verifica estado de conexão via v2 (`/instance/connectionState/{name}`).

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome da instância.

        Returns:
            dict com instance: {instanceName, state}.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url, f"/instance/connectionState/{name}", api_key=api_key
        )
        if not response.ok:
            raise Exception(
                f"Erro ao verificar estado: {response.status_code} - {response.text}"
            )
        return response.json()

    def delete_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> None:
        """Remove instância via v2 (`DELETE /instance/delete/{name}`).

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome da instância.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url,
            f"/instance/delete/{name}",
            api_key=api_key,
            method="DELETE",
        )
        if not response.ok:
            raise Exception(
                f"Erro ao deletar instância: {response.status_code} - {response.text}"
            )

    def logout_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> None:
        """Logout da instância via v2 (`DELETE /instance/logout/{name}`).

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome da instância.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url,
            f"/instance/logout/{name}",
            api_key=api_key,
            method="DELETE",
        )
        if not response.ok:
            raise Exception(
                f"Erro ao desconectar instância: {response.status_code} - {response.text}"
            )

    # ------------------------------------------------------------------
    # Mídia legado v2
    # ------------------------------------------------------------------

    def get_base64_from_media(
        self,
        base_url: str,
        api_key: str,
        instance_name: str,
        message_key: Dict[str, Any],
        message_content: Dict[str, Any],
    ) -> str:
        """Obtém base64 de mídia descriptografada via Evolution v2.

        Endpoint CPU-intensivo — usar apenas como fallback quando o servidor
        não tem S3/MinIO configurado e `download_media` não estiver disponível.

        Args:
            base_url: URL base do servidor.
            api_key: Chave de API da instância.
            instance_name: Nome da instância.
            message_key: Chave da mensagem (remoteJid, fromMe, id).
            message_content: Conteúdo da mensagem (audioMessage, etc.).

        Returns:
            String base64 do conteúdo de mídia descriptografado.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        path = f"/chat/getBase64FromMediaMessage/{instance_name}"
        body: Dict[str, Any] = {
            "message": {
                "key": message_key,
                "message": message_content,
            },
            "convertToMp4": False,
        }
        response = self._send_request(
            base_url, path, api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao obter base64 de mídia: {response.status_code} - {response.text}"
            )
        data: Dict[str, Any] = response.json()
        return str(data.get("base64", ""))

    def download_media(
        self,
        *,
        base_url: str,
        api_key: str,
        instance: str,
        message_id: str,
        number: str,
    ) -> dict:
        """Não suportado em v2. Retorna dict vazio (use get_base64_from_media)."""
        return {}

    # ------------------------------------------------------------------
    # Helpers internos (compatibilidade com chamadores legados)
    # ------------------------------------------------------------------

    def _typing(
        self,
        typing: bool,
        instance: str,
        number: str,
        api_key: str,
        base_url: str,
    ) -> None:
        """Envia estado de digitação via endpoint v2 legacy."""
        state = "composing" if typing else "paused"
        try:
            self.set_presence(
                instance=instance,
                api_key=api_key,
                base_url=base_url,
                number=number,
                state=state,
            )
        except Exception:
            pass  # presença é best-effort

    def set_webhook(
        self,
        base_url: str,
        api_key: str,
        instance_name: str,
        webhook_url: str,
    ) -> Dict[str, Any]:
        """Configura webhook via endpoint v2 separado (`/webhook/set/{name}`).

        Usado internamente por `connect_instance`. Não existe em Evolution Go.

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            instance_name: Nome da instância.
            webhook_url: URL do webhook do painel.

        Returns:
            dict com dados do webhook configurado.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: Dict[str, Any] = {
            "url": webhook_url,
            "enabled": True,
            "webhook_by_events": False,
            "webhook_base64": False,
            "events": [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "PRESENCE_UPDATE",
                "CONNECTION_UPDATE",
                "CONTACTS_UPDATE",
                "QRCODE_UPDATED",
            ],
        }
        response = self._send_request(
            base_url,
            f"/webhook/set/{instance_name}",
            api_key=api_key,
            method="POST",
            body=body,
        )
        if not response.ok:
            raise Exception(
                f"Erro ao configurar webhook: {response.status_code} - {response.text}"
            )
        return response.json()

    # ------------------------------------------------------------------
    # Alias de retrocompatibilidade (era EvolutionWhatsAppService)
    # ------------------------------------------------------------------

    def send_message(
        self,
        instance: str,
        api_key: str,
        number: str,
        text: str,
        base_url: str,
    ) -> None:
        """Alias retrocompat para send_text (signature positional legada).

        Chamadores novos devem usar `send_text` com kwargs.
        """
        self.send_text(
            instance=instance,
            api_key=api_key,
            base_url=base_url,
            number=number,
            text=text,
        )

    def get_connection_state(
        self,
        base_url: str,
        api_key: str,
        instance_name: str,
    ) -> Dict[str, Any]:
        """Alias retrocompat para get_status (signature legada)."""
        return self.get_status(base_url=base_url, api_key=api_key, name=instance_name)


# Alias para compatibilidade com imports existentes
EvolutionWhatsAppService = EvolutionV2Adapter
