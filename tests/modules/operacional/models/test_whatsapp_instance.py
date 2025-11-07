"""Testes para o modelo WhatsAppInstance e suas validações."""

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest.mock import patch

from smart_core_assistant_painel.app.ui.operacional.models import (
    AtendenteHumano,
    Departamento,
    WhatsAppInstance,
    FluxoAtendimento,
)


class WhatsAppInstanceTestCase(TestCase):
    """Testes para o modelo WhatsAppInstance."""

    def setUp(self) -> None:
        """Configura dados iniciais para os testes."""
        # Desabilitar signals que podem interferir nos testes
        with patch('smart_core_assistant_painel.app.ui.operacional.models.post_save'):
            self.departamento = Departamento.objects.create(
                nome="Vendas",
                slug="vendas",
                descricao="Departamento de vendas",
            )

            self.fluxo = FluxoAtendimento.objects.create(
                nome="Fluxo Vendas",
                descricao="Fluxo principal do departamento de vendas",
                departamento=self.departamento,
            )

            self.atendente = AtendenteHumano.objects.create(
                nome="João Silva",
                cargo="Vendedor",
                telefone="+5511999998888",
                email="joao@empresa.com",
                departamento=self.departamento,
                fluxo=self.fluxo,
            )

    def test_criar_instancia_departamental(self) -> None:
        """Testa criar uma instância vinculada a departamento."""
        instancia = WhatsAppInstance.objects.create(
            departamento=self.departamento,
            phone_number="+5511999997777",
            instance_id="vendas_main",
            api_key="test_api_key_dept",
            provider="evolution",
        )

        assert instancia.tipo_instancia == "departamental"
        assert instancia.responsavel_principal == self.departamento
        assert instancia.owner is None

    def test_criar_instancia_individual(self) -> None:
        """Testa criar uma instância vinculada a atendente."""
        instancia = WhatsAppInstance.objects.create(
            owner=self.atendente,
            phone_number="+5511999996666",
            instance_id="joao_personal",
            api_key="test_api_key_user",
            provider="evolution",
        )

        assert instancia.tipo_instancia == "individual"
        assert instancia.responsavel_principal == self.atendente
        assert instancia.departamento is None

    def test_validacao_departamento_e_owner_preenchidos(self) -> None:
        """Testa validação quando ambos departamento e owner estão preenchidos."""
        instancia = WhatsAppInstance(
            departamento=self.departamento,
            owner=self.atendente,
            phone_number="+5511999995555",
            api_key="test_api_key_both",
        )

        with pytest.raises(ValidationError) as exc_info:
            instancia.clean()

        assert (
            "Uma instância deve estar vinculada a UM departamento OU UM atendente, nunca ambos."
            in str(exc_info.value)
        )

    def test_validacao_nenhum_responsavel_preenchido(self) -> None:
        """Testa validação quando nenhum responsável está preenchido."""
        instancia = WhatsAppInstance(
            phone_number="+5511999994444",
            api_key="test_api_key_none",
        )

        with pytest.raises(ValidationError) as exc_info:
            instancia.clean()

        assert (
            "Uma instância deve estar vinculada a pelo menos UM departamento ou UM atendente."
            in str(exc_info.value)
        )

    def test_roteamento_instancia_individual(self) -> None:
        """Testa roteamento de atendimento para instância individual."""
        instancia = WhatsAppInstance.objects.create(
            owner=self.atendente,
            phone_number="+5511999993333",
            instance_id="joao_routing",
            api_key="test_api_key_routing",
            provider="evolution",
        )

        mensagem = {"from": "+5511888887777", "body": "Test message"}
        atendente_selecionado = instancia.rotear_atendimento(mensagem)

        assert atendente_selecionado == self.atendente

    def test_roteamento_instancia_individual_indisponivel(self) -> None:
        """Testa roteamento quando atendente individual está indisponível."""
        self.atendente.disponivel = False
        self.atendente.save()

        instancia = WhatsAppInstance.objects.create(
            owner=self.atendente,
            phone_number="+5511999992222",
            instance_id="joao_unavailable",
            api_key="test_api_key_unavail",
            provider="evolution",
        )

        mensagem = {"from": "+5511888886666", "body": "Test message"}
        atendente_selecionado = instancia.rotear_atendimento(mensagem)

        assert atendente_selecionado is None

    def test_roteamento_instancia_departamental(self) -> None:
        """Testa roteamento de atendimento para instância departamental."""
        # Criar múltiplos atendentes no departamento
        atendente2 = AtendenteHumano.objects.create(
            nome="Maria Santos",
            cargo="Vendedora",
            telefone="+5511999991111",
            departamento=self.departamento,
            fluxo=self.fluxo,
        )

        instancia = WhatsAppInstance.objects.create(
            departamento=self.departamento,
            phone_number="+5511999990000",
            instance_id="vendas_routing",
            api_key="test_api_key_dept_route",
            provider="evolution",
        )

        mensagem = {"from": "+5511888885555", "body": "Test message"}
        atendente_selecionado = instancia.rotear_atendimento(mensagem)

        # Deve selecionar um dos atendentes disponíveis (João ou Maria)
        assert atendente_selecionado in [self.atendente, atendente2]

    def test_metodos_helper_display(self) -> None:
        """Testa os métodos helper para exibição."""
        # Instância departamental
        instancia_dept = WhatsAppInstance(
            departamento=self.departamento,
            phone_number="+5511999998888",
            api_key="test_dept_display",
        )
        instancia_dept.clean()

        assert instancia_dept.tipo_instancia == "departamental"
        assert instancia_dept.responsavel_principal == self.departamento

        # Instância individual
        instancia_user = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999997777",
            api_key="test_user_display",
        )
        instancia_user.clean()

        assert instancia_user.tipo_instancia == "individual"
        assert instancia_user.responsavel_principal == self.atendente

    def test_string_representation(self) -> None:
        """Testa representação em string do modelo."""
        # Com instance_id
        instancia = WhatsAppInstance(
            departamento=self.departamento,
            phone_number="+5511999996666",
            instance_id="test_instance",
            api_key="test_api_key_str",
        )
        assert "Vendas - test_instance" in str(instancia)

        # Sem instance_id (usa phone_number)
        instancia2 = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999995555",
            api_key="test_api_key_str2",
        )
        assert "sem-departamento - +5511999995555" in str(instancia2)
