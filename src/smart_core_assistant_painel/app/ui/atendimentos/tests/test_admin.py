"""Testes para a interface administrativa do app Atendimentos."""

from typing import Optional

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase

from smart_core_assistant_painel.app.ui.atendimentos.admin import (
    AtendimentoAdmin,
    MensagemAdmin,
)
from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
    TipoEtapa,
)


class MockRequest:
    """Mock request para testes do admin."""

    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user or User()


class TestAtendimentoAdmin(TestCase):
    """Testes para o admin do modelo Atendimento."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = AtendimentoAdmin(Atendimento, self.site)

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.EM_ATENDIMENTO
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "id",
            "contato_telefone",
            "status",
            "data_inicio",
            "data_fim",
            "atendente_humano_nome",
            "avaliacao",
            "total_mensagens",
            "duracao_formatada",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = [
            "status",
            "prioridade",
            "data_inicio",
            "avaliacao",
            "atendente_humano",
        ]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = [
            "contato__telefone",
            "contato__nome_contato",
            "assunto",
            "atendente_humano__nome",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_duracao_formatada_method(self) -> None:
        """Testa o método duracao_formatada."""
        duracao = self.admin.duracao_formatada(self.atendimento)
        self.assertEqual(duracao, "Em andamento")

        import datetime

        self.atendimento.data_fim = (
            self.atendimento.data_inicio
            + datetime.timedelta(hours=1, minutes=30)
        )
        self.atendimento.save()

        duracao = self.admin.duracao_formatada(self.atendimento)
        self.assertIn("1:30", duracao)

    def test_filtra_etapa_atual_por_departamento_novo(self) -> None:
        """Form de criação deve filtrar etapas pelo departamento selecionado."""
        dep_a = Departamento.objects.create(nome="Suporte")
        dep_b = Departamento.objects.create(nome="Comercial")

        fluxo_a: FluxoAtendimento = dep_a.ensure_fluxo("Fluxo A")
        fluxo_b: FluxoAtendimento = dep_b.ensure_fluxo("Fluxo B")

        # Cria etapas específicas para garantir distinção
        etapa_a = EtapaFluxo.objects.create(
            fluxo=fluxo_a,
            nome="Etapa A",
            descricao="Teste A",
            ordem=10,
            cor="#123456",
            tipo_etapa=TipoEtapa.TRABALHO,
        )
        etapa_b = EtapaFluxo.objects.create(
            fluxo=fluxo_b,
            nome="Etapa B",
            descricao="Teste B",
            ordem=10,
            cor="#654321",
            tipo_etapa=TipoEtapa.TRABALHO,
        )

        request = MockRequest()
        # Simula seleção do departamento via GET
        request.GET = {"departamento": str(dep_a.id)}

        form_cls = self.admin.get_form(request)
        qs = form_cls.base_fields["etapa_atual"].queryset

        # Todas as etapas devem pertencer ao dep_a
        self.assertEqual(
            qs.filter(fluxo__departamento=dep_a).count(), qs.count()
        )
        # Etapa de outro departamento não deve aparecer
        self.assertFalse(qs.filter(id=etapa_b.id).exists())

    def test_filtra_etapa_atual_por_departamento_edicao(self) -> None:
        """Form de edição deve filtrar etapas pelo departamento do objeto."""
        dep = Departamento.objects.create(nome="Financeiro")
        fluxo: FluxoAtendimento = dep.ensure_fluxo("Fluxo Fin")
        etapa = EtapaFluxo.objects.create(
            fluxo=fluxo,
            nome="Etapa Fin",
            descricao="Teste",
            ordem=5,
            cor="#ABCDEF",
            tipo_etapa=TipoEtapa.TRABALHO,
        )

        atendimento = Atendimento.objects.create(
            contato=self.contato,
            status=StatusAtendimento.EM_ATENDIMENTO,
            departamento=dep,
        )

        request = MockRequest()
        form_cls = self.admin.get_form(request, obj=atendimento)
        qs = form_cls.base_fields["etapa_atual"].queryset

        # Deve conter a etapa do próprio departamento
        self.assertTrue(qs.filter(id=etapa.id).exists())


class TestMensagemAdmin(TestCase):
    """Testes para o admin do modelo Mensagem."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = MensagemAdmin(Mensagem, self.site)

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.EM_ANDAMENTO
        )

        self.mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Mensagem de teste muito longa para verificar o truncamento",
            message_id_whatsapp="TEST123",
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "atendimento",
            "remetente",
            "tipo",
            "conteudo_truncado",
            "timestamp",
            "message_id_whatsapp",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = ["remetente", "tipo", "timestamp"]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = [
            "conteudo",
            "message_id_whatsapp",
            "atendimento__contato__nome_contato",
            "atendimento__contato__telefone",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_conteudo_truncado_method(self) -> None:
        """Testa o método conteudo_truncado."""
        conteudo_truncado = self.admin.conteudo_truncado(self.mensagem)
        self.assertTrue(len(conteudo_truncado) <= 50)
        self.assertIn("Mensagem de teste", conteudo_truncado)

        mensagem_curta = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.BOT,
            conteudo="Curta",
            message_id_whatsapp="SHORT123",
        )

        conteudo_curto = self.admin.conteudo_truncado(mensagem_curta)
        self.assertEqual(conteudo_curto, "Curta")
