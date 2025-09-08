"""Tests for the Treinamento app URLs."""

from django.test import TestCase
from django.urls import reverse, resolve

from smart_core_assistant_painel.app.ui.treinamento import views


class TestTreinamentoAppUrls(TestCase):
    """Tests for the Treinamento app URLs."""

    def test_treinar_ia_url_resolves(self) -> None:
        """Test that the treinar_ia URL resolves to the correct view."""
        url = reverse('treinamento:treinar_ia')
        self.assertEqual(resolve(url).func, views.treinar_ia)

    def test_pre_processamento_url_resolves(self) -> None:
        """Test that the pre_processamento URL resolves to the correct view."""
        url = reverse('treinamento:pre_processamento', args=[1])
        self.assertEqual(resolve(url).func, views.pre_processamento)

    def test_verificar_treinamentos_vetorizados_url_resolves(self) -> None:
        """Test that the verificar_treinamentos_vetorizados URL resolves to the correct view."""
        url = reverse('treinamento:verificar_treinamentos_vetorizados')
        self.assertEqual(resolve(url).func, views.verificar_treinamentos_vetorizados)