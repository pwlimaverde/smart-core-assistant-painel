
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from smart_core_assistant_painel.app.ui.treinamento.models import Treinamento, Documento, QueryCompose
from smart_core_assistant_painel.app.ui.treinamento.signals import (
    signals_gerar_documentos_treinamento,
    signals_embeddings_documento,
    signals_embeddings_query_compose,
    __gerar_documentos as task_gerar_documentos,
    __gerar_embedding_documento as task_gerar_emb_doc,
    __gerar_embedding_query_compose as task_gerar_emb_qc,
    signal_remover_treinamento_ia,
    __task_remover_treinamento_ia as task_remover_treinamento
)

pytestmark = pytest.mark.django_db

class TestTreinamentoSignals:
    @patch("smart_core_assistant_painel.app.ui.treinamento.signals.async_task")
    def test_signals_gerar_documentos_treinamento(self, mock_task):
        t = Treinamento(id=1, treinamento_finalizado=True, treinamento_vetorizado=False)
        signals_gerar_documentos_treinamento(Treinamento, t, False)
        mock_task.assert_called_with(task_gerar_documentos, 1)

        mock_task.reset_mock()
        t.treinamento_vetorizado = True
        signals_gerar_documentos_treinamento(Treinamento, t, False)
        mock_task.assert_not_called()

    @patch("smart_core_assistant_painel.app.ui.treinamento.signals.async_task")
    def test_signals_embeddings_documento(self, mock_task):
        d = Documento(id=1, conteudo="c", embedding=None)
        signals_embeddings_documento(Documento, d, True)
        mock_task.assert_called_with(task_gerar_emb_doc, 1)

        mock_task.reset_mock()
        d.embedding = [0.1]
        signals_embeddings_documento(Documento, d, False)
        mock_task.assert_not_called()

    @patch("smart_core_assistant_painel.app.ui.treinamento.signals.async_task")
    def test_signals_embeddings_query_compose(self, mock_task):
        qc = QueryCompose(id=1, descricao="d", embedding=None)
        signals_embeddings_query_compose(QueryCompose, qc, True)
        mock_task.assert_called_with(task_gerar_emb_qc, 1)

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.FeaturesCompose.generate_chunks")
    def test_task_gerar_documentos(self, mock_chunks):
        t = Treinamento.objects.create(tag="t1", grupo="g1", conteudo="content", treinamento_finalizado=True)
        mock_chunks.return_value = [Document(page_content="chunk1", metadata={})]

        task_gerar_documentos(t.id)

        t.refresh_from_db()
        assert t.treinamento_vetorizado is True
        assert Documento.objects.filter(treinamento=t).count() == 1

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.FeaturesCompose.generate_embeddings")
    def test_task_gerar_embedding_documento(self, mock_emb):
        t = Treinamento.objects.create(tag="t2", grupo="g2")
        d = Documento.objects.create(treinamento=t, conteudo="content")
        mock_emb.return_value = [0.1] * 1024

        task_gerar_emb_doc(d.id)

        d.refresh_from_db()
        # Vector field check implicitly via no exception

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.FeaturesCompose.generate_embeddings")
    def test_task_gerar_embedding_query_compose(self, mock_emb):
        qc = QueryCompose.objects.create(tag="t", grupo="g", descricao="desc", exemplo="ex", comportamento="c")
        mock_emb.return_value = [0.1] * 1024

        task_gerar_emb_qc(qc.id)

        qc.refresh_from_db()

    def test_signal_remover_treinamento(self):
        t = Treinamento(id=1, treinamento_finalizado=True)
        with patch("smart_core_assistant_painel.app.ui.treinamento.signals.__task_remover_treinamento_ia") as mock_task:
            signal_remover_treinamento_ia(Treinamento, t)
            mock_task.assert_called_with(1)

    def test_task_remover_treinamento_ia(self):
        t = Treinamento.objects.create(tag="t3", grupo="g3", treinamento_vetorizado=True)
        task_remover_treinamento(t.id)
        t.refresh_from_db()
        assert t.treinamento_vetorizado is False
