from typing import Any, Dict, List


def _normalize_single(
    payload: Dict[str, Any], data: Dict[str, Any]
) -> Dict[str, Any]:
    key: Dict[str, Any] = data.get("key", {})
    remote_jid: str | None = key.get("remoteJid")
    remote_jid_alt: str | None = key.get("remoteJidAlt")
    addressing_mode: str | None = key.get("addressingMode")
    from_me: bool = key.get("fromMe", False)
    message: Dict[str, Any] = data.get("message", {})
    message_keys = list(message.keys())
    message_type: str | None = (
        message_keys[0] if message_keys else data.get("messageType")
    )
    text: str = ""
    md: Dict[str, Any] = {}
    if "messageTimestamp" in data:
        md["messageTimestamp"] = data["messageTimestamp"]
    if "instanceId" in data:
        md["instanceId"] = data["instanceId"]
    if "source" in data:
        md["source"] = data["source"]

    if message_type == "conversation":
        val = message.get("conversation")
        text = val if isinstance(val, str) else str(val)
    elif message_type == "extendedTextMessage":
        text = message.get("extendedTextMessage", {}).get("text", "")
    else:
        text = ""

    jid_val: str | None = None
    lid_val: str | None = None

    if isinstance(remote_jid, str) and remote_jid.endswith("@s.whatsapp.net"):
        jid_val = remote_jid
    elif isinstance(remote_jid_alt, str) and remote_jid_alt.endswith(
        "@s.whatsapp.net"
    ):
        jid_val = remote_jid_alt

    if isinstance(remote_jid, str) and remote_jid.endswith("@lid"):
        lid_val = remote_jid
    elif isinstance(remote_jid_alt, str) and remote_jid_alt.endswith("@lid"):
        lid_val = remote_jid_alt

    phone: str = ""
    if isinstance(jid_val, str) and jid_val.endswith("@s.whatsapp.net"):
        phone = jid_val.split("@")[0]

    envelope: Dict[str, Any] = {
        "source": "EvolutionAPI",
        "instance": payload.get("instance"),
        "instance_id": data.get("instanceId"),
        "sender_jid": payload.get("sender"),
        "from_me": from_me,
        "contact": {
            "jid": jid_val,
            "lid": lid_val,
            "addressing_mode": addressing_mode,
            "phone": phone,
        },
        "message": {
            "id": key.get("id"),
            "type": message_type,
            "text": text,
            "metadata": md,
        },
        "profile": {
            "push_name": data.get("pushName"),
        },
        "apikey": payload.get("apikey"),
        "raw": payload,
    }
    return envelope


def normalize_evolution_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    data_obj: Any = payload.get("data", {})
    if isinstance(data_obj, list):
        first: Dict[str, Any] = next(
            (item for item in data_obj if isinstance(item, dict)),
            {},
        )
        return _normalize_single(payload, first)
    return _normalize_single(
        payload, data_obj if isinstance(data_obj, dict) else {}
    )


def normalize_evolution_webhook_batch(
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    data_obj: Any = payload.get("data", {})
    if isinstance(data_obj, list):
        envelopes: List[Dict[str, Any]] = []
        for item in data_obj:
            if isinstance(item, dict):
                envelopes.append(_normalize_single(payload, item))
        return envelopes
    return [normalize_evolution_webhook(payload)]
