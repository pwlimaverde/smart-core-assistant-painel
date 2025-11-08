"""Testes para os modelos do app Atendimentos."""

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

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


class TestAtendimento(TestCase):
    """Testes para o modelo Atendimento."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.EM_ANDAMENTO
        )

    def test_atendimento_creation(self) -> None:
        """Testa a criação de um atendimento."""
        self.assertEqual(self.atendimento.contato, self.contato)
        self.assertEqual(
            self.atendimento.status, StatusAtendimento.EM_ANDAMENTO
        )
        self.assertIsNotNone(self.atendimento.data_inicio)
        self.assertIsNone(self.atendimento.data_fim)

    def test_atendimento_finalizacao(self) -> None:
        """Testa a finalização de um atendimento."""
        self.atendimento.status = StatusAtendimento.RESOLVIDO
        self.atendimento.data_fim = timezone.now()
        self.atendimento.save()

        self.assertEqual(self.atendimento.status, StatusAtendimento.RESOLVIDO)
        self.assertIsNotNone(self.atendimento.data_fim)

    def test_clean_valida_etapa_do_departamento(self) -> None:
        """Valida que a etapa pertence ao departamento do atendimento."""
        dep_a: Departamento = Departamento.objects.create(nome="Suporte")
        dep_b: Departamento = Departamento.objects.create(nome="Comercial")

        fluxo_a: FluxoAtendimento = dep_a.ensure_fluxo("Fluxo A")
        fluxo_b: FluxoAtendimento = dep_b.ensure_fluxo("Fluxo B")

        etapa_a: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo_a,
            nome="Etapa A",
            descricao="Teste A",
            ordem=10,
            cor="#123456",
            tipo_etapa=TipoEtapa.TRABALHO,
        )
        etapa_b: EtapaFluxo = EtapaFluxo.objects.create(
            fluxo=fluxo_b,
            nome="Etapa B",
            descricao="Teste B",
            ordem=10,
            cor="#654321",
            tipo_etapa=TipoEtapa.TRABALHO,
        )

        atendimento = Atendimento(
            contato=self.contato,
            status=StatusAtendimento.EM_ANDAMENTO,
            departamento=dep_a,
            etapa_atual=etapa_b,
        )

        with self.assertRaises(ValidationError):
            atendimento.clean()

        # Agora com etapa do mesmo departamento não deve lançar
        atendimento.etapa_atual = etapa_a
        atendimento.clean()


class TestMensagem(TestCase):
    """Testes para o modelo Mensagem."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.EM_ANDAMENTO
        )

    def test_mensagem_creation(self) -> None:
        """Testa a criação de uma mensagem."""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Mensagem de teste",
            message_id_whatsapp="TEST123",
        )

        self.assertEqual(mensagem.atendimento, self.atendimento)
        self.assertEqual(mensagem.tipo, TipoMensagem.TEXTO_FORMATADO)
        self.assertEqual(mensagem.remetente, TipoRemetente.CONTATO)
        self.assertEqual(mensagem.conteudo, "Mensagem de teste")
        self.assertEqual(mensagem.message_id_whatsapp, "TEST123")
        self.assertIsNotNone(mensagem.timestamp)

    def test_mensagem_bot(self) -> None:
        """Testa a criação de uma mensagem do bot."""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.BOT,
            conteudo="Resposta do bot",
        )

        self.assertEqual(mensagem.remetente, TipoRemetente.BOT)
        self.assertEqual(mensagem.conteudo, "Resposta do bot")
