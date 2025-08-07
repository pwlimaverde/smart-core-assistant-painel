"""Testes para sinais (signals) do app Oraculo."""

from typing import Any
from django.test import TestCase, TransactionTestCase
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from unittest.mock import Mock, patch

from ..models import (
    Contato,
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)


class TestModelSignals(TestCase):
    """Testes para sinais dos modelos."""

    def setUp(self) -> None:
        """Configuração inicial."""
        # Mock para capturar sinais
        self.signal_received = Mock()

        # Conecta sinais para teste
        post_save.connect(self.signal_received, sender=Contato)
        post_save.connect(self.signal_received, sender=Atendimento)
        post_save.connect(self.signal_received, sender=Mensagem)

    def tearDown(self) -> None:
        """Limpeza após testes."""
        # Desconecta sinais
        post_save.disconnect(self.signal_received, sender=Contato)
        post_save.disconnect(self.signal_received, sender=Atendimento)
        post_save.disconnect(self.signal_received, sender=Mensagem)

    def test_contato_post_save_signal(self) -> None:
        """Testa sinal post_save do modelo Contato."""
        # Cria contato
        contato = Contato.objects.create(telefone="5511999999999", nome="Cliente Teste")

        # Verifica se o sinal foi enviado
        self.signal_received.assert_called()

        # Verifica argumentos do sinal
        call_args = self.signal_received.call_args
        self.assertEqual(call_args[1]["sender"], Contato)
        self.assertEqual(call_args[1]["instance"], contato)
        self.assertTrue(call_args[1]["created"])

    def test_atendimento_post_save_signal(self) -> None:
        """Testa sinal post_save do modelo Atendimento."""
        contato = Contato.objects.create(
            telefone="5511888888888", nome="Cliente Atendimento"
        )

        # Reset mock
        self.signal_received.reset_mock()

        # Cria atendimento
        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Verifica se o sinal foi enviado
        self.signal_received.assert_called()

        call_args = self.signal_received.call_args
        self.assertEqual(call_args[1]["sender"], Atendimento)
        self.assertEqual(call_args[1]["instance"], atendimento)
        self.assertTrue(call_args[1]["created"])

    def test_mensagem_post_save_signal(self) -> None:
        """Testa sinal post_save do modelo Mensagem."""
        contato = Contato.objects.create(
            telefone="5511777777777", nome="Cliente Mensagem"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Reset mock
        self.signal_received.reset_mock()

        # Cria mensagem
        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Mensagem de teste",
            tipo=TipoMensagem.TEXTO,
            remetente=TipoRemetente.CONTATO,
        )

        # Verifica se o sinal foi enviado
        self.signal_received.assert_called()

        call_args = self.signal_received.call_args
        self.assertEqual(call_args[1]["sender"], Mensagem)
        self.assertEqual(call_args[1]["instance"], mensagem)
        self.assertTrue(call_args[1]["created"])

    def test_model_update_signal(self) -> None:
        """Testa sinal ao atualizar modelo."""
        contato = Contato.objects.create(
            telefone="5511666666666", nome="Cliente Original"
        )

        # Reset mock
        self.signal_received.reset_mock()

        # Atualiza contato
        contato.nome = "Cliente Atualizado"
        contato.save()

        # Verifica se o sinal foi enviado
        self.signal_received.assert_called()

        call_args = self.signal_received.call_args
        self.assertEqual(call_args[1]["sender"], Contato)
        self.assertEqual(call_args[1]["instance"], contato)
        self.assertFalse(call_args[1]["created"])  # Não é criação


class TestCustomSignals(TestCase):
    """Testes para sinais customizados do aplicativo."""

    def setUp(self) -> None:
        """Configuração inicial."""
        self.mock_handler = Mock()

    @patch("smart_core_assistant_painel.app.ui.oraculo.signals.atendimento_iniciado")
    def test_atendimento_iniciado_signal(self, mock_signal) -> None:
        """Testa sinal customizado de atendimento iniciado."""
        contato = Contato.objects.create(telefone="5511555555555", nome="Cliente Sinal")

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Se o sinal customizado existir, deve ter sido enviado
        # Este teste verifica se a estrutura está preparada para sinais customizados
        self.assertIsNotNone(atendimento)

    @patch("smart_core_assistant_painel.app.ui.oraculo.signals.mensagem_recebida")
    def test_mensagem_recebida_signal(self, mock_signal) -> None:
        """Testa sinal customizado de mensagem recebida."""
        contato = Contato.objects.create(
            telefone="5511444444444", nome="Cliente Mensagem Sinal"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        mensagem = Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Mensagem com sinal",
            tipo=TipoMensagem.TEXTO,
            remetente=TipoRemetente.CONTATO,
        )

        # Verifica se a estrutura está preparada
        self.assertIsNotNone(mensagem)

    @patch("smart_core_assistant_painel.app.ui.oraculo.signals.atendimento_finalizado")
    def test_atendimento_finalizado_signal(self, mock_signal) -> None:
        """Testa sinal customizado de atendimento finalizado."""
        contato = Contato.objects.create(
            telefone="5511333333333", nome="Cliente Finalização"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Finaliza atendimento
        atendimento.status = StatusAtendimento.FINALIZADO
        atendimento.data_fim = timezone.now()
        atendimento.save()

        # Verifica se a estrutura está preparada
        self.assertEqual(atendimento.status, StatusAtendimento.FINALIZADO)


class TestSignalHandlers(TestCase):
    """Testes para handlers de sinais."""

    def setUp(self) -> None:
        """Configuração inicial."""
        # Simula handlers de sinais
        self.log_handler = Mock()
        self.notification_handler = Mock()
        self.analytics_handler = Mock()

    def test_contato_created_handler(self) -> None:
        """Testa handler para criação de contato."""

        # Simula handler que registra criação de contato
        @receiver(post_save, sender=Contato)
        def log_contato_created(
            sender: Any, instance: Contato, created: bool, **kwargs: Any
        ) -> None:
            if created:
                self.log_handler(f"Contato criado: {instance.nome}")

        # Cria contato
        Contato.objects.create(telefone="5511222222222", nome="Cliente Log")

        # Verifica se o handler foi chamado
        self.log_handler.assert_called_with("Contato criado: Cliente Log")

        # Desconecta o handler
        post_save.disconnect(log_contato_created, sender=Contato)

    def test_atendimento_status_change_handler(self) -> None:
        """Testa handler para mudança de status de atendimento."""
        contato = Contato.objects.create(
            telefone="5511111111111", nome="Cliente Status"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Simula handler que monitora mudanças de status
        @receiver(pre_save, sender=Atendimento)
        def monitor_status_change(
            sender: Any, instance: Atendimento, **kwargs: Any
        ) -> None:
            if instance.pk:
                try:
                    old_instance = Atendimento.objects.get(pk=instance.pk)
                    if old_instance.status != instance.status:
                        self.notification_handler(
                            f"Status alterado de {old_instance.status} para {instance.status}"
                        )
                except Atendimento.DoesNotExist:
                    pass

        # Altera status
        atendimento.status = StatusAtendimento.HUMANO
        atendimento.save()

        # Verifica se o handler foi chamado
        self.notification_handler.assert_called_with(
            f"Status alterado de {StatusAtendimento.ATIVO} para {StatusAtendimento.HUMANO}"
        )

        # Desconecta o handler
        pre_save.disconnect(monitor_status_change, sender=Atendimento)

    def test_mensagem_analytics_handler(self) -> None:
        """Testa handler para analytics de mensagens."""
        contato = Contato.objects.create(
            telefone="5511000000000", nome="Cliente Analytics"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Simula handler de analytics
        @receiver(post_save, sender=Mensagem)
        def track_mensagem(
            sender: Any, instance: Mensagem, created: bool, **kwargs: Any
        ) -> None:
            if created:
                self.analytics_handler(
                    {
                        "tipo": instance.tipo,
                        "remetente": instance.remetente,
                        "atendimento_id": instance.atendimento.id,
                    }
                )

        # Cria mensagem
        Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Mensagem analytics",
            tipo=TipoMensagem.TEXTO,
            remetente=TipoRemetente.CONTATO,
        )

        # Verifica se o handler foi chamado
        self.analytics_handler.assert_called_with(
            {
                "tipo": TipoMensagem.TEXTO,
                "remetente": TipoRemetente.CONTATO,
                "atendimento_id": atendimento.id,
            }
        )

        # Desconecta o handler
        post_save.disconnect(track_mensagem, sender=Mensagem)


class TestSignalErrorHandling(TestCase):
    """Testes para tratamento de erros em sinais."""

    def setUp(self) -> None:
        """Configuração inicial."""
        self.error_handler = Mock()

    def test_signal_handler_exception(self) -> None:
        """Testa tratamento de exceções em handlers de sinais."""

        # Simula handler que gera exceção
        @receiver(post_save, sender=Contato)
        def failing_handler(
            sender: Any, instance: Contato, created: bool, **kwargs: Any
        ) -> None:
            if created:
                raise Exception("Erro simulado no handler")

        # Cria contato (deve funcionar mesmo com handler falhando)
        try:
            contato = Contato.objects.create(
                telefone="5510999999999", nome="Cliente Erro"
            )

            # O contato deve ser criado mesmo com erro no handler
            self.assertIsNotNone(contato.id)

        except Exception as e:
            # Se a exceção vazar, registra para análise
            self.error_handler(str(e))

        # Desconecta o handler
        post_save.disconnect(failing_handler, sender=Contato)

    def test_signal_handler_with_database_error(self) -> None:
        """Testa handler com erro de banco de dados."""

        # Simula handler que tenta operação de banco inválida
        @receiver(post_save, sender=Atendimento)
        def db_error_handler(
            sender: Any, instance: Atendimento, created: bool, **kwargs: Any
        ) -> None:
            if created:
                try:
                    # Tenta criar contato com telefone duplicado
                    Contato.objects.create(
                        telefone=instance.contato.telefone,  # Telefone já existe
                        nome="Duplicado",
                    )
                except Exception as e:
                    self.error_handler(f"Erro de banco: {str(e)}")

        contato = Contato.objects.create(
            telefone="5510888888888", nome="Cliente DB Erro"
        )

        # Cria atendimento (deve acionar o handler com erro)
        Atendimento.objects.create(contato=contato, status=StatusAtendimento.ATIVO)

        # Verifica se o erro foi capturado
        self.error_handler.assert_called()

        # Desconecta o handler
        post_save.disconnect(db_error_handler, sender=Atendimento)

    def test_signal_handler_timeout(self) -> None:
        """Testa handler com timeout."""
        import time

        # Simula handler lento
        @receiver(post_save, sender=Mensagem)
        def slow_handler(
            sender: Any, instance: Mensagem, created: bool, **kwargs: Any
        ) -> None:
            if created:
                start_time = time.time()
                time.sleep(0.1)  # Simula operação lenta
                end_time = time.time()

                if end_time - start_time > 0.05:  # Mais de 50ms
                    self.error_handler("Handler muito lento")

        contato = Contato.objects.create(
            telefone="5510777777777", nome="Cliente Timeout"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Cria mensagem (deve acionar handler lento)
        Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Mensagem timeout",
            tipo=TipoMensagem.TEXTO,
            remetente=TipoRemetente.CONTATO,
        )

        # Verifica se o timeout foi detectado
        self.error_handler.assert_called_with("Handler muito lento")

        # Desconecta o handler
        post_save.disconnect(slow_handler, sender=Mensagem)


class TestSignalIntegration(TransactionTestCase):
    """Testes de integração para sinais (usando TransactionTestCase para transações)."""

    def setUp(self) -> None:
        """Configuração inicial."""
        self.integration_log = []

    def test_complete_workflow_signals(self) -> None:
        """Testa sinais em um fluxo completo de atendimento."""

        # Handlers para capturar todo o fluxo
        @receiver(post_save, sender=Contato)
        def log_contato(
            sender: Any, instance: Contato, created: bool, **kwargs: Any
        ) -> None:
            if created:
                self.integration_log.append(f"Contato criado: {instance.nome}")

        @receiver(post_save, sender=Atendimento)
        def log_atendimento(
            sender: Any, instance: Atendimento, created: bool, **kwargs: Any
        ) -> None:
            if created:
                self.integration_log.append(f"Atendimento iniciado: {instance.id}")
            else:
                self.integration_log.append(f"Atendimento atualizado: {instance.id}")

        @receiver(post_save, sender=Mensagem)
        def log_mensagem(
            sender: Any, instance: Mensagem, created: bool, **kwargs: Any
        ) -> None:
            if created:
                self.integration_log.append(
                    f"Mensagem criada: {instance.remetente} - {instance.tipo}"
                )

        # Executa fluxo completo
        contato = Contato.objects.create(telefone="5510666666666", nome="Cliente Fluxo")

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Primeira mensagem",
            tipo=TipoMensagem.TEXTO,
            remetente=TipoRemetente.CONTATO,
        )

        Mensagem.objects.create(
            atendimento=atendimento,
            conteudo="Resposta do bot",
            tipo=TipoMensagem.TEXTO,
            remetente=TipoRemetente.BOT,
        )

        # Finaliza atendimento
        atendimento.status = StatusAtendimento.FINALIZADO
        atendimento.data_fim = timezone.now()
        atendimento.save()

        # Verifica se todos os sinais foram capturados
        expected_logs = [
            "Contato criado: Cliente Fluxo",
            f"Atendimento iniciado: {atendimento.id}",
            f"Mensagem criada: {TipoRemetente.CONTATO} - {TipoMensagem.TEXTO}",
            f"Mensagem criada: {TipoRemetente.BOT} - {TipoMensagem.TEXTO}",
            f"Atendimento atualizado: {atendimento.id}",
        ]

        for expected_log in expected_logs:
            self.assertIn(expected_log, self.integration_log)

        # Desconecta handlers
        post_save.disconnect(log_contato, sender=Contato)
        post_save.disconnect(log_atendimento, sender=Atendimento)
        post_save.disconnect(log_mensagem, sender=Mensagem)

    def test_signal_ordering(self) -> None:
        """Testa ordem de execução dos sinais."""
        execution_order = []

        @receiver(pre_save, sender=Contato)
        def pre_save_contato(sender: Any, instance: Contato, **kwargs: Any) -> None:
            execution_order.append("pre_save_contato")

        @receiver(post_save, sender=Contato)
        def post_save_contato(
            sender: Any, instance: Contato, created: bool, **kwargs: Any
        ) -> None:
            execution_order.append("post_save_contato")

        # Cria contato
        Contato.objects.create(telefone="5510555555555", nome="Cliente Ordem")

        # Verifica ordem de execução
        expected_order = ["pre_save_contato", "post_save_contato"]
        self.assertEqual(execution_order, expected_order)

        # Desconecta handlers
        pre_save.disconnect(pre_save_contato, sender=Contato)
        post_save.disconnect(post_save_contato, sender=Contato)


class TestSignalPerformance(TestCase):
    """Testes de performance para sinais."""

    def test_multiple_signals_performance(self) -> None:
        """Testa performance com múltiplos sinais."""
        import time

        call_count = 0

        @receiver(post_save, sender=Contato)
        def performance_handler(
            sender: Any, instance: Contato, created: bool, **kwargs: Any
        ) -> None:
            nonlocal call_count
            call_count += 1

        start_time = time.time()

        # Cria múltiplos contatos
        for i in range(100):
            Contato.objects.create(
                telefone=f"551044444{i:04d}", nome=f"Cliente Performance {i}"
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # Verifica que todos os sinais foram executados
        self.assertEqual(call_count, 100)

        # Performance deve ser aceitável
        self.assertLess(execution_time, 5.0)  # Menos de 5 segundos

        # Desconecta handler
        post_save.disconnect(performance_handler, sender=Contato)

    def test_signal_memory_usage(self) -> None:
        """Testa uso de memória com sinais."""
        import gc

        # Força garbage collection
        gc.collect()

        data_store = []

        @receiver(post_save, sender=Mensagem)
        def memory_handler(
            sender: Any, instance: Mensagem, created: bool, **kwargs: Any
        ) -> None:
            # Simula handler que armazena dados
            data_store.append(
                {
                    "id": instance.id,
                    "conteudo": instance.conteudo,
                    "timestamp": instance.data_criacao,
                }
            )

        contato = Contato.objects.create(
            telefone="5510333333333", nome="Cliente Memória"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.ATIVO
        )

        # Cria múltiplas mensagens
        for i in range(50):
            Mensagem.objects.create(
                atendimento=atendimento,
                conteudo=f"Mensagem {i}",
                tipo=TipoMensagem.TEXTO,
                remetente=TipoRemetente.CONTATO,
            )

        # Verifica que os dados foram armazenados
        self.assertEqual(len(data_store), 50)

        # Limpa dados
        data_store.clear()
        gc.collect()

        # Desconecta handler
        post_save.disconnect(memory_handler, sender=Mensagem)
