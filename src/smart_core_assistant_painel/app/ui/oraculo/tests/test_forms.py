"""Testes para formulários do app Oraculo."""

import json

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django import forms

from ..models import (
    Contato,
    AtendenteHumano,
    Atendimento,
    Mensagem,
    Treinamentos,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)


class ContatoForm(ModelForm):
    """Formulário para modelo Contato."""

    class Meta:
        model = Contato
        fields = ["telefone", "nome_contato", "nome_perfil_whatsapp"]

    def clean_telefone(self) -> str:
        """Validação customizada para telefone."""
        telefone = self.cleaned_data.get("telefone")
        if telefone:
            # Remove caracteres não numéricos
            telefone_limpo = "".join(filter(str.isdigit, telefone))

            # Valida tamanho
            if len(telefone_limpo) < 10 or len(telefone_limpo) > 13:
                raise ValidationError("Telefone deve ter entre 10 e 13 dígitos.")

            # Retorna o telefone limpo - o modelo fará a normalização para
            # formato internacional
            return telefone_limpo
        return telefone


class AtendenteHumanoForm(ModelForm):
    """Formulário para modelo AtendenteHumano."""

    # Sobrescrevemos o campo JSON para aceitar texto simples no formulário
    # e realizar a conversão para lista no método de limpeza. Isso evita
    # exigir JSON válido do usuário de formulário e suporta CSV como
    # "Vendas, Suporte" ou um único valor como "Suporte".
    especialidades = forms.CharField(required=False)

    class Meta:
        model = AtendenteHumano
        fields = ["nome", "cargo", "email", "ativo", "especialidades"]

    def clean_especialidades(self) -> list[str]:
        """Normaliza o campo especialidades para lista de strings.

        Aceita:
        - String CSV: "Vendas, Suporte" -> ["Vendas", "Suporte"]
        - String única: "Suporte" -> ["Suporte"]
        - JSON válido (lista): "[\"Vendas\", \"Suporte\"]"
        - Valor vazio: retorna lista vazia
        """
        value = self.cleaned_data.get("especialidades")
        if not value:
            return []

        # Se já for uma lista, retorna diretamente
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]

        # Se for string, tenta interpretar como JSON primeiro
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [
                        str(v).strip() for v in parsed if isinstance(v, (str, int))
                    ]
            except Exception:
                # Não é JSON, segue para CSV
                pass

            # Trata como CSV
            return [s.strip() for s in value.split(",") if s.strip()]

        # Qualquer outro tipo: normaliza para lista vazia
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


class AtendimentoForm(ModelForm):
    """Formulário para modelo Atendimento."""

    class Meta:
        model = Atendimento
        fields = ["contato", "atendente_humano", "status", "assunto", "prioridade"]

    def clean(self) -> dict:
        """Validação geral do formulário."""
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        atendente_humano = cleaned_data.get("atendente_humano")

        # Se status é TRANSFERIDO, deve ter atendente humano
        if status == StatusAtendimento.TRANSFERIDO and not atendente_humano:
            raise ValidationError(
                "Atendimento transferido requer um atendente designado."
            )

        # Se tem atendente humano, deve estar ativo
        if atendente_humano and not atendente_humano.ativo:
            raise ValidationError("Atendente selecionado não está ativo.")

        return cleaned_data


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


class TreinamentosForm(ModelForm):
    """Formulário para modelo Treinamentos."""

    class Meta:
        model = Treinamentos
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


class TestContatoForm(TestCase):
    """Testes para ContatoForm."""

    def test_form_valido(self) -> None:
        """Testa formulário válido."""
        form_data = {
            "telefone": "11999999999",
            "nome_contato": "Cliente Teste",
            "nome_perfil_whatsapp": "Cliente WhatsApp",
        }
        form = ContatoForm(data=form_data)

        self.assertTrue(form.is_valid())
        contato = form.save()
        self.assertEqual(contato.telefone, "5511999999999")
        self.assertEqual(contato.nome_contato, "Cliente Teste")

    def test_telefone_com_formatacao(self) -> None:
        """Testa limpeza de telefone com formatação."""
        form_data = {"telefone": "(11) 99999-9999", "nome_contato": "Cliente Teste"}
        form = ContatoForm(data=form_data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["telefone"], "11999999999")

    def test_telefone_muito_curto(self) -> None:
        """Testa validação de telefone muito curto."""
        form_data = {"telefone": "119999", "nome_contato": "Cliente Teste"}
        form = ContatoForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("telefone", form.errors)

    def test_telefone_muito_longo(self) -> None:
        """Testa validação de telefone muito longo."""
        form_data = {"telefone": "551199999999999", "nome_contato": "Cliente Teste"}
        form = ContatoForm(data=form_data)

        self.assertFalse(form.is_valid())
        self.assertIn("telefone", form.errors)

    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = ContatoForm(data={})

        self.assertFalse(form.is_valid())
        # Telefone é obrigatório
        self.assertIn("telefone", form.errors)

    def test_campos_opcionais(self) -> None:
        """Testa que nome_contato e nome_perfil_whatsapp são opcionais."""
        form_data = {
            "telefone": "11999999999",
            # nome_contato e nome_perfil_whatsapp omitidos
        }
        form = ContatoForm(data=form_data)

        self.assertTrue(form.is_valid())


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
            "email": "existente@teste.com",  # Email já existe
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
            "email": "existente@teste.com",  # Mesmo email do atendente
            "ativo": True,
        }
        form = AtendenteHumanoForm(data=form_data, instance=self.atendente_existente)

        self.assertTrue(form.is_valid())

    def test_campos_obrigatorios(self) -> None:
        """Testa validação de campos obrigatórios."""
        form = AtendenteHumanoForm(data={})

        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        self.assertIn("cargo", form.errors)


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
            # atendente_humano omitido
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


class TreinamentosForm(ModelForm):
    """Formulário para modelo Treinamentos."""

    class Meta:
        model = Treinamentos
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
            "conteudo": "   ",  # Apenas espaços
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
            "tag": "ab",  # Menos de 3 caracteres
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
            "grupo": "ab",  # Menos de 3 caracteres
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
            # treinamento_finalizado omitido
        }
        form = TreinamentosForm(data=form_data)

        self.assertTrue(form.is_valid())


class TestFormsIntegration(TestCase):
    """Testes de integração para formulários."""

    def test_fluxo_completo_atendimento(self) -> None:
        """Testa fluxo completo de criação via formulários."""
        # 1. Cria contato
        contato_form = ContatoForm(
            data={
                "telefone": "(11) 99999-9999",
                "nome_contato": "Cliente Integração",
                "email": "integracao@teste.com",
            }
        )
        self.assertTrue(contato_form.is_valid())
        contato = contato_form.save()

        # 2. Cria atendente
        atendente_form = AtendenteHumanoForm(
            data={
                "nome": "Atendente Integração",
                "cargo": "Suporte",
                "email": "atendente.integracao@teste.com",
                "ativo": True,
                "especialidades": "Suporte Técnico",
            }
        )
        self.assertTrue(atendente_form.is_valid())
        atendente = atendente_form.save()

        # 3. Cria atendimento
        atendimento_form = AtendimentoForm(
            data={
                "contato": contato.id,
                "atendente_humano": atendente.id,
                "status": StatusAtendimento.TRANSFERIDO,
                "assunto": "Atendimento de integração",
                "prioridade": "normal",
            }
        )
        self.assertTrue(atendimento_form.is_valid())
        atendimento = atendimento_form.save()

        # 4. Cria mensagem
        mensagem_form = MensagemForm(
            data={
                "atendimento": atendimento.id,
                "conteudo": "Primeira mensagem do atendimento",
                "tipo": TipoMensagem.TEXTO_FORMATADO,
                "remetente": TipoRemetente.CONTATO,
            }
        )
        self.assertTrue(mensagem_form.is_valid())
        mensagem = mensagem_form.save()

        # 5. Verifica relacionamentos
        self.assertEqual(mensagem.atendimento, atendimento)
        self.assertEqual(atendimento.contato, contato)
        self.assertEqual(atendimento.atendente_humano, atendente)

    def test_validacao_cruzada_formularios(self) -> None:
        """Testa validações que dependem de múltiplos formulários."""
        # Cria contato
        contato = Contato.objects.create(
            telefone="11888888888", nome_contato="Cliente Validação"
        )

        # Tenta criar atendimento humano sem atendente ativo
        atendente_inativo = AtendenteHumano.objects.create(
            nome="Atendente Inativo", email="inativo@teste.com", ativo=False
        )

        atendimento_form = AtendimentoForm(
            data={
                "contato": contato.id,
                "atendente_humano": atendente_inativo.id,
                "status": StatusAtendimento.TRANSFERIDO,
            }
        )

        # Deve falhar na validação
        self.assertFalse(atendimento_form.is_valid())
        self.assertIn("__all__", atendimento_form.errors)


class TestFormsPerformance(TestCase):
    """Testes de performance para formulários."""

    def test_validacao_multiplos_formularios(self) -> None:
        """Testa performance de validação de múltiplos formulários."""
        # Cria múltiplos contatos e atendentes e valida formulários em massa
        for i in range(50):
            contato_form = ContatoForm(
                data={
                    "telefone": f"(11) 9{i:08d}",
                    "nome_contato": f"Cliente {i}",
                }
            )
            self.assertTrue(contato_form.is_valid())

            atendente_form = AtendenteHumanoForm(
                data={
                    "nome": f"Atendente {i}",
                    "cargo": "Suporte",
                    "email": f"atendente{i}@teste.com",
                    "ativo": True,
                    "especialidades": "Suporte",
                }
            )
            self.assertTrue(atendente_form.is_valid())
