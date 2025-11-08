"""Testes unitários completamente isolados para o modelo WhatsAppInstance."""

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.db.models.signals import post_save


@override_settings(SIGNALS_DISABLED=True)
class WhatsAppInstanceUnitTestCase(TestCase):
    """Testes unitários isolados para validações do WhatsAppInstance sem signals."""

    def setUp(self) -> None:
        """Configura objetos básicos para testes sem signals."""
        # Desabilitar temporariamente todos os signals
        self.signals_backup = {}
        for signal in [post_save]:
            self.signals_backup[signal] = signal.receivers
            signal.receivers = []

        # Criar objetos diretamente no banco sem signals
        from smart_core_assistant_painel.app.ui.operacional.models import (
            Departamento,
            AtendenteHumano,
            WhatsAppInstance,
            FluxoAtendimento,
        )

        self.Departamento = Departamento
        self.AtendenteHumano = AtendenteHumano
        self.WhatsAppInstance = WhatsAppInstance

    def tearDown(self) -> None:
        """Restaurar signals após os testes."""
        # Restaurar signals
        for signal, receivers in self.signals_backup.items():
            signal.receivers = receivers

    def test_validacao_ambos_preenchidos_erro(self) -> None:
        """Testa erro quando departamento e owner estão preenchidos."""
        dept = self.Departamento(
            nome="Vendas",
            slug="vendas",
            descricao="Departamento de vendas",
        )
        dept.save_base()

        fluxo = FluxoAtendimento(
            nome="Fluxo Vendas",
            descricao="Fluxo principal",
            departamento=dept,
        )
        fluxo.save_base()

        atendente = self.AtendenteHumano(
            nome="João Silva",
            cargo="Vendedor",
            telefone="+5511999998888",
            departamento=dept,
            fluxo=fluxo,
        )
        atendente.save_base()

        instancia = self.WhatsAppInstance(
            departamento=dept,
            owner=atendente,
            phone_number="+5511999995555",
            api_key="test_api_key_both",
        )

        with pytest.raises(ValidationError) as exc_info:
            instancia.clean()

        assert (
            "Uma instância deve estar vinculada a UM departamento OU UM atendente, nunca ambos."
            in str(exc_info.value)
        )

    def test_validacao_nenhum_preenchido_erro(self) -> None:
        """Testa erro quando nenhum responsável está preenchido."""
        instancia = self.WhatsAppInstance(
            phone_number="+5511999994444",
            api_key="test_api_key_none",
        )

        with pytest.raises(ValidationError) as exc_info:
            instancia.clean()

        assert (
            "Uma instância deve estar vinculada a pelo menos UM departamento ou UM atendente."
            in str(exc_info.value)
        )

    def test_instancia_departamental_ok(self) -> None:
        """Testa criação bem-sucedida de instância departamental."""
        dept = self.Departamento(
            nome="Vendas",
            slug="vendas",
            descricao="Departamento de vendas",
        )
        dept.save_base()

        fluxo = FluxoAtendimento(
            nome="Fluxo Vendas",
            descricao="Fluxo principal",
            departamento=dept,
        )
        fluxo.save_base()

        instancia = self.WhatsAppInstance(
            departamento=dept,
            phone_number="+5511999997777",
            api_key="test_api_key_dept",
        )

        # Não deve lançar exceção
        instancia.clean()
        assert instancia.tipo_instancia == "departamental"
        assert instancia.responsavel_principal == dept

    def test_instancia_individual_ok(self) -> None:
        """Testa criação bem-sucedida de instância individual."""
        dept = self.Departamento(
            nome="Vendas",
            slug="vendas",
            descricao="Departamento de vendas",
        )
        dept.save_base()

        atendente = self.AtendenteHumano(
            nome="João Silva",
            cargo="Vendedor",
            telefone="+5511999998888",
            departamento=dept,
            fluxo=fluxo,
        )
        atendente.save_base()

        instancia = self.WhatsAppInstance(
            owner=atendente,
            phone_number="+5511999996666",
            api_key="test_api_key_user",
        )

        # Não deve lançar exceção
        instancia.clean()
        assert instancia.tipo_instancia == "individual"
        assert instancia.responsavel_principal == atendente

    def test_propriedades_helper_sem_objetos(self) -> None:
        """Testa propriedades helper quando não há objetos vinculados."""
        instancia = self.WhatsAppInstance(
            phone_number="+5511999995555",
            api_key="test_api_key_none",
        )

        assert instancia.tipo_instancia == "desconhecido"
        assert instancia.responsavel_principal is None

    def test_roteamento_individual_disponivel(self) -> None:
        """Testa roteamento para instância individual com atendente disponível."""
        dept = self.Departamento(
            nome="Vendas",
            slug="vendas",
            descricao="Departamento de vendas",
        )
        dept.save_base()

        fluxo = FluxoAtendimento(
            nome="Fluxo Vendas",
            descricao="Fluxo principal",
            departamento=dept,
        )
        fluxo.save_base()

        atendente = self.AtendenteHumano(
            nome="João Silva",
            cargo="Vendedor",
            telefone="+5511999998888",
            departamento=dept,
            fluxo=fluxo,
            disponivel=True,
        )
        atendente.save_base()

        instancia = self.WhatsAppInstance(
            owner=atendente,
            phone_number="+5511999993333",
            api_key="test_api_key_routing",
        )

        mensagem = {"from": "+5511888887777", "body": "Test message"}
        resultado = instancia.rotear_atendimento(mensagem)
        assert resultado == atendente

    def test_roteamento_individual_indisponivel(self) -> None:
        """Testa roteamento para instância individual com atendente indisponível."""
        dept = self.Departamento(
            nome="Vendas",
            slug="vendas",
            descricao="Departamento de vendas",
        )
        dept.save_base()

        fluxo = FluxoAtendimento(
            nome="Fluxo Vendas",
            descricao="Fluxo principal",
            departamento=dept,
        )
        fluxo.save_base()

        atendente = self.AtendenteHumano(
            nome="João Silva",
            cargo="Vendedor",
            telefone="+5511999998888",
            departamento=dept,
            fluxo=fluxo,
            disponivel=False,
        )
        atendente.save_base()

        instancia = self.WhatsAppInstance(
            owner=atendente,
            phone_number="+5511999992222",
            api_key="test_api_key_unavail",
        )

        mensagem = {"from": "+5511888886666", "body": "Test message"}
        resultado = instancia.rotear_atendimento(mensagem)
        assert resultado is None

    def test_roteamento_desconhecido(self) -> None:
        """Testa roteamento quando tipo da instância é desconhecido."""
        instancia = self.WhatsAppInstance(
            phone_number="+5511999991111",
            api_key="test_api_key_unknown",
        )

        mensagem = {"from": "+5511888885555", "body": "Test message"}
        resultado = instancia.rotear_atendimento(mensagem)
        assert resultado is None

    def test_string_representation_completa(self) -> None:
        """Testa representação em string em diferentes cenários."""
        dept = self.Departamento(
            nome="Vendas",
            slug="vendas",
            descricao="Departamento de vendas",
        )
        dept.save_base()

        fluxo = FluxoAtendimento(
            nome="Fluxo Vendas",
            descricao="Fluxo principal",
            departamento=dept,
        )
        fluxo.save_base()

        atendente = self.AtendenteHumano(
            nome="João Silva",
            cargo="Vendedor",
            telefone="+5511999998888",
            departamento=dept,
            fluxo=fluxo,
        )
        atendente.save_base()

        # Com instance_id
        instancia1 = self.WhatsAppInstance(
            departamento=dept,
            phone_number="+5511999996666",
            instance_id="test_instance",
            api_key="test_api_key_str",
        )
        assert "Vendas - test_instance" in str(instancia1)

        # Sem instance_id
        instancia2 = self.WhatsAppInstance(
            owner=atendente,
            phone_number="+5511999995555",
            api_key="test_api_key_str2",
        )
        assert "sem-departamento - +5511999995555" in str(instancia2)
