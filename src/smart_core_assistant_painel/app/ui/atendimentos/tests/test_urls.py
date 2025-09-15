"""Tests for the Atendimentos app URLs."""

from django.test import TestCase
from django.urls import reverse, resolve


class TestAtendimentosUrls(TestCase):
    """Tests for the Atendimentos app URLs."""

    def test_webhook_whatsapp_url_resolves(self) -> None:
        """Test that the webhook_whatsapp URL resolves with correct names."""
        url = reverse('atendimentos:webhook_whatsapp')
        match = resolve(url)
        self.assertEqual(match.url_name, 'webhook_whatsapp')
        self.assertEqual(match.app_name, 'atendimentos')

    def test_webhook_whatsapp_url_name(self) -> None:
        """Test that the webhook_whatsapp URL has the correct path."""
        url = reverse('atendimentos:webhook_whatsapp')
        self.assertEqual(url, '/atendimentos/webhook_whatsapp/')