"""Testes de URLs para o app `appflowy_adapter`."""

from django.test import TestCase
from django.urls import resolve, reverse

from smart_core_assistant_painel.app.appflowy_adapter import views


class TestAppFlowyAdapterUrls(TestCase):
    """Verifica resolução e paths das rotas principais."""

    def test_health_url_resolves(self) -> None:
        """Confere resolução da URL de saúde."""

        url: str = reverse("appflowy_adapter:health")
        match = resolve(url)
        self.assertEqual(match.url_name, "health")
        self.assertEqual(match.app_name, "appflowy_adapter")
        self.assertEqual(match.func, views.health)
        self.assertEqual(url, "/api/appflowy_adapter/health/")
