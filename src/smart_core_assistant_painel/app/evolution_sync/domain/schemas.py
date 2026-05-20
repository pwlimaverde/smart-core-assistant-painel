"""[EVO-SCHEMA-001] Schemas de domínio para o Evolution Sync.

Contém dataclasses e enums para normalização dos payloads de webhook,
suportando tanto Evolution v2 (dot.case lowercase) quanto Evolution Go
(UPPERCASE).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvolutionEventName(str, Enum):
    """[EVO-SCHEMA-002] Nomes canônicos de eventos da Evolution API.

    Suporta Evolution Go (UPPERCASE) e Evolution v2 (dot.case lowercase)
    via ``from_raw()``. Internamente tudo usa o formato Go (UPPERCASE).
    """

    MESSAGE = "MESSAGE"
    MESSAGE_UPDATE = "MESSAGE_UPDATE"
    MESSAGE_DELETE = "MESSAGE_DELETE"
    SEND_MESSAGE = "SEND_MESSAGE"
    PRESENCE = "PRESENCE"
    CONNECTION = "CONNECTION"
    QRCODE = "QRCODE"
    CONTACTS = "CONTACTS"
    GROUP = "GROUP"
    CALL = "CALL"

    @classmethod
    def from_raw(cls, raw: str) -> "EvolutionEventName | None":
        """Converte nome de evento bruto (v2 ou Go) para o enum canônico.

        Aceita ambos os formatos sem configuração adicional:
        - Evolution Go (UPPERCASE): ``"MESSAGE"``, ``"MESSAGE_UPDATE"``
        - Evolution v2 (dot.case): ``"messages.upsert"``, ``"messages.update"``

        Args:
            raw: Nome do evento recebido no payload do webhook.

        Returns:
            ``EvolutionEventName`` correspondente, ou ``None`` se desconhecido.

        Example::

            EvolutionEventName.from_raw("messages.upsert")  # → MESSAGE
            EvolutionEventName.from_raw("MESSAGE_UPDATE")   # → MESSAGE_UPDATE
        """
        # 1. Tenta match direto (Evolution Go — UPPERCASE)
        if raw in cls._value2member_map_:
            return cls(raw)

        # 2. Normaliza e tenta aliases v2 → Go
        # "messages.upsert" → "MESSAGES_UPSERT" → alias → MESSAGE
        normalized = raw.upper().replace(".", "_")
        # Remove plural "S" para alinhar com aliases
        normalized_singular = normalized.rstrip("S")

        # 2a. Match direto após normalizar (Evolution Go emite PascalCase:
        # "Message" → "MESSAGE", "QRCode" → "QRCODE", "Presence" → "PRESENCE").
        # Sem isto, esses eventos caíam em None e eram descartados no filtro
        # global do webhook (mensagens inbound não eram processadas).
        if normalized in cls._value2member_map_:
            return cls(normalized)

        _ALIASES: dict[str, "EvolutionEventName"] = {
            # Evolution Go: evento de conexão estabelecida / encerrada
            "CONNECTED": cls.CONNECTION,
            "DISCONNECTED": cls.CONNECTION,
            "LOGGEDOUT": cls.CONNECTION,
            "LOGGED_OUT": cls.CONNECTION,
            "LOGOUT": cls.CONNECTION,
            # messages.upsert / MESSAGES_UPSERT → MESSAGE
            "MESSAGES_UPSERT": cls.MESSAGE,
            "MESSAGE_UPSERT": cls.MESSAGE,
            # messages.update / MESSAGES_UPDATE → MESSAGE_UPDATE
            "MESSAGES_UPDATE": cls.MESSAGE_UPDATE,
            # messages.delete / MESSAGES_DELETE → MESSAGE_DELETE
            "MESSAGES_DELETE": cls.MESSAGE_DELETE,
            # send.message / SEND_MESSAGE
            "SEND_MESSAGE": cls.SEND_MESSAGE,
            # presence.update / PRESENCE_UPDATE → PRESENCE
            "PRESENCE_UPDATE": cls.PRESENCE,
            # connection.update / CONNECTION_UPDATE → CONNECTION
            "CONNECTION_UPDATE": cls.CONNECTION,
            # qrcode.updated / QRCODE_UPDATED → QRCODE
            "QRCODE_UPDATED": cls.QRCODE,
            # contacts.update / CONTACTS_UPDATE → CONTACTS
            "CONTACTS_UPDATE": cls.CONTACTS,
            # groups.upsert → GROUP
            "GROUPS_UPSERT": cls.GROUP,
            "GROUP_UPSERT": cls.GROUP,
        }

        return (
            _ALIASES.get(normalized)
            or _ALIASES.get(normalized_singular)
        )


@dataclass
class EvolutionMessageData:
    """Dados da mensagem recebida via webhook.

    Attributes:
        id: ID da mensagem.
        type: Tipo da mensagem (ex: conversation, extendedTextMessage).
        text: Conteúdo de texto da mensagem.
        metadata: Metadados adicionais da mensagem (timestamp, instanceId, etc).
    """

    id: Optional[str] = None
    type: Optional[str] = None
    text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], key: Dict[str, Any]
    ) -> "EvolutionMessageData":
        """Cria uma instância a partir do payload JSON do webhook.

        Args:
            data: O objeto 'data' do payload.
            key: O objeto 'key' dentro de 'data'.

        Returns:
            EvolutionMessageData: Instância populada com os dados da mensagem.
        """
        message: Dict[str, Any] = data.get("message", {})
        # Prioritize explicit messageType from payload
        message_type: str | None = data.get("messageType")

        if not message_type and message:
            # Filter out known metadata keys to find the real message type
            ignore_keys = {
                "messageContextInfo",
                "senderKeyDistributionMessage",
            }
            valid_keys = [k for k in message.keys() if k not in ignore_keys]
            if valid_keys:
                message_type = valid_keys[0]
            else:
                # Fallback to first key if everything is ignored or empty
                keys = list(message.keys())
                if keys:
                    message_type = keys[0]

        text: str = ""
        metadata: Dict[str, Any] = {}
        if message_type == "conversation":
            val = message.get("conversation")
            text = val if isinstance(val, str) else str(val)
        elif message_type == "extendedTextMessage":
            text = message.get("extendedTextMessage", {}).get("text", "")
        elif message_type == "audioMessage":
            msg_data = message.get("audioMessage", {})
            # A Evolution pode enviar o base64 em chaves diferentes
            # dependendo da versão/configuração do webhook.
            base64_data = (
                msg_data.get("base64")
                or message.get("base64")
                or data.get("base64")
                or ""
            )
            text = "[audio]"
            metadata = {
                "mimetype": msg_data.get("mimetype"),
                "url": msg_data.get("url"),
                "seconds": msg_data.get("seconds"),
                "ptt": msg_data.get("ptt", False),
                "base64": (
                    base64_data
                    if isinstance(base64_data, str)
                    else str(base64_data)
                ),
                # Campos de encriptação do WhatsApp necessários
                # para descriptografar mídia via Evolution API
                # (getBase64FromMediaMessage).
                "mediaKey": msg_data.get("mediaKey", ""),
                "directPath": msg_data.get("directPath", ""),
                "fileSha256": msg_data.get("fileSha256", ""),
                "fileEncSha256": msg_data.get("fileEncSha256", ""),
                "fileLength": msg_data.get("fileLength"),
                "mediaKeyTimestamp": msg_data.get("mediaKeyTimestamp"),
            }
        elif message_type == "imageMessage":
            msg_data = message.get("imageMessage", {})
            caption = msg_data.get("caption")
            text = (
                caption if isinstance(caption, str) and caption else "[imagem]"
            )
            metadata = {
                "mimetype": msg_data.get("mimetype"),
                "url": msg_data.get("url"),
                "mediaKey": msg_data.get("mediaKey", ""),
                "directPath": msg_data.get("directPath", ""),
                "fileSha256": msg_data.get("fileSha256", ""),
                "fileEncSha256": msg_data.get("fileEncSha256", ""),
                "fileLength": msg_data.get("fileLength"),
                "mediaKeyTimestamp": msg_data.get("mediaKeyTimestamp"),
            }
        elif message_type == "videoMessage":
            msg_data = message.get("videoMessage", {})
            caption = msg_data.get("caption")
            text = (
                caption if isinstance(caption, str) and caption else "[video]"
            )
            metadata = {
                "mimetype": msg_data.get("mimetype"),
                "url": msg_data.get("url"),
                "seconds": msg_data.get("seconds"),
                "mediaKey": msg_data.get("mediaKey", ""),
                "directPath": msg_data.get("directPath", ""),
                "fileSha256": msg_data.get("fileSha256", ""),
                "fileEncSha256": msg_data.get("fileEncSha256", ""),
                "fileLength": msg_data.get("fileLength"),
                "mediaKeyTimestamp": msg_data.get("mediaKeyTimestamp"),
            }
        elif message_type == "documentMessage":
            msg_data = message.get("documentMessage", {})
            file_name = msg_data.get("fileName")
            text = (
                file_name
                if isinstance(file_name, str) and file_name
                else "[documento]"
            )
            metadata = {
                "mimetype": msg_data.get("mimetype"),
                "url": msg_data.get("url"),
                "mediaKey": msg_data.get("mediaKey", ""),
                "directPath": msg_data.get("directPath", ""),
                "fileSha256": msg_data.get("fileSha256", ""),
                "fileEncSha256": msg_data.get("fileEncSha256", ""),
                "fileLength": msg_data.get("fileLength"),
                "mediaKeyTimestamp": msg_data.get("mediaKeyTimestamp"),
            }

        return cls(
            id=key.get("id"),
            type=message_type,
            text=text,
            metadata=metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converte os dados da mensagem para dicionário.

        Returns:
            Dict[str, Any]: Dicionário com os dados da mensagem.
        """
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass
class EvolutionContactData:
    """Dados do contato recebidos via webhook.

    Attributes:
        jid: ID do contato no WhatsApp (ex: 123456789@s.whatsapp.net).
        lid: ID do contato no formato LID.
        addressing_mode: Modo de endereçamento.
        phone: Número de telefone extraído do JID.
    """

    jid: Optional[str] = None
    lid: Optional[str] = None
    addressing_mode: Optional[str] = None
    phone: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionContactData":
        """Cria uma instância a partir do payload JSON do webhook.

        Args:
            data: O objeto 'data' do payload (pode conter 'key' ou ter campos diretos).

        Returns:
            EvolutionContactData: Instância populada com os dados do contato.
        """
        key: Dict[str, Any] = data.get("key", {})

        # Tenta pegar do key primeiro (padrão messages.upsert)
        remote_jid: str | None = key.get("remoteJid")
        remote_jid_alt: str | None = key.get("remoteJidAlt")
        addressing_mode: str | None = key.get("addressingMode")

        # Se não achou no key, tenta direto no data (padrão contacts.update)
        if not remote_jid:
            remote_jid = data.get("remoteJid")
        if not remote_jid_alt:
            remote_jid_alt = data.get("remoteJidAlt")
        if not addressing_mode:
            addressing_mode = data.get("addressingMode")

        jid_val: str | None = None
        lid_val: str | None = None

        # Extrair JID (individual ou grupo)
        if isinstance(remote_jid, str) and (
            remote_jid.endswith("@s.whatsapp.net")
            or remote_jid.endswith("@g.us")
        ):
            jid_val = remote_jid
        elif isinstance(remote_jid_alt, str) and (
            remote_jid_alt.endswith("@s.whatsapp.net")
            or remote_jid_alt.endswith("@g.us")
        ):
            jid_val = remote_jid_alt

        # Extrair LID
        if isinstance(remote_jid, str) and remote_jid.endswith("@lid"):
            lid_val = remote_jid
        elif isinstance(remote_jid_alt, str) and remote_jid_alt.endswith(
            "@lid"
        ):
            lid_val = remote_jid_alt

        # Extrair telefone do JID
        phone: str = ""
        if isinstance(jid_val, str) and jid_val.endswith("@s.whatsapp.net"):
            phone = jid_val.split("@")[0]

        return cls(
            jid=jid_val,
            lid=lid_val,
            addressing_mode=addressing_mode,
            phone=phone,
        )

    def is_group(self) -> bool:
        """Verifica se o contato é um grupo do WhatsApp.

        Returns:
            bool: True se o JID termina com @g.us (grupo), False caso contrário.
        """
        if self.jid:
            return self.jid.endswith("@g.us")
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Converte os dados do contato para dicionário.

        Returns:
            Dict[str, Any]: Dicionário com os dados do contato.
        """
        return {
            "jid": self.jid,
            "lid": self.lid,
            "addressing_mode": self.addressing_mode,
            "phone": self.phone,
        }


@dataclass
class EvolutionProfileData:
    """Dados do perfil do contato.

    Attributes:
        push_name: Nome de exibição do usuário no WhatsApp.
    """

    push_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvolutionProfileData":
        """Cria uma instância a partir do payload JSON do webhook.

        Args:
            data: O objeto 'data' do payload.

        Returns:
            EvolutionProfileData: Instância populada com os dados do perfil.
        """
        return cls(push_name=data.get("pushName"))

    def to_dict(self) -> Dict[str, Any]:
        """Converte os dados do perfil para dicionário.

        Returns:
            Dict[str, Any]: Dicionário com os dados do perfil.
        """
        return {"push_name": self.push_name}


@dataclass
class EvolutionWebhookEnvelope:
    """Envelope normalizado contendo os dados do webhook.

    Attributes:
        source: Fonte dos dados (sempre 'EvolutionAPI').
        event: Tipo de evento (messages.upsert, contacts.update, etc.).
        instance: Nome da instância.
        instance_id: ID da instância.
        sender_jid: JID do remetente.
        from_me: Se a mensagem foi enviada pela própria instância.
        contact: Dados do contato.
        message: Dados da mensagem.
        profile: Dados do perfil.
        apikey: Chave de API da instância.
        raw: Payload original completo.
    """

    source: str = "EvolutionAPI"
    event: Optional[str] = None
    instance: Optional[str] = None
    instance_id: Optional[str] = None
    sender_jid: Optional[str] = None
    from_me: bool = False
    contact: EvolutionContactData = field(default_factory=EvolutionContactData)
    message: EvolutionMessageData = field(default_factory=EvolutionMessageData)
    profile: EvolutionProfileData = field(default_factory=EvolutionProfileData)
    apikey: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls, payload: Dict[str, Any], data: Dict[str, Any]
    ) -> "EvolutionWebhookEnvelope":
        """Cria uma instância a partir do payload JSON bruto do webhook.

        Este método encapsula toda a lógica de normalização e parsing do webhook,
        convertendo o JSON em uma estrutura de dados tipada e validada.

        Args:
            payload: O payload completo do webhook recebido.
            data: O objeto 'data' específico a ser processado (pode ser um item de batch).

        Returns:
            EvolutionWebhookEnvelope: Instância normalizada do envelope.
        """
        key: Dict[str, Any] = data.get("key", {})
        from_me: bool = key.get("fromMe", False)

        # Normaliza nome do evento: aceita v2 (dot.case) e Go (UPPERCASE)
        raw_event: str = payload.get("event", "")
        parsed_event = EvolutionEventName.from_raw(raw_event)
        event_value: str = parsed_event.value if parsed_event else raw_event

        # Criar os sub-objetos usando seus próprios factory methods
        contact_data = EvolutionContactData.from_dict(data)
        message_data = EvolutionMessageData.from_dict(data, key)
        profile_data = EvolutionProfileData.from_dict(data)

        # Evolution Go: messageTimestamp pode vir como string
        # Normalizar para int no metadata se necessário
        msg_timestamp = data.get("messageTimestamp")
        if isinstance(msg_timestamp, str):
            try:
                data = {**data, "messageTimestamp": int(msg_timestamp)}
            except (ValueError, TypeError):
                pass

        # Evolution Go: mediaUrl pode vir em data.message.mediaUrl
        # Injeta no metadata para uso downstream (attendance_orchestrator)
        message_obj: Dict[str, Any] = data.get("message", {})
        media_url: str = message_obj.get("mediaUrl", "")
        if media_url and message_data.metadata is not None:
            message_data.metadata["media_url"] = media_url

        return cls(
            source="EvolutionAPI",
            event=event_value,
            instance=payload.get("instance"),
            instance_id=data.get("instanceId"),
            sender_jid=payload.get("sender"),
            from_me=from_me,
            contact=contact_data,
            message=message_data,
            profile=profile_data,
            apikey=payload.get("apikey"),
            raw=payload,
        )

    @classmethod
    def from_dict_single(
        cls, payload: Dict[str, Any]
    ) -> "EvolutionWebhookEnvelope":
        """Cria uma instância a partir de um payload simples (não-batch).

        Args:
            payload: O payload completo do webhook.

        Returns:
            EvolutionWebhookEnvelope: Instância normalizada do envelope.
        """
        data_obj: Any = payload.get("data", {})
        if isinstance(data_obj, list):
            first: Dict[str, Any] = next(
                (item for item in data_obj if isinstance(item, dict)),
                {},
            )
            return cls.from_dict(payload, first)
        return cls.from_dict(
            payload, data_obj if isinstance(data_obj, dict) else {}
        )

    @classmethod
    def from_dict_batch(
        cls, payload: Dict[str, Any]
    ) -> List["EvolutionWebhookEnvelope"]:
        """Cria uma lista de instâncias a partir de um payload batch.

        Args:
            payload: O payload completo do webhook contendo múltiplos items.

        Returns:
            List[EvolutionWebhookEnvelope]: Lista de envelopes normalizados.
        """
        data_obj: Any = payload.get("data", {})
        if isinstance(data_obj, list):
            envelopes: List[EvolutionWebhookEnvelope] = []
            for item in data_obj:
                if isinstance(item, dict):
                    envelopes.append(cls.from_dict(payload, item))
            return envelopes
        return [cls.from_dict_single(payload)]

    def to_dict(self) -> Dict[str, Any]:
        """Converte o envelope para dicionário (compatibilidade com código legado).

        Returns:
            Dict[str, Any]: Representação em dicionário do envelope.
        """
        return {
            "source": self.source,
            "event": self.event,
            "instance": self.instance,
            "instance_id": self.instance_id,
            "sender_jid": self.sender_jid,
            "from_me": self.from_me,
            "contact": self.contact.to_dict(),
            "message": self.message.to_dict(),
            "profile": self.profile.to_dict(),
            "apikey": self.apikey,
            "raw": self.raw,
        }
