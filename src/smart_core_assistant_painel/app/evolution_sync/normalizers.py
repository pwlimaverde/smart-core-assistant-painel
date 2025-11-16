from typing import Any, Dict


def normalize_evolution_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    data: Dict[str, Any] = payload.get("data", {})
    key: Dict[str, Any] = data.get("key", {})
    remote_jid: str | None = key.get("remoteJid")
    remote_jid_alt: str | None = key.get("remoteJidAlt")
    addressing_mode: str | None = key.get("addressingMode")
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

    phone: str = ""
    if remote_jid_alt and "@s.whatsapp.net" in remote_jid_alt:
        phone = remote_jid_alt.split("@")[0]
    elif remote_jid and (addressing_mode == "pn" or "@s.whatsapp.net" in remote_jid):
        phone = remote_jid.split("@")[0]

    envelope: Dict[str, Any] = {
        "source": "EvolutionAPI",
        "instance": payload.get("instance"),
        "instance_id": data.get("instanceId"),
        "sender_jid": payload.get("sender"),
        "contact": {
            "jid": remote_jid,
            "lid": remote_jid_alt,
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