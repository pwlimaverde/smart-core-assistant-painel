"""Tests for the Atendimentos app URLs."""

from django.test import TestCase
from django.urls import reverse, resolve

from smart_core_assistant_painel.app.ui.atendimentos.views import webhook_whatsapp


class TestAtendimentosUrls(TestCase):
    """Tests for the Atendimentos app URLs."""

    def test_webhook_whatsapp_url_resolves(self) -> None:
        """Test that the webhook_whatsapp URL resolves to the correct view."""
        url = reverse('atendimentos:webhook_whatsapp')
        self.assertEqual(resolve(url).func, webhook_whatsapp)

    def test_webhook_whatsapp_url_name(self) -> None:
        """Test that the webhook_whatsapp URL has the correct name."""
        url = reverse('atendimentos:webhook_whatsapp')
        self.assertEqual(url, '/atendimentos/webhook_whatsapp/')