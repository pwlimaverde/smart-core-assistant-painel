from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
        message_keys = list(message.keys())
        message_type: str | None = (
            message_keys[0] if message_keys else data.get("messageType")
        )

        text: str = ""
        if message_type == "conversation":
            val = message.get("conversation")
            text = val if isinstance(val, str) else str(val)
        elif message_type == "extendedTextMessage":
            text = message.get("extendedTextMessage", {}).get("text", "")

        md: Dict[str, Any] = {}
        if "messageTimestamp" in data:
            md["messageTimestamp"] = data["messageTimestamp"]
        if "instanceId" in data:
            md["instanceId"] = data["instanceId"]
        if "source" in data:
            md["source"] = data["source"]

        return cls(
            id=key.get("id"),
            type=message_type,
            text=text,
            metadata=md,
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
    def from_dict(cls, key: Dict[str, Any]) -> "EvolutionContactData":
        """Cria uma instância a partir do payload JSON do webhook.

        Args:
            key: O objeto 'key' do payload que contém dados do contato.

        Returns:
            EvolutionContactData: Instância populada com os dados do contato.
        """
        remote_jid: str | None = key.get("remoteJid")
        remote_jid_alt: str | None = key.get("remoteJidAlt")
        addressing_mode: str | None = key.get("addressingMode")

        jid_val: str | None = None
        lid_val: str | None = None

        # Extrair JID
        if isinstance(remote_jid, str) and remote_jid.endswith(
            "@s.whatsapp.net"
        ):
            jid_val = remote_jid
        elif isinstance(remote_jid_alt, str) and remote_jid_alt.endswith(
            "@s.whatsapp.net"
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

        # Criar os sub-objetos usando seus próprios factory methods
        contact_data = EvolutionContactData.from_dict(key)
        message_data = EvolutionMessageData.from_dict(data, key)
        profile_data = EvolutionProfileData.from_dict(data)

        return cls(
            source="EvolutionAPI",
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
