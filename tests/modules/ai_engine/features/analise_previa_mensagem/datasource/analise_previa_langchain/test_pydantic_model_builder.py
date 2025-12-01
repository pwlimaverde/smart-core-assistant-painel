
import unittest
from typing import get_args, get_origin

from smart_core_assistant_painel.modules.ai_engine.features.analise_previa_mensagem.datasource.analise_previa_langchain.pydantic_model_builder import (
    _build_docstring,
    _extract_allowed_values,
    _extract_examples,
    _fixed_entities_doc_section,
    _get_fixed_entity_types,
    build_analise_previa_model,
)

class TestPydanticModelBuilder(unittest.TestCase):
    def test_get_fixed_entity_types(self):
        types = _get_fixed_entity_types()
        self.assertIsInstance(types, set)
        self.assertIn("nome_contato", types)
        self.assertIn("cpf_cliente", types)

    def test_fixed_entities_doc_section(self):
        doc = _fixed_entities_doc_section()
        self.assertIn("ENTIDADES FIXAS", doc)
        self.assertIn("nome_contato:", doc)

    def test_extract_allowed_values(self):
        # Empty
        allowed, desc = _extract_allowed_values([], "test")
        self.assertEqual(allowed, tuple())
        self.assertIn("não fornecida", desc)

        # None
        allowed, desc = _extract_allowed_values(None, "test")
        self.assertEqual(allowed, tuple())

        # Valid items
        items = [
            {"type": "t1"},
            {"label": "t2"},
            {"nome": "t3"},
            {"name": "t4"},
            {"type": "t1"}, # duplicate
            {"other": "x"} # ignored
        ]
        allowed, desc = _extract_allowed_values(items, "test")
        self.assertEqual(allowed, ("t1", "t2", "t3", "t4"))
        self.assertIn("t1", desc)

        # Empty result after filtering
        items = [{"other": "x"}]
        allowed, desc = _extract_allowed_values(items, "test")
        self.assertEqual(allowed, tuple())
        self.assertIn("Lista de test permitidos vazia", desc)

    def test_extract_examples(self):
        # Empty
        self.assertEqual(_extract_examples([]), [])
        self.assertEqual(_extract_examples(None), [])

        # Valid items with various example keys
        items = [
            {"type": "t1", "exemplos": ["ex1"]},
            {"type": "t2", "examples": "ex2"},
            {"type": "t3", "example": "ex3"},
            {"type": "t4", "amostras": ["ex4"]},
            {"type": "t5", "descricao": "desc5"},
            {"type": "t6"}, # no example/desc
            {"other": "x"} # ignored
        ]
        examples = _extract_examples(items)
        self.assertEqual(len(examples), 6)
        self.assertEqual(examples[0], {"type": "t1", "value": "ex1"})
        self.assertEqual(examples[1], {"type": "t2", "value": "ex2"})
        self.assertEqual(examples[2], {"type": "t3", "value": "ex3"})
        self.assertEqual(examples[3], {"type": "t4", "value": "ex4"})
        self.assertEqual(examples[4], {"type": "t5", "value": "desc5"})
        self.assertEqual(examples[5], {"type": "t6", "value": "exemplo"})

    def test_build_docstring(self):
        intents = [{"type": "i1", "descricao": "d1"}]
        entities = [{"type": "e1", "descricao": "d2"}]

        doc = _build_docstring(intents, entities)
        self.assertIn("INSTRUÇÕES", doc)
        self.assertIn("INTENTS DISPONÍVEIS", doc)
        self.assertIn("- i1: d1", doc)
        self.assertIn("ENTIDADES DISPONÍVEIS", doc)
        self.assertIn("- e1: d2", doc)
        self.assertIn("ENTIDADES FIXAS", doc)

        # Empty
        doc = _build_docstring(None, None)
        self.assertNotIn("INTENTS DISPONÍVEIS", doc)

    def test_build_analise_previa_model(self):
        intents = [{"type": "i1"}]
        entities = [{"type": "e1"}]

        Model = build_analise_previa_model(
            intent_types_json=intents,
            entity_types_json=entities
        )

        self.assertTrue(hasattr(Model, "__intent_allowed__"))
        self.assertTrue(hasattr(Model, "__entity_allowed__"))

        self.assertIn("i1", Model.__intent_allowed__)
        self.assertIn("e1", Model.__entity_allowed__)
        self.assertIn("nome_contato", Model.__entity_allowed__) # Fixed entity

        # Instantiate
        inst = Model(
            intent=[{"type": "i1", "value": "v"}],
            entities=[{"type": "e1", "value": "v"}]
        )
        self.assertTrue(hasattr(inst, "intent"))
        self.assertTrue(hasattr(inst, "entities"))
        self.assertEqual(inst.intent[0].type, "i1")

    def test_build_analise_previa_model_empty(self):
        Model = build_analise_previa_model(
            intent_types_json=None,
            entity_types_json=None
        )
        inst = Model(
            intent=[],
            entities=[]
        )
        self.assertTrue(hasattr(inst, "intent"))
        self.assertTrue(hasattr(inst, "entities"))
