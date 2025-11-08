"""Testes para sinais do app Operacional.

Verifica criação automática de etapas ao criar um novo FluxoAtendimento.
"""

from typing import Optional

from django.test import TestCase

from smart_core_assistant_painel.app.ui.operacional.models import (
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
    TipoEtapa,
)


class FluxoSignalsTest(TestCase):
    def test_cria_quatro_etapas_padrao_em_novo_fluxo(self) -> None:
        """Cria fluxo e valida 4 etapas padrão com dados especificados."""

        # Cria departamento simples
        dep: Departamento = Departamento.objects.create(nome="Operacional")

        # Cria novo fluxo (dispara sinal post_save com created=True)
        fluxo: FluxoAtendimento = FluxoAtendimento.objects.create(
            departamento=dep,
            nome="Fluxo Operacional",
        )

        # Consulta etapas criadas
        etapas = FluxoAtendimento.objects.get(id=fluxo.id).etapas.all()
        self.assertEqual(etapas.count(), 4)

        # Valida a etapa inicial (ordem 0)
        etapa_inicial: Optional[EtapaFluxo] = fluxo.etapas.filter(
            ordem=0
        ).first()
        self.assertIsNotNone(etapa_inicial)
        assert etapa_inicial is not None
        self.assertEqual(etapa_inicial.nome, "Fila de Atendimento")
        self.assertEqual(etapa_inicial.tipo_etapa, TipoEtapa.FILA)
        self.assertEqual(etapa_inicial.cor, "#B0C4DE")

        # Valida etapa Resolvido (ordem 1000)
        etapa_resolvido: Optional[EtapaFluxo] = fluxo.etapas.filter(
            ordem=1000
        ).first()
        self.assertIsNotNone(etapa_resolvido)
        assert etapa_resolvido is not None
        self.assertEqual(etapa_resolvido.nome, "Resolvido")
        self.assertEqual(etapa_resolvido.tipo_etapa, TipoEtapa.FINALIZACAO)
        self.assertEqual(etapa_resolvido.cor, "#66CDAA")

        # Valida etapa Pendência (ordem 999)
        etapa_pendencia: Optional[EtapaFluxo] = fluxo.etapas.filter(
            ordem=999
        ).first()
        self.assertIsNotNone(etapa_pendencia)
        assert etapa_pendencia is not None
        self.assertEqual(etapa_pendencia.nome, "Pendência")
        self.assertEqual(etapa_pendencia.tipo_etapa, TipoEtapa.ESPERA)
        self.assertEqual(etapa_pendencia.cor, "#FFFACD")

        # Valida etapa Cancelado (ordem 1001)
        etapa_cancelado: Optional[EtapaFluxo] = fluxo.etapas.filter(
            ordem=1001
        ).first()
        self.assertIsNotNone(etapa_cancelado)
        assert etapa_cancelado is not None
        self.assertEqual(etapa_cancelado.nome, "Cancelado")
        self.assertEqual(etapa_cancelado.tipo_etapa, TipoEtapa.FINALIZACAO)
        self.assertEqual(etapa_cancelado.cor, "#FA8072")