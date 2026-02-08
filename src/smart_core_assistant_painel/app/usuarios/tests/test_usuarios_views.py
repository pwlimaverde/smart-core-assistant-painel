"""Tests for the Usuarios app views."""

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse


class TestUsuariosAppViews(TestCase):
    """Tests for the Usuarios app views."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_cadastro_get(self) -> None:
        """Test cadastro view GET request."""
        # Act
        response = self.client.get(reverse("cadastro"))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cadastro.html")

    def test_cadastro_post_success(self) -> None:
        """Test successful user registration."""
        # Act
        response = self.client.post(
            reverse("cadastro"),
            {
                "username": "newuser",
                "senha": "newpass123",
                "confirmar_senha": "newpass123",
            },
        )

        # Assert
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_cadastro_post_password_mismatch(self) -> None:
        """Test registration with password mismatch."""
        # Act
        response = self.client.post(
            reverse("cadastro"),
            {
                "username": "newuser",
                "senha": "newpass123",
                "confirmar_senha": "differentpass",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("As senhas não coincidem" in str(m) for m in messages)
        )

    def test_cadastro_post_password_too_short(self) -> None:
        """Test registration with password too short."""
        # Act
        response = self.client.post(
            reverse("cadastro"),
            {"username": "newuser", "senha": "123", "confirmar_senha": "123"},
        )

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "A senha deve ter pelo menos 6 caracteres" in str(m)
                for m in messages
            )
        )

    def test_cadastro_post_username_exists(self) -> None:
        """Test registration with existing username."""
        # Arrange
        User.objects.create_user(
            username="existinguser", password="testpass123"
        )

        # Act
        response = self.client.post(
            reverse("cadastro"),
            {
                "username": "existinguser",
                "senha": "newpass123",
                "confirmar_senha": "newpass123",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Este nome de usuário já existe" in str(m) for m in messages)
        )

    def test_cadastro_post_missing_fields(self) -> None:
        """Test registration with missing fields."""
        # Act
        response = self.client.post(
            reverse("cadastro"),
            {"username": "", "senha": "", "confirmar_senha": ""},
        )

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "Nome de usuário e senha são obrigatórios" in str(m)
                for m in messages
            )
        )

    def test_login_get(self) -> None:
        """Test login view GET request."""
        # Act
        response = self.client.get(reverse("login"))

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_post_success(self) -> None:
        """Test successful user login."""
        # Act
        response = self.client.post(
            reverse("login"), {"username": "testuser", "senha": "testpass123"}
        )

        # Assert
        self.assertRedirects(
            response,
            reverse("treinamento:treinar_ia"),
            fetch_redirect_response=False,
        )

    def test_login_post_invalid_credentials(self) -> None:
        """Test login with invalid credentials."""
        # Act
        response = self.client.post(
            reverse("login"), {"username": "nonexistent", "senha": "wrongpass"}
        )

        # Assert
        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "Nome de usuário ou senha inválidos" in str(m)
                for m in messages
            )
        )
