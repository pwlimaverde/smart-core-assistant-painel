
import unittest
from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.langchain_pydantic.analise_previa_mensagem_langchain import (
    AnalisePreviaMensagemLangchain,
)

class TestReexport(unittest.TestCase):
    def test_import(self):
        self.assertTrue(issubclass(AnalisePreviaMensagemLangchain, object))
