"""Testes para as views do app Oráculo."""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.http import HttpResponseRedirect
from django.test import Client, TestCase
from django.urls import reverse
from langchain.docstore.document import Document
from rolepermissions.roles import assign_role

from smart_core_assistant_painel.app.ui.oraculo.models import Treinamentos
from smart_core_assistant_painel.app.ui.oraculo.views import (
    TreinamentoService,
    _processar_treinamento,
)


class TestTreinamentoService(TestCase):
    """Testes para a classe TreinamentoService."""

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose.pre_analise_ia_treinamento"
    )
    def test_aplicar_pre_analise_documentos(self, mock_pre_analise):
        """Testa a aplicação da pré-análise em documentos."""
        mock_pre_analise.return_value = "Conteúdo pré-analisado"
        documentos = [
            Document(page_content="Conteúdo 1"),
            Document(page_content="Conteúdo 2"),
        ]

        documentos_processados = (
            TreinamentoService.aplicar_pre_analise_documentos(documentos)
        )

        self.assertEqual(len(documentos_processados), 2)
        self.assertEqual(
            documentos_processados[0].page_content, "Conteúdo pré-analisado"
        )
        self.assertEqual(mock_pre_analise.call_count, 2)

    def test_processar_arquivo_upload_com_caminho_temporario(self):
        """Testa o processamento de um arquivo com temporary_file_path."""
        mock_arquivo = MagicMock()
        mock_arquivo.temporary_file_path.return_value = "/tmp/testfile.txt"

        path = TreinamentoService.processar_arquivo_upload(mock_arquivo)

        self.assertEqual(path, "/tmp/testfile.txt")

    @patch("tempfile.NamedTemporaryFile")
    def test_processar_arquivo_upload_sem_caminho_temporario(
        self, mock_tempfile
    ):
        """Testa o processamento de um arquivo sem temporary_file_path."""
        mock_arquivo = MagicMock()
        del mock_arquivo.temporary_file_path
        mock_arquivo.name = "test.txt"
        mock_arquivo.chunks.return_value = [b"chunk1", b"chunk2"]

        mock_temp_file_instance = MagicMock()
        mock_tempfile.return_value.__enter__.return_value = (
            mock_temp_file_instance
        )
        mock_temp_file_instance.name = "/tmp/tempfile.txt"

        path = TreinamentoService.processar_arquivo_upload(mock_arquivo)

        self.assertEqual(path, "/tmp/tempfile.txt")
        mock_temp_file_instance.write.assert_any_call(b"chunk1")
        mock_temp_file_instance.write.assert_any_call(b"chunk2")

    @patch("os.path.exists", return_value=True)
    @patch("os.unlink")
    def test_limpar_arquivo_temporario(self, mock_unlink, mock_exists):
        """Testa a limpeza de um arquivo temporário."""
        path = "/tmp/testfile.txt"
        TreinamentoService.limpar_arquivo_temporario(path)
        mock_exists.assert_called_once_with(path)
        mock_unlink.assert_called_once_with(path)

    @patch("smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose")
    def test_processar_conteudo_texto(self, mock_features_compose):
        """Testa o processamento de conteúdo de texto."""
        mock_features_compose.pre_analise_ia_treinamento.return_value = (
            "Conteúdo pré-analisado"
        )
        mock_features_compose.load_document_conteudo.return_value = [
            Document(page_content="doc")
        ]

        docs = TreinamentoService.processar_conteudo_texto(
            1, "conteúdo", "tag", "grupo"
        )

        self.assertEqual(len(docs), 1)
        mock_features_compose.pre_analise_ia_treinamento.assert_called_once_with(
            "conteúdo"
        )
        mock_features_compose.load_document_conteudo.assert_called_once_with(
            id="1", conteudo="Conteúdo pré-analisado", tag="tag", grupo="grupo"
        )

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.TreinamentoService.aplicar_pre_analise_documentos"
    )
    @patch("smart_core_assistant_painel.app.ui.oraculo.views.FeaturesCompose")
    def test_processar_arquivo_documento(
        self, mock_features_compose, mock_aplicar_pre_analise
    ):
        """Testa o processamento de um arquivo de documento."""
        mock_features_compose.load_document_file.return_value = [
            Document(page_content="doc")
        ]
        mock_aplicar_pre_analise.return_value = [
            Document(page_content="doc_analisado")
        ]

        docs = TreinamentoService.processar_arquivo_documento(
            1, "/path/to/doc.txt", "tag", "grupo"
        )

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].page_content, "doc_analisado")
        mock_features_compose.load_document_file.assert_called_once_with(
            id="1", path="/path/to/doc.txt", tag="tag", grupo="grupo"
        )
        mock_aplicar_pre_analise.assert_called_once_with(
            [Document(page_content="doc")]
        )


class TestOraculoViews(TestCase):
    """Testes para as views do app Oráculo."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        assign_role(self.user, "gerente")
        self.client.login(username="testuser", password="testpassword")
        self.treinamento = Treinamentos.objects.create(tag="t", grupo="g")

    def test_treinar_ia_get(self):
        """Testa a requisição GET para a view treinar_ia."""
        response = self.client.get(reverse("oraculo:treinar_ia"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "treinar_ia.html")

    def test_treinar_ia_post_sem_tag_ou_grupo(self):
        """Testa a requisição POST sem tag ou grupo."""
        response = self.client.post(
            reverse("oraculo:treinar_ia"), {"conteudo": "teste"}, follow=True
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Tag e Grupo são obrigatórios.")

    def test_treinar_ia_post_sem_conteudo_ou_documento(self):
        """Testa a requisição POST sem conteúdo ou documento."""
        response = self.client.post(
            reverse("oraculo:treinar_ia"),
            {"tag": "t", "grupo": "g"},
            follow=True,
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "É necessário fornecer conteúdo ou documento."
        )

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views._processar_treinamento"
    )
    def test_treinar_ia_post_chama_processar(self, mock_processar):
        """Testa se a requisição POST chama a função de processamento."""
        mock_processar.return_value = HttpResponseRedirect(
            reverse("oraculo:treinar_ia")
        )
        self.client.post(
            reverse("oraculo:treinar_ia"),
            {"tag": "t", "grupo": "g", "conteudo": "c"},
        )
        mock_processar.assert_called_once()

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.TreinamentoService.limpar_arquivo_temporario"
    )
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.TreinamentoService.processar_conteudo_texto"
    )
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.TreinamentoService.processar_arquivo_documento"
    )
    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views.TreinamentoService.processar_arquivo_upload"
    )
    @patch("django.db.transaction.atomic")
    def test_processar_treinamento_sucesso(
        self,
        mock_atomic,
        mock_upload,
        mock_proc_doc,
        mock_proc_texto,
        mock_limpar,
    ):
        """Testa o sucesso do processamento de treinamento."""
        mock_request = MagicMock()
        mock_request.POST.get.side_effect = ["tag", "grupo", "conteudo"]
        mock_request.FILES.get.return_value = "documento"

        _processar_treinamento(mock_request)

        mock_upload.assert_called_once()
        mock_proc_doc.assert_called_once()
        mock_proc_texto.assert_called_once()
        mock_limpar.assert_called_once()

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views._exibir_pre_processamento"
    )
    def test_pre_processamento_get(self, mock_exibir):
        """Testa a requisição GET para a view pre_processamento."""
        mock_exibir.return_value = HttpResponseRedirect(
            reverse("oraculo:treinar_ia")
        )
        self.client.get(
            reverse("oraculo:pre_processamento", args=[self.treinamento.id])
        )
        mock_exibir.assert_called_once()

    @patch(
        "smart_core_assistant_painel.app.ui.oraculo.views._processar_pre_processamento"
    )
    def test_pre_processamento_post(self, mock_processar):
        """Testa a requisição POST para a view pre_processamento."""
        mock_processar.return_value = HttpResponseRedirect(
            reverse("oraculo:treinar_ia")
        )
        self.client.post(
            reverse("oraculo:pre_processamento", args=[self.treinamento.id]),
            {"acao": "aceitar"},
        )
        mock_processar.assert_called_once()
