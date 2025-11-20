import json
from typing import Any, Dict
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
)



class TestMessageDuplication(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        cache.clear()

    def test_duplicate_webhook_content(self) -> None:
        """
        Testa se o envio duplicado do mesmo webhook resulta em conteúdo duplicado na mensagem.
        """
        payload: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "test-instance-dupe",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "UNIQUE_MESSAGE_ID_123",
                },
                "pushName": "Test User",
                "message": {
                    "conversation": "Mensagem de teste única",
                },
                "messageType": "conversation",
                "messageTimestamp": 1763301593,
                "instanceId": "test-instance-dupe",
                "source": "android",
            },
            "sender": "5511999999999@s.whatsapp.net",
        }

        # Envia o webhook a primeira vez
        resp1 = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp1.status_code, 200)

        # Envia o webhook a segunda vez (simulando retentativa ou duplicidade)
        resp2 = self.client.post(
            reverse("evolution_webhook"),

        # SE O BUG EXISTIR: o conteúdo será "Mensagem de teste única\nMensagem de teste única"
        # SE O BUG FOR CORRIGIDO: o conteúdo será apenas "Mensagem de teste única"
        print(f"\nConteúdo da mensagem: {mensagem.conteudo!r}")

        # A asserção abaixo deve FALHAR se o bug existir (esperamos falha agora)
        self.assertEqual(mensagem.conteudo, "Mensagem de teste única")

    def test_deduplication_cache(self) -> None:
        """
        Testa se o cache de deduplicação está funcionando corretamente.
        """
        payload: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "test-instance-dedup",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "5511888888888@s.whatsapp.net",
                    "fromMe": False,
                    "id": "UNIQUE_ID_CACHE_TEST",
                },
                "pushName": "Cache Test User",
                "message": {
                    "conversation": "Teste de cache",
                },
                "messageType": "conversation",
                "messageTimestamp": 1763301599,
                "instanceId": "test-instance-dedup",
                "source": "android",
            },
            "sender": "5511888888888@s.whatsapp.net",
        }

        # Primeira requisição: deve ser processada (status ok ou accepted)
        resp1 = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertIn(resp1.status_code, [200, 202])
        content1 = resp1.json()
        # Se processou, deve ter status ok ou accepted
        self.assertIn(content1.get("status"), ["ok", "accepted"])

        # Segunda requisição imediata: deve ser ignorada (status ignored_from_me pois a lista valid_envelopes ficará vazia)
        resp2 = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 200)
        content2 = resp2.json()
        self.assertEqual(content2.get("status"), "ignored_from_me")
