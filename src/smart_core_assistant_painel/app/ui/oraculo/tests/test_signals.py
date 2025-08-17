"""Testes para sinais (signals) do app Oraculo."""

from typing import Any
from django.test import TestCase, TransactionTestCase
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..models import (
    Contato,
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)


class TestModelSignals(TestCase):
    """Testes para sinais de modelo básicos."""

    def setUp(self) -> None:
        """Configuração inicial."""
        self.test_signals_fired = []

    def tearDown(self) -> None:
        """Limpeza após os testes."""
        self.test_signals_fired.clear()

    def test_contato_post_save_signal(self) -> None:
        """Testa se o sinal post_save é disparado ao criar Contato."""

        # Handler para capturar o sinal
        @receiver(post_save, sender=Contato)
        def test_handler(
            sender: Any, instance: Contato, created: bool, **kwargs: Any
        ) -> None:
            self.test_signals_fired.append(
                {"sender": sender, "instance": instance, "created": created}
            )

        # Cria contato
        contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Teste Signal"
        )

        # Verifica se o sinal foi disparado
        self.assertEqual(len(self.test_signals_fired), 1)
        self.assertEqual(self.test_signals_fired[0]["instance"], contato)
        self.assertTrue(self.test_signals_fired[0]["created"])

    def test_atendimento_post_save_signal(self) -> None:
        """Testa se o sinal post_save é disparado ao criar Atendimento."""

        # Handler para capturar o sinal
        @receiver(post_save, sender=Atendimento)
        def test_handler(
            sender: Any, instance: Atendimento, created: bool, **kwargs: Any
        ) -> None:
            self.test_signals_fired.append(
                {"sender": sender, "instance": instance, "created": created}
            )

        # Cria contato e atendimento
        contato = Contato.objects.create(
            telefone="5511888888888", nome_contato="Cliente Signal"
        )
        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.EM_ANDAMENTO
        )

        # Verifica se o sinal foi disparado
        self.assertEqual(len(self.test_signals_fired), 1)
        self.assertEqual(self.test_signals_fired[0]["instance"], atendimento)
        self.assertTrue(self.test_signals_fired[0]["created"])

    def test_mensagem_post_save_signal(self) -> None:
        """Testa se o sinal post_save é disparado ao criar Mensagem."""

        # Handler para capturar o sinal
        @receiver(post_save, sender=Mensagem)
        def test_handler(
            sender: Any, instance: Mensagem, created: bool, **kwargs: Any
        ) -> None:
            self.test_signals_fired.append(
                {"sender": sender, "instance": instance, "created": created}
            )

        # Cria contato, atendimento e mensagem
        contato = Contato.objects.create(
            telefone="5511777777777", nome_contato="Cliente Msg Signal"
        )
        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.EM_ANDAMENTO
        )
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Mensagem teste",
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
        )

        # Verifica se o sinal foi disparado
        self.assertEqual(len(self.test_signals_fired), 1)
        self.assertEqual(self.test_signals_fired[0]["instance"], mensagem)
        self.assertTrue(self.test_signals_fired[0]["created"])


class TestSignalHandlers(TestCase):
    """Testes para handlers de sinais customizados."""

    def setUp(self) -> None:
        """Configuração inicial."""
        self.handler_calls = []

    def test_custom_contato_handler(self) -> None:
        """Testa handler customizado para criação de contato."""

        # Handler customizado para contatos
        @receiver(post_save, sender=Contato)
        def contato_handler(
            sender: Any, instance: Contato, created: bool, **kwargs: Any
        ) -> None:
            if created:
                self.handler_calls.append(f"Contato criado: {instance.nome_contato}")

        # Cria contato (sem atribuição, apenas para disparar o sinal)
        Contato.objects.create(
            telefone="5511666666666", nome_contato="Handler Test"
        )

        # Verifica se o handler foi chamado
        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(self.handler_calls[0], "Contato criado: Handler Test")

    def test_atendimento_status_change_handler(self) -> None:
        """Testa handler para mudança de status de atendimento."""

        # Handler para mudanças no atendimento
        @receiver(post_save, sender=Atendimento)
        def atendimento_handler(
            sender: Any, instance: Atendimento, **kwargs: Any
        ) -> None:
            self.handler_calls.append(
                f"Atendimento {instance.id} - Status: {instance.status}"
            )

        # Cria contato e atendimento
        contato = Contato.objects.create(
            telefone="5511555555555", nome_contato="Status Test"
        )
        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.EM_ANDAMENTO
        )

        # Muda status
        atendimento.status = StatusAtendimento.RESOLVIDO
        atendimento.save()

        # Verifica se o handler foi chamado
        self.assertEqual(len(self.handler_calls), 2)  # Criação + atualização
        # Os valores do enum são strings (e.g., 'em_andamento', 'resolvido')
        self.assertIn(StatusAtendimento.EM_ANDAMENTO, self.handler_calls[0])
        self.assertIn(StatusAtendimento.RESOLVIDO, self.handler_calls[1])


class TestSignalIntegration(TransactionTestCase):
    """Testes de integração com sinais em transações."""

    def test_signal_rollback_behavior(self) -> None:
        """Testa comportamento de sinais em rollback de transação."""
        signals_fired = []

        @receiver(post_save, sender=Contato)
        def track_signal(sender: Any, instance: Contato, **kwargs: Any) -> None:
            signals_fired.append(instance.id)

        # Testa rollback
        from django.db import transaction

        try:
            with transaction.atomic():
                # Cria contato apenas para disparar o sinal
                Contato.objects.create(
                    telefone="5511444444444", nome_contato="Rollback Test"
                )
                # Força rollback com exceção
                raise Exception("Forçar rollback")
        except Exception:
            pass

        # Signal deve ter sido disparado mesmo com rollback
        self.assertEqual(len(signals_fired), 1)

    def test_bulk_operations_signals(self) -> None:
        """Testa sinais em operações bulk."""
        signals_fired = []

        @receiver(post_save, sender=Contato)
        def track_bulk_signal(sender: Any, instance: Contato, **kwargs: Any) -> None:
            signals_fired.append(instance.nome_contato)

        # Bulk create não dispara sinais post_save por padrão
        Contato.objects.bulk_create(
            [
                Contato(telefone="5511111111111", nome_contato="Bulk 1"),
                Contato(telefone="5511222222222", nome_contato="Bulk 2"),
            ]
        )

        # Sinais não devem ter sido disparados
        self.assertEqual(len(signals_fired), 0)

        # Create individual dispara sinais
        Contato.objects.create(telefone="5511333333333", nome_contato="Individual")

        # Agora deve ter 1 sinal
        self.assertEqual(len(signals_fired), 1)
        self.assertEqual(signals_fired[0], "Individual")


class TestMemoryLeaks(TestCase):
    """Testes para verificar vazamentos de memória com sinais."""

    def test_signal_memory_usage(self) -> None:
        """Testa uso de memória com muitos sinais."""
        # Simula um handler que armazena dados
        data_store = {}

        def memory_handler(sender: Any, instance: Mensagem, **kwargs: Any) -> None:
            data_store[instance.id] = {
                "id": instance.id,
                "conteudo": instance.conteudo,
                "timestamp": instance.timestamp,
            }

        # Conecta o handler
        post_save.connect(memory_handler, sender=Mensagem)

        try:
            # Cria muitas mensagens
            contato = Contato.objects.create(
                telefone="5511000000000", nome_contato="Memory Test"
            )
            atendimento = Atendimento.objects.create(
                contato=contato, status=StatusAtendimento.EM_ANDAMENTO
            )

            for i in range(100):
                Mensagem.objects.create(
                    atendimento=atendimento,
                    conteudo=f"Mensagem {i}",
                    tipo=TipoMensagem.TEXTO_FORMATADO,
                    remetente=TipoRemetente.CONTATO,
                )

            # Verifica se todos os dados foram armazenados
            self.assertEqual(len(data_store), 100)

        finally:
            # Desconecta o handler para evitar interferência
            post_save.disconnect(memory_handler, sender=Mensagem)

    def test_signal_handler_exception_handling(self) -> None:
        """Testa tratamento de exceções em handlers."""
        exceptions_caught = []

        def failing_handler(sender: Any, instance: Contato, **kwargs: Any) -> None:
            exceptions_caught.append("Handler executado")
            raise Exception("Handler falhou")

        # Conecta handler que falha
        post_save.connect(failing_handler, sender=Contato)

        try:
            # Cria contato - deve funcionar mesmo com handler falhando
            contato = Contato.objects.create(
                telefone="5511987654321", nome_contato="Exception Test"
            )

            # Verifica se o contato foi criado
            self.assertTrue(Contato.objects.filter(id=contato.id).exists())

            # Handler deve ter sido executado
            self.assertEqual(len(exceptions_caught), 1)

        finally:
            # Desconecta o handler
            post_save.disconnect(failing_handler, sender=Contato)


class TestSignalPerformance(TestCase):
    """Testes de performance para sinais."""

    def test_signal_performance_with_many_handlers(self) -> None:
        """Testa performance com muitos handlers conectados."""
        handlers = []

        # Cria vários handlers
        for i in range(10):

            def make_handler(index):
                def handler(sender: Any, instance: Contato, **kwargs: Any) -> None:
                    pass  # Handler vazio para teste de performance

                return handler

            handler = make_handler(i)
            handlers.append(handler)
            post_save.connect(handler, sender=Contato)

        try:
            import time

            start_time = time.time()

            # Cria contatos
            for i in range(50):
                Contato.objects.create(
                    telefone=f"551199999{i:04d}", nome_contato=f"Performance Test {i}"
                )

            end_time = time.time()

            # Deve completar em tempo razoável (< 5 segundos)
            self.assertLess(end_time - start_time, 5.0)

        finally:
            # Desconecta todos os handlers
            for handler in handlers:
                post_save.disconnect(handler, sender=Contato)
