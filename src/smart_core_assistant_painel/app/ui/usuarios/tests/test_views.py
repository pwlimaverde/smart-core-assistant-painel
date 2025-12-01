
import pytest
from unittest.mock import MagicMock, patch
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.shortcuts import reverse
from smart_core_assistant_painel.app.ui.usuarios.views import (
    cadastro, login, permissoes, tornar_gerente, dashboard_gerente
)
from smart_core_assistant_painel.app.ui.operacional.models import Atendente

pytestmark = pytest.mark.django_db

class TestUsuariosViews:
    def test_cadastro_get(self):
        factory = RequestFactory()
        request = factory.get("/cadastro")
        response = cadastro(request)
        assert response.status_code == 200

    def test_cadastro_post_valid(self):
        factory = RequestFactory()
        request = factory.post("/cadastro", {
            "username": "newuser",
            "senha": "password123",
            "confirmar_senha": "password123"
        })
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.app.ui.usuarios.views.redirect") as mock_redirect:
            response = cadastro(request)
            assert User.objects.filter(username="newuser").exists()
            mock_redirect.assert_called_with("login")

    def test_cadastro_post_invalid(self):
        factory = RequestFactory()
        request = factory.post("/cadastro", {
            "username": "newuser",
            "senha": "password123",
            "confirmar_senha": "different"
        })
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.app.ui.usuarios.views.redirect") as mock_redirect:
            response = cadastro(request)
            assert not User.objects.filter(username="newuser").exists()
            mock_redirect.assert_called_with("cadastro")

    @patch("smart_core_assistant_painel.app.ui.usuarios.views.authenticate")
    @patch("smart_core_assistant_painel.app.ui.usuarios.views.auth.login")
    def test_login_post_valid(self, mock_auth_login, mock_authenticate):
        user = User.objects.create_user(username="u", password="p")
        mock_authenticate.return_value = user

        factory = RequestFactory()
        request = factory.post("/login", {"username": "u", "senha": "p"})
        request.session = {}
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.app.ui.usuarios.views.redirect") as mock_redirect:
            response = login(request)
            mock_auth_login.assert_called()
            mock_redirect.assert_called_with("treinamento:treinar_ia")

    @patch("smart_core_assistant_painel.app.ui.usuarios.views.authenticate")
    @patch("smart_core_assistant_painel.app.ui.usuarios.views.auth.login")
    def test_login_post_valid_redirect_kanban(self, mock_auth_login, mock_authenticate):
        user = User.objects.create_user(username="u", password="p")
        mock_authenticate.return_value = user

        # Mock Atendente
        mock_atendente = MagicMock(spec=Atendente)
        mock_atendente.departamento_id = 10
        mock_atendente.departamento = MagicMock()

        with patch("smart_core_assistant_painel.app.ui.operacional.models.Atendente.objects.filter") as mock_at_filter:
            mock_at_filter.return_value.select_related.return_value.first.return_value = mock_atendente

            factory = RequestFactory()
            request = factory.post("/login", {"username": "u", "senha": "p"})
            request.session = {}
            request._messages = MagicMock()

            with patch("smart_core_assistant_painel.app.ui.usuarios.views.redirect") as mock_redirect:
                response = login(request)
                mock_redirect.assert_called_with("atendimentos:kanban_departamento", departamento_id=10)

    def test_permissoes(self):
        factory = RequestFactory()
        request = factory.get("/permissoes")
        response = permissoes(request)
        assert response.status_code == 200

    @patch("smart_core_assistant_painel.app.ui.usuarios.views.assign_role")
    def test_tornar_gerente(self, mock_assign):
        user = User.objects.create_user(username="u", password="p")
        factory = RequestFactory()
        request = factory.post(f"/tornar_gerente/{user.id}")

        with patch("smart_core_assistant_painel.app.ui.usuarios.views.redirect") as mock_redirect:
            tornar_gerente(request, user.id)
            mock_assign.assert_called_with(user, "gerente")
            mock_redirect.assert_called_with("permissoes")

    @patch("smart_core_assistant_painel.app.ui.usuarios.views.has_permission")
    def test_dashboard_gerente_access(self, mock_has_perm):
        user = User.objects.create_user(username="u", password="p")
        mock_has_perm.return_value = True

        factory = RequestFactory()
        request = factory.get("/dashboard")
        request.user = user

        response = dashboard_gerente(request)
        assert response.status_code == 200

    def test_dashboard_gerente_no_auth(self):
        factory = RequestFactory()
        request = factory.get("/dashboard")
        request.user = MagicMock(is_authenticated=False)

        with patch("smart_core_assistant_painel.app.ui.usuarios.views.redirect") as mock_redirect:
            dashboard_gerente(request)
            mock_redirect.assert_called_with("login")
