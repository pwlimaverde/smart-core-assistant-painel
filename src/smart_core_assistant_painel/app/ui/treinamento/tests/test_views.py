
import pytest
from unittest.mock import MagicMock, patch
from django.test import Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from smart_core_assistant_painel.app.ui.treinamento.models import Treinamento, QueryCompose
from smart_core_assistant_painel.app.ui.treinamento.views import treinar_ia, pre_processamento, verificar_treinamentos_vetorizados, verificar_query_compose, cadastrar_query_compose

pytestmark = pytest.mark.django_db

@pytest.fixture
def user():
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def client(user):
    c = Client()
    c.force_login(user)
    return c

@patch("smart_core_assistant_painel.app.ui.treinamento.views.has_permission")
class TestTreinamentoViews:
    def test_treinar_ia_get(self, mock_has_perm, client):
        mock_has_perm.return_value = True
        response = client.get("/ui/treinamento/treinar_ia/") # Assuming url path, or I can use reverse if I knew the name patterns
        # Since I don't know urlconf, I can test view functions directly with RequestFactory
        pass

    def test_treinar_ia_view_get(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        factory = RequestFactory()
        request = factory.get("/treinar_ia")
        request.user = user
        request.session = {}
        request._messages = MagicMock()

        response = treinar_ia(request)
        assert response.status_code == 200

    def test_treinar_ia_view_post_create(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        factory = RequestFactory()
        request = factory.post("/treinar_ia", {"tag": "tag1", "grupo": "grp1", "conteudo": "content"})
        request.user = user
        request.session = {}
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.app.ui.treinamento.views.redirect") as mock_redirect:
            response = treinar_ia(request)
            assert Treinamento.objects.count() == 1
            t = Treinamento.objects.first()
            mock_redirect.assert_called_with("treinamento:pre_processamento", id=t.id)

    def test_treinar_ia_view_post_edit(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        t = Treinamento.objects.create(tag="old", grupo="old", conteudo="old")
        factory = RequestFactory()
        request = factory.post("/treinar_ia", {"tag": "new", "grupo": "new", "conteudo": "new", "treinamento_id": str(t.id)})
        request.user = user
        request.session = {}
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.app.ui.treinamento.views.redirect") as mock_redirect:
            response = treinar_ia(request)
            t.refresh_from_db()
            assert t.tag == "new"
            mock_redirect.assert_called_with("treinamento:pre_processamento", id=t.id)

    def test_pre_processamento_view_get(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        t = Treinamento.objects.create(tag="t", grupo="g", conteudo="content")
        factory = RequestFactory()
        request = factory.get(f"/pre_processamento/{t.id}")
        request.user = user
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.modules.ai_engine.FeaturesCompose.melhoria_ia_treinamento", return_value="improved"):
            response = pre_processamento(request, t.id)
            assert response.status_code == 200

    def test_pre_processamento_view_post_aceitar(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        t = Treinamento.objects.create(tag="t", grupo="g", conteudo="content")
        factory = RequestFactory()
        request = factory.post(f"/pre_processamento/{t.id}", {"acao": "aceitar"})
        request.user = user
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.modules.ai_engine.FeaturesCompose.melhoria_ia_treinamento", return_value="improved"):
            pre_processamento(request, t.id)
            t.refresh_from_db()
            assert t.conteudo == "improved"
            assert t.treinamento_finalizado is True

    def test_verificar_treinamentos_vetorizados_get(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        factory = RequestFactory()
        request = factory.get("/verificar")
        request.user = user
        request._messages = MagicMock()

        response = verificar_treinamentos_vetorizados(request)
        assert response.status_code == 200

    def test_verificar_query_compose_get(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        factory = RequestFactory()
        request = factory.get("/verificar_qc")
        request.user = user
        request._messages = MagicMock()

        response = verificar_query_compose(request)
        assert response.status_code == 200

    def test_cadastrar_query_compose_post(self, mock_has_perm, user):
        mock_has_perm.return_value = True
        factory = RequestFactory()
        request = factory.post("/cadastrar_qc", {
            "tag": "t", "grupo": "g", "descricao": "d", "exemplo": "e", "comportamento": "c"
        })
        request.user = user
        request.session = {}
        request._messages = MagicMock()

        with patch("smart_core_assistant_painel.app.ui.treinamento.views.redirect") as mock_redirect:
            cadastrar_query_compose(request)
            assert QueryCompose.objects.count() == 1
            mock_redirect.assert_called_with("treinamento:cadastrar_query_compose")
