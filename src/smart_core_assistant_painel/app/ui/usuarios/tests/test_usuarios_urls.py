"""Tests for the Usuarios app URLs."""

from django.test import TestCase
from django.urls import resolve, reverse

from smart_core_assistant_painel.app.ui.usuarios import views


class TestUsuariosAppUrls(TestCase):
    """Tests for the Usuarios app URLs."""

    def test_cadastro_url_resolves(self) -> None:
        """Test that the cadastro URL resolves to the correct view."""
        url = reverse("cadastro")
        self.assertEqual(resolve(url).func, views.cadastro)

    def test_login_url_resolves(self) -> None:
        """Test that the login URL resolves to the correct view."""
        url = reverse("login")
        self.assertEqual(resolve(url).func, views.login)

