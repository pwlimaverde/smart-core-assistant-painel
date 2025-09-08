"""Testes para formulários do app Atendimentos."""

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.test import TestCase

from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.operacional.models import AtendenteHumano
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)


class AtendimentoForm(ModelForm):
    """Formulário para modelo Atendimento."""

    class Meta:
        model = Atendimento
        fields = [
            "contato",
            "atendente_humano",
            "status",
            "assunto",
            "prioridade",
        ]

    def clean(self) -> dict:
        """Validação geral do formulário."""
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        atendente_humano = cleaned_data.get("atendente_humano")

        if status == StatusAtendimento.TRANSFERIDO and not atendente_humano:
            raise ValidationError(
                "Atendimento transferido requer um atendente designado."
            )

        if atendente_humano and not atendente_humano.ativo:
            raise ValidationError("Atendente selecionado não está ativo.")

        return cleaned_data


class TestAtendimentoForm(TestCase):
    """Testes para AtendimentoForm."""

    def setUp(self) -> None:
        """Configuração inicial."""
        self.contato = Contato.objects.create(
            telefone="11999999999", nome_contato="Cliente Teste"
        )

        self.atendente_ativo = AtendenteHumano.objects.create(
            nome="Atendente Ativo", email="ativo@teste.com", ativo=True
        )

        self.atendente_inativo = AtendenteHumano.objects.create(
            nome="Atendente Inativo", email="inativo@teste.com", ativo=False
        )

    def test_form_valido_bot(self) -> None:
        """Testa formulário válido para atendimento por bot."""
        form_data = {
            "contato": self.contato.id,
            "status": StatusAtendimento.EM_ANDAMENTO,
            "assunto": "Atendimento por bot",
            "prioridade": "normal",
        }
        form = AtendimentoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valido_humano(self) -> None:
        """Testa formulário válido para atendimento humano."""
        form_data = {
            "contato": self.contato.id,
            "atendente_humano": self.atendente_ativo.id,
            "status": StatusAtendimento.TRANSFERIDO,
            "assunto": "Atendimento humano",
            "prioridade": "alta",
        }
        form = AtendimentoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_transferido_sem_atendente(self) -> None:
        """Testa validação de atendimento transferido sem atendente."""
        form_data = {
            "contato": self.contato.id,
            "status": StatusAtendimento.TRANSFERIDO,
        }
        form = AtendimentoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_atendente_inativo(self) -> None:
        """Testa validação de atendente inativo."""
        form_data = {
            "contato": self.contato.id,
            "atendente_humano": self.atendente_inativo.id,
            "status": StatusAtendimento.TRANSFERIDO,
        }
        form = AtendimentoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = AtendimentoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("contato", form.errors)
        self.assertIn("status", form.errors)


class MensagemForm(ModelForm):
    """Formulário para modelo Mensagem."""

    class Meta:
        model = Mensagem
        fields = ["atendimento", "conteudo", "tipo", "remetente"]

    def clean_conteudo(self) -> str:
        """Validação customizada para conteúdo."""
        conteudo = self.cleaned_data.get("conteudo")
        if conteudo and len(conteudo.strip()) == 0:
            raise ValidationError("Mensagem não pode estar vazia.")
        return conteudo


class TestMensagemForm(TestCase):
    """Testes para MensagemForm."""

    def setUp(self) -> None:
        """Configuração inicial."""
        contato = Contato.objects.create(
            telefone="11999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.EM_ANDAMENTO
        )

    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            "atendimento": self.atendimento.id,
            "conteudo": "Mensagem de teste",
            "tipo": TipoMensagem.TEXTO_FORMATADO,
            "remetente": TipoRemetente.CONTATO,
        }
        form = MensagemForm(data=form_data)
        self.assertTrue(form.is_valid())
        mensagem = form.save()
        self.assertEqual(mensagem.conteudo, "Mensagem de teste")

    def test_conteudo_vazio(self) -> None:
        """Testa validação de conteúdo vazio."""
        form_data = {
            "atendimento": self.atendimento.id,
            "conteudo": "   ",
            "tipo": TipoMensagem.TEXTO_FORMATADO,
            "remetente": TipoRemetente.CONTATO,
        }
        form = MensagemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("conteudo", form.errors)

    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = MensagemForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("atendimento", form.errors)
        self.assertIn("conteudo", form.errors)
        self.assertIn("tipo", form.errors)
        self.assertIn("remetente", form.errors)
