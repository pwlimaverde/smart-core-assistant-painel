import json
from typing import Any, Dict

from django.test import Client, TestCase
from django.urls import reverse

from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionContact,
    EvolutionInstance,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato


class TestEvolutionWebhookFlow(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()

    def test_end_to_end_contact_attendance_message(self) -> None:
        payload: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "99910a55-8bbd-440a-9e14-9d5833a63c5e",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "558897141275@s.whatsapp.net",
                    "remoteJidAlt": "62921321222334@lid",
                    "fromMe": False,
                    "id": "ACE67E7835EF52C7FF28C63C5616F4A4",
                    "participant": "",
                    "addressingMode": "pn",
                },
                "pushName": "Paulo Weslley Limaverde",
                "status": "DELIVERY_ACK",
                "message": {
                    "conversation": "Teste recebimento de mensagens",
                },
                "messageType": "conversation",
                "messageTimestamp": 1763301593,
                "instanceId": "99910a55-8bbd-440a-9e14-9d5833a63c5e",
                "source": "android",
            },
            "sender": "5588921729550@s.whatsapp.net",
        }

        resp = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        evo_contact: EvolutionContact | None = EvolutionContact.objects.first()
        self.assertIsNotNone(evo_contact)
        assert evo_contact is not None
        self.assertIsNotNone(evo_contact.contact_id)

        send_message_response_by_contact(int(evo_contact.contact_id))

        contato: Contato | None = Contato.objects.filter(
            id=evo_contact.contact_id
        ).first()
        print(f"DEBUG: contato={contato}")
        self.assertIsNotNone(contato)
        assert contato is not None

        atendimento: Atendimento | None = Atendimento.objects.filter(
            contato=contato
        ).first()
        print(f"DEBUG: atendimento={atendimento}")
        self.assertIsNotNone(atendimento)
        assert atendimento is not None

        mensagem: Mensagem | None = Mensagem.objects.filter(
            atendimento=atendimento
        ).first()
        print(f"DEBUG: mensagem={mensagem}")
        self.assertIsNotNone(mensagem)

    def test_phone_saved_when_pn_available(self) -> None:
        payload: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "inst-name",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "remoteJidAlt": "1234567890@lid",
                    "fromMe": False,
                    "id": "MSG1",
                    "participant": "",
                    "addressingMode": "pn",
                },
                "pushName": "Cliente PN",
                "status": "DELIVERY_ACK",
                "message": {"conversation": "Olá"},
                "messageType": "conversation",
                "messageTimestamp": 1763301593,
                "instanceId": "inst-id",
                "source": "android",
            },
            "sender": "5511999999999@s.whatsapp.net",
        }
        resp = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        evo_contact: EvolutionContact | None = EvolutionContact.objects.first()
        assert evo_contact is not None
        contato: Contato | None = Contato.objects.filter(
            id=evo_contact.contact_id
        ).first()
        assert contato is not None
        self.assertEqual(contato.telefone, "5511999999999")

    def test_phone_updated_when_only_lid_then_pn(self) -> None:
        payload_lid_only: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "inst-name",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "1234567890@lid",
                    "fromMe": False,
                    "id": "MSG2",
                    "participant": "",
                    "addressingMode": "lid",
                },
                "pushName": "Cliente LID",
                "status": "DELIVERY_ACK",
                "message": {"conversation": "Oi"},
                "messageType": "conversation",
                "messageTimestamp": 1763301593,
                "instanceId": "inst-id",
                "source": "android",
            },
            "sender": "558800000000@s.whatsapp.net",
        }
        resp1 = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload_lid_only),
            content_type="application/json",
        )
        self.assertEqual(resp1.status_code, 200)
        evo_contact1: EvolutionContact | None = (
            EvolutionContact.objects.first()
        )
        assert evo_contact1 is not None
        contato1: Contato | None = Contato.objects.filter(
            id=evo_contact1.contact_id
        ).first()
        assert contato1 is not None
        self.assertIsNone(contato1.telefone)

        payload_with_pn_alt: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "inst-name",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "1234567890@lid",
                    "remoteJidAlt": "5511888888888@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG3",
                    "participant": "",
                    "addressingMode": "lid",
                },
                "pushName": "Cliente LID/PN",
                "status": "DELIVERY_ACK",
                "message": {"conversation": "Olá novamente"},
                "messageType": "conversation",
                "messageTimestamp": 1763301594,
                "instanceId": "inst-id",
                "source": "android",
            },
            "sender": "558800000000@s.whatsapp.net",
        }
        resp2 = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload_with_pn_alt),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(EvolutionContact.objects.count(), 1)
        evo_contact: EvolutionContact | None = EvolutionContact.objects.first()
        assert evo_contact is not None
        contato: Contato | None = Contato.objects.filter(
            id=evo_contact.contact_id
        ).first()
        assert contato is not None
        self.assertEqual(contato.telefone, "5511888888888")

    def test_signal_dispatches_on_bot_response(self) -> None:
        instance = EvolutionInstance.objects.create(
            name="inst-name",
            instance_id="inst-id",
            api_key="TEST_API_KEY",
        )
        contato = Contato.objects.create(
            nome_contato="Cliente",
            telefone="5511999999999",
            ativo=True,
            metadados={},
        )
        evo_contact = EvolutionContact.objects.create(
            instance=instance,
            contact=contato,
            jid="5511999999999@s.whatsapp.net",
            addressing_mode="pn",
            active=True,
        )
        assert evo_contact is not None
        from smart_core_assistant_painel.app.ui.atendimentos.models import (
            Atendimento,
            Mensagem,
        )

        atendimento = Atendimento.objects.create(contato=contato)
        ctx = dict(atendimento.contexto_conversa or {})
        ctx["api_key"] = instance.api_key
        atendimento.contexto_conversa = ctx
        atendimento.save(update_fields=["contexto_conversa"])
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Oi",
        )
        mensagem.metadados = {
            "evolution": {"instance_id": instance.instance_id}
        }
        mensagem.save(update_fields=["metadados"])
        from unittest.mock import patch

        with patch(
            "smart_core_assistant_painel.app.evolution_sync.signals._resolve_evolution_base_url",
            return_value="http://test-url.com",
        ), patch(
            "smart_core_assistant_painel.app.evolution_sync.services.evolution_api.EvolutionWhatsAppService.send_message"
        ) as mocked_send:
            atendimento.refresh_from_db()
            mensagem.refresh_from_db()

            # Trigger signal
            mensagem.resposta_bot = "Resposta do bot"
            mensagem.respondida = True
            mensagem.save()

            mocked_send.assert_called_once()

    def test_instance_phone_number_filled(self) -> None:
        """Testa que o phone_number é preenchido com o name da instância."""
        payload: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "5588123456789",
            "apikey": "TEST_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "5511999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG_TEST_PHONE",
                    "participant": "",
                    "addressingMode": "pn",
                },
                "pushName": "Cliente Teste",
                "status": "DELIVERY_ACK",
                "message": {"conversation": "Olá"},
                "messageType": "conversation",
                "messageTimestamp": 1763301593,
                "instanceId": "inst-id-123",
                "source": "android",
            },
            "sender": "5511999999999@s.whatsapp.net",
        }

        # Envia webhook
        resp = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # Verifica que a instância foi criada
        instance: EvolutionInstance | None = EvolutionInstance.objects.filter(
            instance_id="inst-id-123"
        ).first()
        self.assertIsNotNone(instance)
        assert instance is not None

        # Verifica que phone_number está preenchido e igual ao name
        self.assertEqual(instance.name, "5588123456789")
        self.assertEqual(instance.phone_number, "5588123456789")
        self.assertEqual(instance.phone_number, instance.name)

    def test_instance_phone_number_updated(self) -> None:
        """Testa que o phone_number é atualizado quando o name muda."""
        # Cria uma instância com phone_number vazio
        instance = EvolutionInstance.objects.create(
            name="5588999999999",
            instance_id="inst-update-test",
            api_key="OLD_KEY",
            phone_number="",  # Vazio inicialmente
        )
        self.assertEqual(instance.phone_number, "")

        # Envia webhook com novo nome
        payload: Dict[str, Any] = {
            "event": "messages.upsert",
            "instance": "5588111111111",  # Nome diferente
            "apikey": "NEW_API_KEY",
            "data": {
                "key": {
                    "remoteJid": "5511888888888@s.whatsapp.net",
                    "fromMe": False,
                    "id": "MSG_UPDATE_TEST",
                    "participant": "",
                    "addressingMode": "pn",
                },
                "pushName": "Cliente Update",
                "status": "DELIVERY_ACK",
                "message": {"conversation": "Update teste"},
                "messageType": "conversation",
                "messageTimestamp": 1763301594,
                "instanceId": "inst-update-test",
                "source": "android",
            },
            "sender": "5511888888888@s.whatsapp.net",
        }

        resp = self.client.post(
            reverse("evolution_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # Recarrega a instância do banco
        instance.refresh_from_db()

        # Verifica que name e phone_number foram atualizados
        self.assertEqual(instance.name, "5588111111111")
        self.assertEqual(instance.phone_number, "5588111111111")
        self.assertEqual(instance.phone_number, instance.name)
