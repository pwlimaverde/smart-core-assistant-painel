"""Testes para as views do app de usuários."""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from rolepermissions.roles import assign_role, get_user_roles

from smart_core_assistant_painel.app.ui.core.roles import Gerente


class TestUsuariosViews(TestCase):
    """Testes para as views de usuários."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        assign_role(self.user, "gerente")

    def test_cadastro_get(self) -> None:
        """Testa se a página de cadastro é renderizada corretamente via GET."""
        response = self.client.get(reverse("cadastro"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cadastro.html")

    def test_cadastro_post_success(self) -> None:
        """Testa o cadastro de um novo usuário com sucesso."""
        response = self.client.post(
            reverse("cadastro"),
            {
                "username": "newuser",
                "senha": "newpassword",
                "confirmar_senha": "newpassword",
            },
        )
        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_cadastro_post_password_mismatch(self) -> None:
        """Testa o cadastro com senhas que não coincidem."""
        response = self.client.post(
            reverse("cadastro"),
            {
                "username": "newuser",
                "senha": "newpassword",
                "confirmar_senha": "wrongpassword",
            },
            follow=True,
        )
        self.assertContains(response, "As senhas não coincidem.")

    def test_cadastro_post_password_too_short(self) -> None:
        """Testa o cadastro com uma senha muito curta."""
        response = self.client.post(
            reverse("cadastro"),
            {"username": "newuser", "senha": "123", "confirmar_senha": "123"},
            follow=True,
        )
        self.assertContains(
            response, "A senha deve ter pelo menos 6 caracteres."
        )

    def test_cadastro_post_existing_username(self) -> None:
        """Testa o cadastro com um nome de usuário que já existe."""
        response = self.client.post(
            reverse("cadastro"),
            {
                "username": "testuser",
                "senha": "newpassword",
                "confirmar_senha": "newpassword",
            },
            follow=True,
        )
        self.assertContains(response, "Este nome de usuário já existe.")

    def test_login_get(self) -> None:
        """Testa se a página de login é renderizada corretamente via GET."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

    def test_login_post_success(self) -> None:
        """Testa o login de um usuário com sucesso."""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "senha": "testpassword"},
        )
        self.assertRedirects(response, reverse("treinamento:treinar_ia"))

    def test_login_post_invalid_credentials(self) -> None:
        """Testa o login com credenciais inválidas."""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "senha": "wrongpassword"},
            follow=True,
        )
        self.assertContains(response, "Nome de usuário ou senha inválidos.")

    def test_permissoes_get(self) -> None:
        """Testa se a página de permissões é renderizada com a lista de usuários."""
        self.client.login(username="testuser", password="testpassword")
        User.objects.create_user(username="user2", password="password2")
        response = self.client.get(reverse("permissoes"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "permissoes.html")
        self.assertIn("users", response.context)
        self.assertEqual(len(response.context["users"]), 2)

    def test_tornar_gerente(self) -> None:
        """Testa se a view atribui a role de 'gerente' ao usuário."""
        self.client.login(username="testuser", password="testpassword")
        user_to_promote = User.objects.create_user(
            username="user_to_promote", password="password"
        )

        response = self.client.get(
            reverse("tornar_gerente", args=[user_to_promote.id])
        )

        self.assertRedirects(response, reverse("permissoes"))
        user_to_promote.refresh_from_db()
        roles = get_user_roles(user_to_promote)
        self.assertIn(Gerente, roles)
