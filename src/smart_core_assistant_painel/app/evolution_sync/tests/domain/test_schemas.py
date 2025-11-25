from smart_core_assistant_painel.app.evolution_sync.domain.schemas import (
    EvolutionContactData,
    EvolutionMessageData,
    EvolutionProfileData,
    EvolutionWebhookEnvelope,
)


def test_evolution_message_data_from_dict_conversation() -> None:
    data = {
        "message": {"conversation": "Hello World"},
        "messageType": "conversation",
        "messageTimestamp": 1234567890,
        "instanceId": "inst-1",
        "source": "evo",
    }
    key = {"id": "msg-1"}

    msg = EvolutionMessageData.from_dict(data, key)

    assert msg.id == "msg-1"
    assert msg.type == "conversation"
    assert msg.text == "Hello World"
    assert msg.metadata["messageTimestamp"] == 1234567890
    assert msg.metadata["instanceId"] == "inst-1"
    assert msg.metadata["source"] == "evo"


def test_evolution_message_data_from_dict_extended_text() -> None:
    data = {
        "message": {"extendedTextMessage": {"text": "Extended Hello"}},
        "messageType": "extendedTextMessage",
    }
    key = {"id": "msg-2"}

    msg = EvolutionMessageData.from_dict(data, key)

    assert msg.id == "msg-2"
    assert msg.type == "extendedTextMessage"
    assert msg.text == "Extended Hello"


def test_evolution_message_data_to_dict() -> None:
    msg = EvolutionMessageData(
        id="msg-1",
        type="conversation",
        text="Hello",
        metadata={"timestamp": 123},
    )

    d = msg.to_dict()

    assert d["id"] == "msg-1"
    assert d["type"] == "conversation"
    assert d["text"] == "Hello"
    assert d["metadata"] == {"timestamp": 123}


def test_evolution_contact_data_from_dict() -> None:
    key = {
        "remoteJid": "5511999999999@s.whatsapp.net",
        "addressingMode": "pn",
    }

    contact = EvolutionContactData.from_dict(key)

    assert contact.jid == "5511999999999@s.whatsapp.net"
    assert contact.phone == "5511999999999"
    assert contact.addressing_mode == "pn"
    assert contact.lid is None


def test_evolution_contact_data_from_dict_lid() -> None:
    key = {
        "remoteJid": "123456789@lid",
        "remoteJidAlt": "5511888888888@s.whatsapp.net",
    }

    contact = EvolutionContactData.from_dict(key)

    assert contact.lid == "123456789@lid"
    assert contact.jid == "5511888888888@s.whatsapp.net"
    assert contact.phone == "5511888888888"


def test_evolution_contact_data_to_dict() -> None:
    contact = EvolutionContactData(
        jid="jid-1", lid="lid-1", addressing_mode="pn", phone="123456"
    )

    d = contact.to_dict()

    assert d["jid"] == "jid-1"
    assert d["lid"] == "lid-1"
    assert d["addressing_mode"] == "pn"
    assert d["phone"] == "123456"


def test_evolution_profile_data_from_dict() -> None:
    data = {"pushName": "John Doe"}

    profile = EvolutionProfileData.from_dict(data)

    assert profile.push_name == "John Doe"


def test_evolution_profile_data_to_dict() -> None:
    profile = EvolutionProfileData(push_name="Jane Doe")

    d = profile.to_dict()

    assert d["push_name"] == "Jane Doe"


def test_evolution_webhook_envelope_from_dict() -> None:
    payload = {
        "instance": "inst-name",
        "sender": "sender-jid",
        "apikey": "api-key",
    }
    data = {
        "instanceId": "inst-id",
        "key": {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "id": "msg-id",
            "fromMe": False,
        },
        "message": {"conversation": "text"},
        "pushName": "User",
    }

    envelope = EvolutionWebhookEnvelope.from_dict(payload, data)

    assert envelope.instance == "inst-name"
    assert envelope.instance_id == "inst-id"
    assert envelope.sender_jid == "sender-jid"
    assert envelope.from_me is False
    assert envelope.contact.phone == "5511999999999"
    assert envelope.message.text == "text"
    assert envelope.profile.push_name == "User"
    assert envelope.apikey == "api-key"
    assert envelope.raw == payload


def test_evolution_webhook_envelope_from_dict_single() -> None:
    payload = {
        "instance": "inst-single",
        "data": {
            "key": {"id": "msg-single"},
            "message": {"conversation": "single"},
        },
    }

    envelope = EvolutionWebhookEnvelope.from_dict_single(payload)

    assert envelope.instance == "inst-single"
    assert envelope.message.text == "single"


def test_evolution_webhook_envelope_from_dict_single_with_list_data() -> None:
    # Case where data is a list but we call from_dict_single (should take first)
    payload = {
        "instance": "inst-list-single",
        "data": [
            {
                "key": {"id": "msg-1"},
                "message": {"conversation": "first"},
            },
            {
                "key": {"id": "msg-2"},
                "message": {"conversation": "second"},
            },
        ],
    }

    envelope = EvolutionWebhookEnvelope.from_dict_single(payload)

    assert envelope.instance == "inst-list-single"
    assert envelope.message.text == "first"


def test_evolution_webhook_envelope_from_dict_batch() -> None:
    payload = {
        "instance": "inst-batch",
        "data": [
            {
                "key": {"id": "msg-1"},
                "message": {"conversation": "first"},
            },
            {
                "key": {"id": "msg-2"},
                "message": {"conversation": "second"},
            },
        ],
    }

    envelopes = EvolutionWebhookEnvelope.from_dict_batch(payload)

    assert len(envelopes) == 2
    assert envelopes[0].message.text == "first"
    assert envelopes[1].message.text == "second"


def test_evolution_webhook_envelope_to_dict() -> None:
    envelope = EvolutionWebhookEnvelope(
        instance="inst-1",
        contact=EvolutionContactData(phone="123"),
        message=EvolutionMessageData(text="hello"),
        profile=EvolutionProfileData(push_name="user"),
    )

    d = envelope.to_dict()

    assert d["instance"] == "inst-1"
    assert d["contact"]["phone"] == "123"
    assert d["message"]["text"] == "hello"
    assert d["profile"]["push_name"] == "user"
    assert d["source"] == "EvolutionAPI"


def test_evolution_contact_data_is_group() -> None:
    """Test is_group() method identifies group JIDs correctly."""
    # Caso 1: JID de grupo (@g.us) deve retornar True
    group_contact = EvolutionContactData(jid="120363304634306915@g.us")
    assert group_contact.is_group() is True

    # Caso 2: JID individual (@s.whatsapp.net) deve retornar False
    individual_contact = EvolutionContactData(
        jid="5511999999999@s.whatsapp.net"
    )
    assert individual_contact.is_group() is False

    # Caso 3: LID (@lid) sem JID deve retornar False
    lid_contact = EvolutionContactData(lid="123456789@lid")
    assert lid_contact.is_group() is False

    # Caso 4: JID None/vazio deve retornar False
    empty_contact = EvolutionContactData()
    assert empty_contact.is_group() is False
