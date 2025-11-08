"""Testes isolados para as validações do modelo WhatsAppInstance."""

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from smart_core_assistant_painel.app.ui.operacional.models import (
    AtendenteHumano,
    Departamento,
    WhatsAppInstance,
    FluxoAtendimento,
)


class WhatsAppInstanceValidationTestCase(TestCase):
    """Testes isolados para validações do modelo WhatsAppInstance."""

    def setUp(self) -> None:
        """Configura dados iniciais para os testes."""
        # Criar departamento sem disparar signals
        self.departamento = Departamento(
            nome="Vendas",
            slug="vendas",
            descricao="Departamento de vendas",
        )
        self.departamento.save_base()

        self.fluxo = FluxoAtendimento(
            nome="Fluxo Vendas",
            descricao="Fluxo principal",
            departamento=self.departamento,
        )
        self.fluxo.save_base()

        # Criar atendente sem disparar signals
        self.atendente = AtendenteHumano(
            nome="João Silva",
            cargo="Vendedor",
            telefone="+5511999998888",
            email="joao@empresa.com",
            departamento=self.departamento,
            fluxo=self.fluxo,
        )
        self.atendente.save_base()

    def test_validacao_departamento_e_owner_preenchidos_erro(self) -> None:
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

    def test_validacao_nenhum_responsavel_preenchido_erro(self) -> None:
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

    def test_validacao_instancia_departamental_ok(self) -> None:
        """Testa validação com departamento preenchido e owner vazio."""
        instancia = WhatsAppInstance(
            departamento=self.departamento,
            phone_number="+5511999997777",
            api_key="test_api_key_dept",
        )

        # Não deve lançar exceção
        instancia.clean()
        assert instancia.tipo_instancia == "departamental"
        assert instancia.responsavel_principal == self.departamento

    def test_validacao_instancia_individual_ok(self) -> None:
        """Testa validação com owner preenchido e departamento vazio."""
        instancia = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999996666",
            api_key="test_api_key_user",
        )

        # Não deve lançar exceção
        instancia.clean()
        assert instancia.tipo_instancia == "individual"
        assert instancia.responsavel_principal == self.atendente

    def test_propriedade_tipo_instancia_departamental(self) -> None:
        """Testa propriedade tipo_instancia para instância departamental."""
        instancia = WhatsAppInstance(
            departamento=self.departamento,
            phone_number="+5511999997777",
            api_key="test_api_key_dept",
        )
        assert instancia.tipo_instancia == "departamental"

    def test_propriedade_tipo_instancia_individual(self) -> None:
        """Testa propriedade tipo_instancia para instância individual."""
        instancia = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999996666",
            api_key="test_api_key_user",
        )
        assert instancia.tipo_instancia == "individual"

    def test_propriedade_tipo_instancia_desconhecido(self) -> None:
        """Testa propriedade tipo_instancia quando não há responsável."""
        instancia = WhatsAppInstance(
            phone_number="+5511999995555",
            api_key="test_api_key_none",
        )
        assert instancia.tipo_instancia == "desconhecido"

    def test_propriedade_responsavel_principal_departamento(self) -> None:
        """Testa propriedade responsavel_principal para instância departamental."""
        instancia = WhatsAppInstance(
            departamento=self.departamento,
            phone_number="+5511999997777",
            api_key="test_api_key_dept",
        )
        assert instancia.responsavel_principal == self.departamento

    def test_propriedade_responsavel_principal_atendente(self) -> None:
        """Testa propriedade responsavel_principal para instância individual."""
        instancia = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999996666",
            api_key="test_api_key_user",
        )
        assert instancia.responsavel_principal == self.atendente

    def test_propriedade_responsavel_principal_nulo(self) -> None:
        """Testa propriedade responsavel_principal quando não há responsável."""
        instancia = WhatsAppInstance(
            phone_number="+5511999995555",
            api_key="test_api_key_none",
        )
        assert instancia.responsavel_principal is None

    def test_roteamento_instancia_individual_disponivel(self) -> None:
        """Testa roteamento para instância individual com atendente disponível."""
        instancia = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999993333",
            api_key="test_api_key_routing",
        )

        # Garantir que atendente está disponível
        self.atendente.disponivel = True
        self.atendente.save_base()

        mensagem = {"from": "+5511888887777", "body": "Test message"}
        atendente_selecionado = instancia.rotear_atendimento(mensagem)

        assert atendente_selecionado == self.atendente

    def test_roteamento_instancia_individual_indisponivel(self) -> None:
        """Testa roteamento para instância individual com atendente indisponível."""
        instancia = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999992222",
            api_key="test_api_key_unavail",
        )

        # Marcar atendente como indisponível
        self.atendente.disponivel = False
        self.atendente.save_base()

        mensagem = {"from": "+5511888886666", "body": "Test message"}
        atendente_selecionado = instancia.rotear_atendimento(mensagem)

        assert atendente_selecionado is None

    def test_roteamento_instancia_desconhecida(self) -> None:
        """Testa roteamento para instância sem tipo definido."""
        instancia = WhatsAppInstance(
            phone_number="+5511999991111",
            api_key="test_api_key_unknown",
        )

        mensagem = {"from": "+5511888885555", "body": "Test message"}
        atendente_selecionado = instancia.rotear_atendimento(mensagem)

        assert atendente_selecionado is None

    def test_string_representation_com_instance_id(self) -> None:
        """Testa representação em string com instance_id."""
        instancia = WhatsAppInstance(
            departamento=self.departamento,
            phone_number="+5511999996666",
            instance_id="test_instance",
            api_key="test_api_key_str",
        )
        assert "Vendas - test_instance" in str(instancia)

    def test_string_representation_sem_instance_id(self) -> None:
        """Testa representação em string sem instance_id."""
        instancia = WhatsAppInstance(
            owner=self.atendente,
            phone_number="+5511999995555",
            api_key="test_api_key_str2",
        )
        assert "sem-departamento - +5511999995555" in str(instancia)
