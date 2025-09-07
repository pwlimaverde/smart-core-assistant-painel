"""Testes para formulários do app Operacional."""

import json

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.test import TestCase

from ..models import AtendenteHumano


class AtendenteHumanoForm(ModelForm):
    """Formulário para modelo AtendenteHumano."""

    especialidades = forms.CharField(required=False)

    class Meta:
        model = AtendenteHumano
        fields = ["nome", "cargo", "email", "ativo", "especialidades"]

    def clean_especialidades(self) -> list[str]:
        """Normaliza o campo especialidades para lista de strings."""
        value = self.cleaned_data.get("especialidades")
        if not value:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [
                        str(v).strip()
                        for v in parsed
                        if isinstance(v, (str, int))
                    ]
            except Exception:
                pass
            return [s.strip() for s in value.split(",") if s.strip()]
        return []

    def clean_email(self) -> str:
        """Validação customizada para email."""
        email = self.cleaned_data.get("email")
        if (
            email
            and AtendenteHumano.objects.filter(email=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError("Já existe um atendente com este email.")
        return email


class TestAtendenteHumanoForm(TestCase):
    """Testes para AtendenteHumanoForm."""

    def setUp(self) -> None:
        """Configuração inicial."""
        self.atendente_existente = AtendenteHumano.objects.create(
            nome="Atendente Existente",
            cargo="Analista",
            email="existente@teste.com",
            ativo=True,
        )

    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            "nome": "Novo Atendente",
            "cargo": "Analista",
            "email": "novo@teste.com",
            "ativo": True,
            "especialidades": "Vendas, Suporte",
        }
        form = AtendenteHumanoForm(data=form_data)
        self.assertTrue(form.is_valid())
        atendente = form.save()
        self.assertEqual(atendente.nome, "Novo Atendente")

    def test_email_duplicado(self) -> None:
        """Testa validação de email duplicado."""
        form_data = {
            "nome": "Outro Atendente",
            "cargo": "Supervisor",
            "email": "existente@teste.com",
            "ativo": True,
        }
        form = AtendenteHumanoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_edicao_mesmo_email(self) -> None:
        """Testa que pode manter o mesmo email ao editar."""
        form_data = {
            "nome": "Atendente Editado",
            "cargo": "Gerente",
            "email": "existente@teste.com",
            "ativo": True,
        }
        form = AtendenteHumanoForm(
            data=form_data, instance=self.atendente_existente
        )
        self.assertTrue(form.is_valid())

    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = AtendenteHumanoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        self.assertIn("cargo", form.errors)
