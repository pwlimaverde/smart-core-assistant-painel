"""[EVO-GO-001] Adapter para o Evolution Go.

Implementação que consome os endpoints REST do Evolution Go
(container ``evoapicloud/evolution-go``). É o único backend suportado.

Diferenças-chave em relação ao v2:
- Endpoint de envio: ``/send/text`` (não ``/message/sendText/{instance}``)
- Instância identificada via header ``apikey: <token-instância>``
- Webhook configurado no body do ``POST /instance/connect`` (não endpoint separado)
- ``GET /instance/status`` (não ``/instance/connectionState/{name}``)
- Listar instâncias: ``GET /instance/all``
- Eventos em UPPERCASE (``MESSAGE``, ``MESSAGE_UPDATE``, etc.)
- Suporte nativo a mark-read, reactions, presence (recording), download de mídia
"""

from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode, urljoin

import requests  # noqa: I001

# Eventos suportados pelo Evolution Go (whatsmeow). Enviados no campo ``events``
# do POST /instance/connect. ⚠️ NÃO usar o campo ``subscribe`` — o servidor o
# ignora e ZERA a assinatura (events=""), parando toda a entrega de webhooks.
_DEFAULT_SUBSCRIBE_EVENTS: list[str] = [
    "MESSAGE",
    "CONNECTION",
    "PRESENCE",
    "QRCODE",
]


class EvolutionGoAdapter:
    """[EVO-GO-002] Adapter para Evolution Go.

    Instanciado diretamente: ``EvolutionGoAdapter()``.

    Notas de autenticação:
    - **Global API Key**: usada para listar/criar/deletar instâncias
      (header ``apikey: <global-key>``).
    - **Token de instância**: usada para enviar mensagens e operações
      específicas da instância (header ``apikey: <instance-token>``).
      O token é o campo ``api_key`` de ``EvolutionInstance``.
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
        """Envia uma requisição HTTP para o servidor Evolution Go."""
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
        """Monta a URL completa."""
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
        """Envia mensagem de texto via Evolution Go (``POST /send/text``).

        Args:
            instance: Nome da instância (usado apenas para logging).
            api_key: Token da instância (header ``apikey``).
            base_url: URL base do servidor.
            number: Número de destino (ex: ``5511999999999``).
            text: Conteúdo textual da mensagem.
            quoted: Dados da mensagem citada, ex:
                ``{"key": {"id": "MSGID", "remoteJid": "...", "fromMe": False}}``.

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: dict[str, Any] = {"number": number, "text": text}
        if quoted:
            body["quoted"] = quoted

        response = self._send_request(
            base_url, "/send/text", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao enviar mensagem (Go): {response.status_code} - {response.text}"
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
        """Envia mensagem de mídia via Evolution Go (``POST /send/media``).

        Args:
            instance: Nome da instância (para logging).
            api_key: Token da instância.
            base_url: URL base do servidor.
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
        # Spec Evolution GO (MediaStruct): campos ``type``, ``url``, ``caption``,
        # ``filename`` (não ``mediatype``/``media``/``fileName``).
        body: dict[str, Any] = {
            "number": number,
            "type": kind,
            "url": file_url,
            "caption": caption,
            "filename": filename,
        }
        response = self._send_request(
            base_url, "/send/media", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao enviar mídia (Go): {response.status_code} - {response.text}"
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
        """Envia áudio (PTT / nota de voz) via Evolution Go (``POST /send/media``).

        Args:
            instance: Nome da instância.
            api_key: Token da instância.
            base_url: URL base do servidor.
            number: Número de destino.
            audio_url: URL pública do arquivo de áudio.
            ptt: Se True, envia como nota de voz (Push To Talk).

        Returns:
            dict com a resposta da API.
        """
        body: dict[str, Any] = {
            "number": number,
            "type": "audio",
            "url": audio_url,
        }
        response = self._send_request(
            base_url, "/send/media", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao enviar áudio (Go): {response.status_code} - {response.text}"
            )
        return response.json()

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
        """Reage a uma mensagem via Evolution Go (``POST /message/react``).

        Args:
            instance: Nome da instância.
            api_key: Token da instância.
            base_url: URL base do servidor.
            number: JID/número do chat (remoteJid).
            message_id: ID da mensagem a reagir.
            emoji: Emoji de reação (ex: ``"👍"``). String vazia remove a reação.
            from_me: Se a mensagem original foi enviada pela instância.

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: dict[str, Any] = {
            "number": number,
            "reaction": emoji,
            "id": message_id,
            "fromMe": from_me,
        }
        response = self._send_request(
            base_url, "/message/react", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao reagir à mensagem (Go): {response.status_code} - {response.text}"
            )
        return response.json()

    def mark_read(
        self,
        *,
        instance: str,
        api_key: str,
        base_url: str,
        number: str,
        message_ids: list[str],
    ) -> dict:
        """Marca mensagens como lidas via Evolution Go (``POST /message/markread``).

        Args:
            instance: Nome da instância.
            api_key: Token da instância.
            base_url: URL base do servidor.
            number: JID/número do chat.
            message_ids: Lista de IDs de mensagens a marcar como lidas.

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: dict[str, Any] = {"number": number, "id": message_ids}
        response = self._send_request(
            base_url, "/message/markread", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao marcar como lido (Go): {response.status_code} - {response.text}"
            )
        return response.json()

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
        """Define presença via Evolution Go (``POST /message/presence``).

        Args:
            instance: Nome da instância.
            api_key: Token da instância.
            base_url: URL base do servidor.
            number: JID/número do chat.
            state: Estado de presença:
                - ``"composing"`` → digitando texto
                - ``"paused"``    → parou de digitar
                - ``"recording"`` → gravando áudio
            is_audio: Se True, envia ``isAudio: true`` — o contato vê
                      "gravando áudio…" em vez de "digitando…".

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: dict[str, Any] = {
            "number": number,
            "state": state,
            "isAudio": is_audio,
        }
        response = self._send_request(
            base_url, "/message/presence", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao definir presença (Go): {response.status_code} - {response.text}"
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
        """Obtém URL da foto de perfil via Evolution Go (``POST /user/avatar``).

        Args:
            instance: Nome da instância.
            api_key: Token da instância.
            base_url: URL base do servidor.
            number: Número do contato.

        Returns:
            URL da foto de perfil (string vazia se não disponível).
        """
        body: dict[str, Any] = {"number": number, "preview": False}
        try:
            response = self._send_request(
                base_url, "/user/avatar", api_key=api_key, method="POST", body=body
            )
            if response.ok:
                data = response.json()
                return str(data.get("profilePictureUrl", "") or data.get("url", ""))
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
        """Lista todas as instâncias via Evolution Go (``GET /instance/all``).

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.

        Returns:
            Lista de dicts com dados das instâncias.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url, "/instance/all", api_key=api_key
        )
        if not response.ok:
            raise Exception(
                f"Erro ao listar instâncias (Go): {response.status_code} - {response.text}"
            )
        result = response.json()
        # Evolution Go retorna {"data": [...], "message": "success"}
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        if isinstance(result, list):
            return result
        return []

    def create_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
        token: "str | None" = None,
    ) -> dict:
        """Cria instância via Evolution Go (``POST /instance/create``).

        Body simplificado: apenas ``name`` (e opcionalmente ``token``).
        O webhook é configurado no ``connect_instance`` subsequente.

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome da instância.
            token: Token fixo da instância (opcional — Go gera um se omitido).

        Returns:
            dict com dados da instância criada (incluindo ``token``).

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: dict[str, Any] = {"name": name}
        if token:
            body["token"] = token

        response = self._send_request(
            base_url, "/instance/create", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao criar instância (Go): {response.status_code} - {response.text}"
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
        """Conecta instância e configura webhook+eventos via Evolution Go.

        ``POST /instance/connect`` com body contendo ``instanceName``,
        ``webhookUrl`` e lista de ``subscribe``. Não existe endpoint
        ``/webhook/set`` no Evolution Go.

        Args:
            base_url: URL base do servidor.
            api_key: Token da instância (não a Global API Key — esta retorna
                401 "not authorized" no ``/instance/connect`` do Go).
            name: Nome da instância.
            webhook_url: URL do webhook do painel Django.
            subscribe: Lista de eventos a assinar (ex: ``["MESSAGE", "PRESENCE"]``).
                       Usa ``_DEFAULT_SUBSCRIBE_EVENTS`` se a lista vier vazia.

        Returns:
            dict com dados da conexão (pode incluir QR, status, etc.).

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        events = subscribe if subscribe else _DEFAULT_SUBSCRIBE_EVENTS
        # Campo correto por spec (Evolution GO): ``subscribe`` (array de nomes
        # UPPERCASE: MESSAGE, CONNECTION, PRESENCE, QRCODE). Nomes inválidos
        # zeram a assinatura. ``immediate`` conecta a sessão de imediato.
        body: dict[str, Any] = {
            "instanceName": name,
            "webhookUrl": webhook_url,
            "subscribe": events,
            "immediate": True,
        }
        response = self._send_request(
            base_url, "/instance/connect", api_key=api_key, method="POST", body=body
        )
        if not response.ok:
            raise Exception(
                f"Erro ao conectar instância (Go): {response.status_code} - {response.text}"
            )
        return response.json()

    def set_advanced_settings(
        self,
        *,
        base_url: str,
        api_key: str,
        instance_id: str,
        always_online: bool = True,
        read_messages: bool = True,
        reject_call: bool = False,
        msg_reject_call: str = "",
        ignore_groups: bool = False,
        ignore_status: bool = False,
    ) -> dict:
        """Configura advanced-settings da instância (``PUT /instance/{id}/advanced-settings``).

        ``always_online=True`` é o mecanismo **documentado** para manter a sessão
        whatsmeow conectada (evita o ``connected=false`` por ociosidade), em vez
        de depender só de reconnect periódico. ``read_messages=True`` envia os
        recibos de leitura (ticks azuis).

        Usa o **token da instância** como ``apikey`` (a Global Key dá 401 aqui).

        Args:
            base_url: URL base do servidor.
            api_key: Token da instância.
            instance_id: ID (UUID) da instância no servidor Go.
            always_online: Mantém a presença/sessão sempre online.
            read_messages: Marca mensagens recebidas como lidas.
            reject_call: Rejeita chamadas automaticamente.
            msg_reject_call: Mensagem enviada ao rejeitar chamada.
            ignore_groups: Ignora mensagens de grupos.
            ignore_status: Ignora atualizações de status.

        Returns:
            dict com a resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: dict[str, Any] = {
            "alwaysOnline": always_online,
            "readMessages": read_messages,
            "rejectCall": reject_call,
            "msgRejectCall": msg_reject_call,
            "ignoreGroups": ignore_groups,
            "ignoreStatus": ignore_status,
        }
        response = self._send_request(
            base_url,
            f"/instance/{instance_id}/advanced-settings",
            api_key=api_key,
            method="PUT",
            body=body,
        )
        if not response.ok:
            raise Exception(
                f"Erro ao configurar advanced-settings (Go): "
                f"{response.status_code} - {response.text}"
            )
        return response.json()

    def get_qr_code(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> dict:
        """Obtém QR Code via Evolution Go (``GET /instance/qr``).

        Usa o token da instância como ``apikey`` (não a Global API Key).

        Args:
            base_url: URL base do servidor.
            api_key: Token da instância (não a Global API Key).
            name: Nome da instância (para logging).

        Returns:
            dict com dados do QR Code (base64 e/ou pairing code).

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url, "/instance/qr", api_key=api_key
        )
        if not response.ok:
            raise Exception(
                f"Erro ao obter QR (Go): {response.status_code} - {response.text}"
            )
        return response.json()

    def get_status(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> dict:
        """Retorna estado de conexão via Evolution Go (``GET /instance/status``).

        Usa o token da instância como ``apikey``.

        ⚠️ Não usar ``/instance/connectionState/{name}`` — esse endpoint
        é v2 e retorna 503 no servidor Go.

        Args:
            base_url: URL base do servidor.
            api_key: Token da instância.
            name: Nome da instância (para logging).

        Returns:
            dict com estado da instância (ex: ``{"state": "open"}``).

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url, "/instance/status", api_key=api_key
        )
        if not response.ok:
            raise Exception(
                f"Erro ao verificar estado (Go): {response.status_code} - {response.text}"
            )
        return response.json()

    def delete_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> None:
        """Remove instância via Evolution Go (``DELETE /instance/delete/:instanceId``).

        Requer Global API Key.

        Args:
            base_url: URL base do servidor.
            api_key: Global API Key.
            name: Nome/ID da instância.

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
                f"Erro ao deletar instância (Go): {response.status_code} - {response.text}"
            )

    def logout_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> None:
        """Desconecta sessão WhatsApp via Evolution Go (``DELETE /instance/logout``).

        Usa o token da instância como ``apikey``.

        Args:
            base_url: URL base do servidor.
            api_key: Token da instância.
            name: Nome da instância (para logging).

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url,
            "/instance/logout",
            api_key=api_key,
            method="DELETE",
        )
        if not response.ok:
            raise Exception(
                f"Erro ao desconectar instância (Go): {response.status_code} - {response.text}"
            )

    # ------------------------------------------------------------------
    # Mídia Go
    # ------------------------------------------------------------------

    def download_media(
        self,
        *,
        base_url: str,
        api_key: str,
        message: dict,
    ) -> dict:
        """Faz download/descriptografia de mídia via Evolution Go.

        ``POST /message/downloadimage`` com ``{"message": <objeto Message do
        whatsmeow>}``. Usado como fallback quando o webhook **não** traz o
        ``base64`` inline (ex.: imagens grandes). O ``message`` deve conter o
        sub-objeto de mídia com as chaves de descriptografia do whatsmeow
        (``URL``, ``directPath``, ``mediaKey``, ``fileEncSHA256``,
        ``fileSHA256``, ``mediaKeyTimestamp``, ``mimetype``), ex.::

            {"imageMessage": {"URL": "...", "directPath": "...",
                              "mediaKey": "...", "fileEncSHA256": "...", ...}}

        Args:
            base_url: URL base do servidor.
            api_key: Token da instância.
            message: Objeto ``Message`` (whatsmeow) com o sub-objeto de mídia.

        Returns:
            dict com ``base64`` (e/ou ``mimetype``) da mídia descriptografada.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        body: dict[str, Any] = {"message": message}
        response = self._send_request(
            base_url,
            "/message/downloadimage",
            api_key=api_key,
            method="POST",
            body=body,
        )
        if not response.ok:
            raise Exception(
                f"Erro ao baixar mídia (Go): {response.status_code} - {response.text}"
            )
        return response.json()

    # ------------------------------------------------------------------
    # Utilitários adicionais Go
    # ------------------------------------------------------------------

    def reconnect_instance(
        self,
        *,
        base_url: str,
        api_key: str,
        name: str,
    ) -> dict:
        """Reconecta instância via Evolution Go (``POST /instance/reconnect``).

        Args:
            base_url: URL base do servidor.
            api_key: Token da instância.
            name: Nome da instância (para logging).

        Returns:
            dict com resposta da API.

        Raises:
            Exception: Se a API retornar erro HTTP.
        """
        response = self._send_request(
            base_url, "/instance/reconnect", api_key=api_key, method="POST"
        )
        if not response.ok:
            raise Exception(
                f"Erro ao reconectar instância (Go): {response.status_code} - {response.text}"
            )
        return response.json()
