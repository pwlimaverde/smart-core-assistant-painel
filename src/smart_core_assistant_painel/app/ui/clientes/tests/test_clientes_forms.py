"""Testes para formulários do app Clientes."""

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.test import TestCase

from smart_core_assistant_painel.app.ui.clientes.models import Contato


class ClientesContatoForm(ModelForm):
    """Formulário para modelo Contato."""

    class Meta:
        model = Contato
        fields = ["telefone", "nome_contato", "nome_perfil_whatsapp"]

    def clean_telefone(self) -> str:
        """Validação customizada para telefone."""
        telefone = self.cleaned_data.get("telefone")
        if telefone:
            telefone_limpo = "".join(filter(str.isdigit, telefone))
            if len(telefone_limpo) < 10 or len(telefone_limpo) > 13:
                raise ValidationError("Telefone deve ter entre 10 e 13 dígitos.")
            return telefone_limpo
        return telefone


class TestClientesContatoForm(TestCase):
    """Testes para ContatoForm."""

    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            "telefone": "11999999999",
            "nome_contato": "Cliente Teste",
            "nome_perfil_whatsapp": "Cliente WhatsApp",
        }
        form = ClientesContatoForm(data=form_data)
        self.assertTrue(form.is_valid())
        contato = form.save()
        self.assertEqual(contato.telefone, "5511999999999")
        self.assertEqual(contato.nome_contato, "Cliente Teste")

    def test_telefone_com_formatacao(self) -> None:
        """Testa limpeza de telefone com formatação."""
        form_data = {
            "telefone": "(11) 99999-9999",
            "nome_contato": "Cliente Teste",
        }
        form = ClientesContatoForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["telefone"], "11999999999")

    def test_telefone_muito_curto(self) -> None:
        """Testa validação de telefone muito curto."""
        form_data = {"telefone": "119999", "nome_contato": "Cliente Teste"}
        form = ClientesContatoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("telefone", form.errors)

    def test_telefone_muito_longo(self) -> None:
        """Testa validação de telefone muito longo."""
        form_data = {
            "telefone": "551199999999999",
            "nome_contato": "Cliente Teste",
        }
        form = ClientesContatoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("telefone", form.errors)

    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = ClientesContatoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("telefone", form.errors)

    def test_campos_opcionais(self) -> None:
        """Testa que nome_contato e nome_perfil_whatsapp são opcionais."""
        form_data = {
            "telefone": "11999999999",
        }
        form = ClientesContatoForm(data=form_data)
        self.assertTrue(form.is_valid())
