"""Testes de views para o app `appflowy_adapter`."""

from typing import Any, Dict

from django.test import TestCase
from django.urls import reverse


class TestAppFlowyAdapterViews(TestCase):
    """Valida respostas dos endpoints mínimos."""

    def test_health_endpoint_returns_ok(self) -> None:
        """`GET /api/appflowy_adapter/health/` deve retornar status ok."""

        url: str = reverse("appflowy_adapter:health")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data: Dict[str, Any] = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("adapter"), "appflowy_adapter")
