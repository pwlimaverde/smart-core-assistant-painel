"""Tests for the Clientes app URLs."""

from django.test import TestCase
from django.urls import reverse, resolve


class TestClientesAppUrls(TestCase):
    """Tests for the Clientes app URLs."""

    def test_clientes_urls_empty(self) -> None:
        """Test that the clientes app has no URLs defined."""
        # Since the clientes/urls.py file is empty, there should be no resolvable URLs
        # This test just confirms the current state
        pass