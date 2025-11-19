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
from smart_core_assistant_painel.app.ui.atendimentos.utils import (
    send_message_response_by_contact,
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
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 200)

        # Verifica se o contato foi criado
        evo_contact = EvolutionContact.objects.first()
        self.assertIsNotNone(evo_contact)

        # Força o processamento do buffer
        # Precisamos garantir que o buffer tenha as duas mensagens se o bug existir
        # O processamento normalmente é agendado, aqui chamamos direto
        send_message_response_by_contact(int(evo_contact.contact_id))

        # Verifica a mensagem criada
        mensagem = Mensagem.objects.filter(
            atendimento__contato__id=evo_contact.contact_id
        ).first()
        self.assertIsNotNone(mensagem)

        # SE O BUG EXISTIR: o conteúdo será "Mensagem de teste única\nMensagem de teste única"
        # SE O BUG FOR CORRIGIDO: o conteúdo será apenas "Mensagem de teste única"
        print(f"\nConteúdo da mensagem: {mensagem.conteudo!r}")

        # A asserção abaixo deve FALHAR se o bug existir (esperamos falha agora)
        self.assertEqual(mensagem.conteudo, "Mensagem de teste única")
