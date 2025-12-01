
import unittest
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document
from py_return_success_or_error import ErrorReturn, SuccessReturn

from smart_core_assistant_painel.modules.ai_engine.features.features_compose import (
    FeaturesCompose,
)
from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    DocumentError,
    LlmError,
    AnaliseMensageError,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB


class TestFeaturesCompose(unittest.TestCase):

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentConteudoUseCase")
    def test_load_document_conteudo_success(self, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_doc = Document(page_content="test")
        mock_usecase.return_value = SuccessReturn([mock_doc])

        result = FeaturesCompose.load_document_conteudo("id", "content", "tag", "group")

        self.assertEqual(result, [mock_doc])
        mock_usecase_cls.assert_called()

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentConteudoUseCase")
    def test_load_document_conteudo_error(self, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_usecase.return_value = ErrorReturn(DocumentError("Fail"))

        with self.assertRaises(DocumentError):
            FeaturesCompose.load_document_conteudo("id", "content", "tag", "group")

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentFileUseCase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadDocumentFileDatasource")
    def test_load_document_file_success(self, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_doc = Document(page_content="test")
        mock_usecase.return_value = SuccessReturn([mock_doc])

        result = FeaturesCompose.load_document_file("id", "path", "tag", "group")

        self.assertEqual(result, [mock_doc])

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.GenerateEmbeddingsUseCase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.GenerateEmbeddingsLangchainDatasource")
    def test_generate_embeddings_success(self, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_usecase.return_value = SuccessReturn([0.1, 0.2])

        result = FeaturesCompose.generate_embeddings("text")
        self.assertEqual(result, [0.1, 0.2])

    def test_calculate_embedding_similarity(self):
        v1 = [1.0, 0.0]
        v2 = [1.0, 0.0]
        res = FeaturesCompose._calculate_embedding_similarity(v1, v2)
        self.assertAlmostEqual(res, 1.0)

        v3 = [0.0, 1.0]
        res = FeaturesCompose._calculate_embedding_similarity(v1, v3)
        self.assertAlmostEqual(res, 0.0)

        with self.assertRaises(ValueError):
            FeaturesCompose._calculate_embedding_similarity([], [])

        with self.assertRaises(ValueError):
            FeaturesCompose._calculate_embedding_similarity([1.0], [1.0, 2.0])

        with self.assertRaises(ValueError):
            FeaturesCompose._calculate_embedding_similarity([0.0, 0.0], [1.0, 1.0])

    def test_evaluate_triple_similarity(self):
        # No training
        v1 = [1.0, 0.0]
        v2 = [1.0, 0.0]
        res = FeaturesCompose._evaluate_triple_similarity(v1, v2, None)
        self.assertAlmostEqual(res, 0.75) # 0.75 * 1.0

        # With training - perfect match
        v3 = [1.0, 0.0]
        res = FeaturesCompose._evaluate_triple_similarity(v1, v2, v3)
        # sr=1, sq=1, st=1. base = 0.5 + 0.25 + 0.25 = 1.0. min_qt=1. No penalty.
        self.assertAlmostEqual(res, 1.0)

        # With training - inconsistency
        # Msg=A, Resp=A, Train=B (orthogonal)
        # sr=1. sq=0. st=0.
        # base = 0.5. min_qt=0. penalty = (0.4 - 0) * 0.5 = 0.2
        # final = 0.5 - 0.2 = 0.3
        v1 = [1.0, 0.0]
        v2 = [1.0, 0.0]
        v3 = [0.0, 1.0]
        res = FeaturesCompose._evaluate_triple_similarity(v1, v2, v3)
        self.assertAlmostEqual(res, 0.3)

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.GenerateChunksUseCase")
    def test_generate_chunks_success(self, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_doc = Document(page_content="chunk")
        mock_usecase.return_value = SuccessReturn([mock_doc])

        result = FeaturesCompose.generate_chunks("content", {})
        self.assertEqual(result, [mock_doc])

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.LoadMensageDataUseCase")
    def test_load_message_data_success(self, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_msg_data = MagicMock()
        mock_msg_data.metadados = {"key": "val"}
        mock_msg_data.conteudo = "Conteudo"
        mock_usecase.return_value = SuccessReturn(mock_msg_data)

        result = FeaturesCompose.load_message_data({"key": "val"})
        self.assertEqual(result, mock_msg_data)
        self.assertEqual(result.conteudo, "Conteudo")

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseMensageUseCase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseMensageDatasource")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.FeaturesCompose.generate_embeddings")
    def test_analise_mensage_success(self, mock_gen_emb, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        # Mock analysis result (response text)
        mock_usecase.return_value = SuccessReturn("Resposta do bot")

        # Mock embeddings
        mock_gen_emb.return_value = [1.0, 0.0]

        with patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB") as mock_hub:
            mock_hub.LLM_CLASS = MagicMock()
            mock_hub.MODEL = "model"
            mock_hub.LLM_TEMPERATURE = 0

            result = FeaturesCompose.analise_mensage(
                fluxos_disponiveis={},
                context="pergunta",
                historico_atendimento={},
                prompt_human="prompt",
                dados_treinamento="treino"
            )

            self.assertEqual(result.resposta_bot, "Resposta do bot")
            self.assertFalse(result.transferir_atendimento)

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseMensageUseCase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseMensageDatasource")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.FeaturesCompose.generate_embeddings")
    def test_analise_mensage_low_confidence(self, mock_gen_emb, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_usecase.return_value = SuccessReturn("Resposta incerta")

        # Mock embeddings to produce low score
        # Msg=[1,0], Resp=[0,1], Train=[1,0]
        # sr=0, sq=1, st=0.
        # base = 0 + 0.25 + 0 = 0.25
        # min_qt=0. penalty = 0.2. final = 0.05.

        def side_effect(text):
            if text == "pergunta": return [1.0, 0.0]
            if text == "treino": return [1.0, 0.0]
            return [0.0, 1.0] # response

        mock_gen_emb.side_effect = side_effect

        with patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB") as mock_hub:
            result = FeaturesCompose.analise_mensage(
                fluxos_disponiveis={"Financeiro - 1": "f1"},
                context="pergunta",
                historico_atendimento={},
                prompt_human="prompt",
                dados_treinamento="treino"
            )

            self.assertTrue(result.transferir_atendimento)
            self.assertIn("Vou transferir", result.resposta_bot)
            self.assertEqual(result.fluxo_transferencia, "")

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseMensageUseCase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseMensageDatasource")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.FeaturesCompose.generate_embeddings")
    def test_analise_mensage_explicit_transfer(self, mock_gen_emb, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_usecase.return_value = SuccessReturn("Estarei transferindo seu atendimento para Financeiro.")
        mock_gen_emb.return_value = [1.0, 0.0]

        with patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB") as mock_hub:
            result = FeaturesCompose.analise_mensage(
                fluxos_disponiveis={"Financeiro - 1": "f1"},
                context="context",
                historico_atendimento={},
                prompt_human="prompt",
                dados_treinamento=""
            )

            self.assertTrue(result.transferir_atendimento)
            self.assertEqual(result.fluxo_transferencia, "Financeiro - 1")
            # Should not append generic transfer message if explicit
            self.assertEqual(result.resposta_bot, "Estarei transferindo seu atendimento para Financeiro.")

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnalisePreviaMensagemUsecase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnalisePreviaLangchainDatasource")
    def test_analise_previa_mensagem(self, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_result = MagicMock()
        mock_usecase.return_value = SuccessReturn(mock_result)

        with patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB") as mock_hub:
            result = FeaturesCompose.analise_previa_mensagem({}, "ctx", "valid")
            self.assertEqual(result, mock_result)

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoUseCase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoLangchainDatasource")
    def test_pre_analise_ia_treinamento(self, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_usecase.return_value = SuccessReturn("analise")

        with patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB") as mock_hub:
            result = FeaturesCompose.pre_analise_ia_treinamento("ctx")
            self.assertEqual(result, "analise")

    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoUseCase")
    @patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.AnaliseConteudoLangchainDatasource")
    def test_melhoria_ia_treinamento(self, mock_ds_cls, mock_usecase_cls):
        mock_usecase = mock_usecase_cls.return_value
        mock_usecase.return_value = SuccessReturn("melhoria")

        with patch("smart_core_assistant_painel.modules.ai_engine.features.features_compose.SERVICEHUB") as mock_hub:
            result = FeaturesCompose.melhoria_ia_treinamento("ctx")
            self.assertEqual(result, "melhoria")

    def test_empty_methods(self):
        FeaturesCompose.mensagem_apresentacao()
        FeaturesCompose.solicitacao_info_cliene()
        FeaturesCompose.resumo_atendimento()

    def test_converter_contexto_error(self):
        # converter_contexto just returns "contexto" but has try/except
        # It swallows error and raises it?
        # "raise e"
        # But try block is simple return.
        # Hard to fail unless memory error?
        self.assertEqual(FeaturesCompose.converter_contexto({}), "contexto")
