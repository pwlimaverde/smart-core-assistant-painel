"""Testes para formulários do app Treinamento."""

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.test import TestCase

from ..models import Treinamento


class TreinamentosForm(ModelForm):
    """Formulário para modelo Treinamentos."""

    class Meta:
        model = Treinamento
        fields = ["tag", "grupo", "treinamento_finalizado"]

    def clean_tag(self) -> str:
        """Validação customizada para tag."""
        tag = self.cleaned_data.get("tag")
        if tag and len(tag.strip()) < 3:
            raise ValidationError("Tag deve ter pelo menos 3 caracteres.")
        return tag

    def clean_grupo(self) -> str:
        """Validação customizada para grupo."""
        grupo = self.cleaned_data.get("grupo")
        if grupo and len(grupo.strip()) < 3:
            raise ValidationError("Grupo deve ter pelo menos 3 caracteres.")
        return grupo


class TestTreinamentosForm(TestCase):
    """Testes para TreinamentosForm."""

    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            "tag": "atendimento_geral",
            "grupo": "atendimento",
            "treinamento_finalizado": True,
        }
        form = TreinamentosForm(data=form_data)
        self.assertTrue(form.is_valid())
        treinamento = form.save()
        self.assertEqual(treinamento.tag, "atendimento_geral")

    def test_tag_muito_curta(self) -> None:
        """Testa validação de tag muito curta."""
        form_data = {
            "tag": "ab",
            "grupo": "teste",
            "treinamento_finalizado": False,
        }
        form = TreinamentosForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("tag", form.errors)

    def test_grupo_muito_curto(self) -> None:
        """Testa validação de grupo muito curto."""
        form_data = {
            "tag": "tag_valida",
            "grupo": "ab",
            "treinamento_finalizado": False,
        }
        form = TreinamentosForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("grupo", form.errors)

    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = TreinamentosForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("tag", form.errors)
        self.assertIn("grupo", form.errors)

    def test_treinamento_finalizado_opcional(self) -> None:
        """Testa que treinamento_finalizado é opcional."""
        form_data = {
            "tag": "tag_valida",
            "grupo": "grupo_valido",
        }
        form = TreinamentosForm(data=form_data)
        self.assertTrue(form.is_valid())
