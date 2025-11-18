from typing import Any, Dict

from smart_core_assistant_painel.app.evolution_sync.normalizers import (
    normalize_evolution_webhook,
    normalize_evolution_webhook_batch,
)


def _base_payload() -> Dict[str, Any]:
    return {
        "instance": "test-instance",
        "apikey": "test-api-key",
        "sender": "sender@test",
    }


def test_normalize_evolution_webhook_single_dict() -> None:
    payload: Dict[str, Any] = _base_payload()
    payload["data"] = {
        "key": {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "id": "MSG-123",
        },
        "message": {
            "conversation": "hello",
        },
        "messageType": "conversation",
        "pushName": "John",
        "instanceId": "INST-1",
        "source": "EVO",
    }

    env: Dict[str, Any] = normalize_evolution_webhook(payload)

    assert env["source"] == "EvolutionAPI"
    assert env["instance"] == "test-instance"
    assert env["instance_id"] == "INST-1"
    assert env["apikey"] == "test-api-key"
    assert env["contact"]["phone"] == "5511999999999"
    assert env["message"]["type"] == "conversation"
    assert env["message"]["text"] == "hello"
    assert env["profile"]["push_name"] == "John"


def test_normalize_evolution_webhook_batch_with_list() -> None:
    payload: Dict[str, Any] = _base_payload()
    payload["data"] = [
        {
            "key": {
                "remoteJid": "5511000000000@s.whatsapp.net",
                "id": "MSG-1",
            },
            "message": {
                "conversation": "first",
            },
            "messageType": "conversation",
            "pushName": "A",
            "instanceId": "INST-LIST",
            "source": "EVO",
        },
        {
            "key": {
                "remoteJid": "5511222222222@s.whatsapp.net",
                "id": "MSG-2",
            },
            "message": {
                "conversation": "second",
            },
            "messageType": "conversation",
            "pushName": "B",
            "instanceId": "INST-LIST",
            "source": "EVO",
        },
    ]

    envs = normalize_evolution_webhook_batch(payload)

    assert isinstance(envs, list)
    assert len(envs) == 2
    assert envs[0]["contact"]["phone"] == "5511000000000"
    assert envs[0]["message"]["text"] == "first"
    assert envs[1]["contact"]["phone"] == "5511222222222"
    assert envs[1]["message"]["text"] == "second"