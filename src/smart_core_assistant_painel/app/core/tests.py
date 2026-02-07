"""Testes para views do aplicativo core.

Este módulo contém testes para as views básicas do sistema,
incluindo health check e página inicial.
"""

from django.test import Client, TestCase
from django.urls import reverse


class CoreViewsTestCase(TestCase):
    """Testes para views do core."""

    def setUp(self) -> None:
        """Configuração inicial dos testes."""
        self.client = Client()

    def test_health_check_view(self) -> None:
        """Testa a view de health check."""
        url = reverse("health_check")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_home_view(self) -> None:
        """Testa a view da página inicial."""
        url = reverse("home")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Smart Core Assistant Painel", response.content.decode())
        self.assertIn(
            "Sistema funcionando corretamente!", response.content.decode()
        )
        self.assertIn("/admin/", response.content.decode())

    def test_health_check_direct_url(self) -> None:
        """Testa acesso direto à URL de health check."""
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "OK")

    def test_home_direct_url(self) -> None:
        """Testa acesso direto à URL raiz."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Smart Core Assistant Painel", response.content.decode())
