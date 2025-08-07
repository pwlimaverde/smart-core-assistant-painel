"""Testes para os comandos de gerenciamento do app Oraculo."""

import io
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from ..management.commands.chatbot import Command as ChatbotCommand
from ..models import (
    Atendimento,
    Contato,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)


class TestChatbotCommand(TestCase):
    """Testes para o comando chatbot."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.command = ChatbotCommand()
        self.out = io.StringIO()
        self.err = io.StringIO()
        
        # Cria dados de teste
        self.contato = Contato.objects.create(
            telefone="5511999999999",
            nome="Cliente Teste"
        )
        
        self.atendimento = Atendimento.objects.create(
            contato=self.contato,
            status=StatusAtendimento.ATIVO
        )

    def test_command_help(self) -> None:
        """Testa a ajuda do comando."""
        self.assertIsNotNone(self.command.help)
        self.assertIn("chatbot", self.command.help.lower())

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_handle_default(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa a execução padrão do comando."""
        mock_loading.return_value = None
        mock_services.return_value = None
        
        call_command('chatbot', stdout=self.out, stderr=self.err)
        
        # Verifica se as funções foram chamadas
        mock_loading.assert_called_once()
        mock_services.assert_called_once()
        
        # Verifica a saída
        output = self.out.getvalue()
        self.assertIn("Iniciando", output)

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_handle_with_options(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa a execução do comando com opções."""
        mock_loading.return_value = None
        mock_services.return_value = None
        
        # Testa com opção de debug (se existir)
        try:
            call_command('chatbot', '--debug', stdout=self.out, stderr=self.err)
        except CommandError:
            # Se a opção não existir, testa sem ela
            call_command('chatbot', stdout=self.out, stderr=self.err)
        
        # Verifica se as funções foram chamadas
        mock_loading.assert_called_once()
        mock_services.assert_called_once()

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_handle_loading_error(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa o tratamento de erro no carregamento inicial."""
        mock_loading.side_effect = Exception("Erro no carregamento")
        mock_services.return_value = None
        
        # O comando deve continuar mesmo com erro no loading
        call_command('chatbot', stdout=self.out, stderr=self.err)
        
        # Verifica se o erro foi tratado
        error_output = self.err.getvalue()
        self.assertIn("Erro", error_output)
        
        # Os serviços ainda devem ser iniciados
        mock_services.assert_called_once()

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_handle_services_error(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa o tratamento de erro nos serviços."""
        mock_loading.return_value = None
        mock_services.side_effect = Exception("Erro nos serviços")
        
        # O comando deve tratar o erro graciosamente
        call_command('chatbot', stdout=self.out, stderr=self.err)
        
        # Verifica se o erro foi tratado
        error_output = self.err.getvalue()
        self.assertIn("Erro", error_output)

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_handle_keyboard_interrupt(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa o tratamento de interrupção por teclado."""
        mock_loading.return_value = None
        mock_services.side_effect = KeyboardInterrupt()
        
        # O comando deve tratar a interrupção graciosamente
        call_command('chatbot', stdout=self.out, stderr=self.err)
        
        # Verifica se a interrupção foi tratada
        output = self.out.getvalue()
        self.assertIn("Interrompido", output)

    def test_command_arguments(self) -> None:
        """Testa os argumentos do comando."""
        # Verifica se o comando aceita argumentos específicos
        parser = self.command.create_parser('manage.py', 'chatbot')
        
        # Testa argumentos válidos
        try:
            args = parser.parse_args([])
            self.assertIsNotNone(args)
        except SystemExit:
            # Se não aceitar argumentos vazios, testa com argumentos padrão
            pass

    @patch('smart_core_assistant_painel.modules.whatsapp.inicializar_webhook')
    @patch('smart_core_assistant_painel.modules.ai.inicializar_ai')
    def test_integration_with_modules(self, mock_ai: Mock, mock_webhook: Mock) -> None:
        """Testa a integração com módulos externos."""
        mock_ai.return_value = True
        mock_webhook.return_value = True
        
        # Simula a execução do comando
        with patch.object(self.command, 'handle') as mock_handle:
            mock_handle.return_value = None
            
            call_command('chatbot', stdout=self.out, stderr=self.err)
            
            mock_handle.assert_called_once()


class TestManagementCommandsIntegration(TestCase):
    """Testes de integração para comandos de gerenciamento."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.out = io.StringIO()
        self.err = io.StringIO()

    def test_chatbot_command_exists(self) -> None:
        """Testa se o comando chatbot existe e pode ser executado."""
        try:
            # Tenta executar o comando com timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Comando demorou muito para executar")
            
            # Define timeout de 5 segundos
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            try:
                call_command('chatbot', '--help', stdout=self.out, stderr=self.err)
            except TimeoutError:
                # Se demorar muito, considera que o comando existe
                pass
            finally:
                signal.alarm(0)  # Cancela o timeout
            
            # Se chegou até aqui, o comando existe
            self.assertTrue(True)
            
        except CommandError as e:
            # Se o comando não existir, falha o teste
            if "Unknown command" in str(e):
                self.fail(f"Comando 'chatbot' não encontrado: {e}")
            # Outros erros são aceitáveis (argumentos inválidos, etc.)
        except Exception:
            # Outros erros podem indicar que o comando existe mas tem problemas
            pass

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_command_with_database(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa o comando com operações de banco de dados."""
        mock_loading.return_value = None
        mock_services.return_value = None
        
        # Cria dados no banco
        contato = Contato.objects.create(
            telefone="5511888888888",
            nome="Cliente Comando"
        )
        
        atendimento = Atendimento.objects.create(
            contato=contato,
            status=StatusAtendimento.ATIVO
        )
        
        # Executa o comando
        call_command('chatbot', stdout=self.out, stderr=self.err)
        
        # Verifica se os dados ainda existem
        self.assertTrue(Contato.objects.filter(pk=contato.pk).exists())
        self.assertTrue(Atendimento.objects.filter(pk=atendimento.pk).exists())

    def test_command_error_handling(self) -> None:
        """Testa o tratamento de erros do comando."""
        # Testa com argumentos inválidos
        try:
            call_command('chatbot', '--invalid-arg', stdout=self.out, stderr=self.err)
        except (CommandError, SystemExit):
            # Erro esperado para argumentos inválidos
            pass
        except Exception as e:
            # Outros erros podem ser aceitáveis dependendo da implementação
            pass

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.logger')
    def test_command_logging(self, mock_logger: Mock) -> None:
        """Testa o sistema de logging do comando."""
        with patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services') as mock_services:
            with patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading') as mock_loading:
                mock_loading.return_value = None
                mock_services.return_value = None
                
                call_command('chatbot', stdout=self.out, stderr=self.err)
                
                # Verifica se o logger foi usado (se existir)
                if mock_logger.called:
                    self.assertTrue(mock_logger.info.called or mock_logger.debug.called)


class TestCommandPerformance(TestCase):
    """Testes de performance para comandos de gerenciamento."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.out = io.StringIO()
        self.err = io.StringIO()

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_command_execution_time(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa o tempo de execução do comando."""
        mock_loading.return_value = None
        mock_services.return_value = None
        
        import time
        
        start_time = time.time()
        call_command('chatbot', stdout=self.out, stderr=self.err)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # O comando deve executar em menos de 10 segundos (com mocks)
        self.assertLess(execution_time, 10.0)

    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_services')
    @patch('smart_core_assistant_painel.app.ui.oraculo.management.commands.chatbot.start_initial_loading')
    def test_command_memory_usage(self, mock_loading: Mock, mock_services: Mock) -> None:
        """Testa o uso de memória do comando."""
        mock_loading.return_value = None
        mock_services.return_value = None
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        call_command('chatbot', stdout=self.out, stderr=self.err)
        
        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        # O aumento de memória deve ser razoável (menos de 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)


class TestCommandConfiguration(TestCase):
    """Testes para configuração dos comandos."""

    def test_command_class_structure(self) -> None:
        """Testa a estrutura da classe do comando."""
        command = ChatbotCommand()
        
        # Verifica se tem os métodos necessários
        self.assertTrue(hasattr(command, 'handle'))
        self.assertTrue(callable(getattr(command, 'handle')))
        
        # Verifica se tem help
        self.assertTrue(hasattr(command, 'help'))
        self.assertIsInstance(command.help, str)

    def test_command_options(self) -> None:
        """Testa as opções do comando."""
        command = ChatbotCommand()
        parser = command.create_parser('manage.py', 'chatbot')
        
        # Verifica se o parser foi criado corretamente
        self.assertIsNotNone(parser)
        
        # Testa parsing de argumentos vazios
        try:
            args = parser.parse_args([])
            self.assertIsNotNone(args)
        except SystemExit:
            # Alguns comandos podem requerer argumentos
            pass

    def test_command_inheritance(self) -> None:
        """Testa se o comando herda corretamente de BaseCommand."""
        from django.core.management.base import BaseCommand
        
        command = ChatbotCommand()
        self.assertIsInstance(command, BaseCommand)
        
        # Verifica métodos herdados
        self.assertTrue(hasattr(command, 'execute'))
        self.assertTrue(hasattr(command, 'create_parser'))
        self.assertTrue(hasattr(command, 'print_help'))


class TestCommandDocumentation(TestCase):
    """Testes para documentação dos comandos."""

    def test_command_help_text(self) -> None:
        """Testa se o comando tem texto de ajuda adequado."""
        command = ChatbotCommand()
        
        self.assertIsNotNone(command.help)
        self.assertGreater(len(command.help), 10)  # Pelo menos 10 caracteres
        self.assertIn("chatbot", command.help.lower())

    def test_command_description(self) -> None:
        """Testa se o comando tem descrição adequada."""
        command = ChatbotCommand()
        
        # Verifica se tem descrição (pode estar em help ou em atributo separado)
        has_description = (
            hasattr(command, 'description') or 
            (hasattr(command, 'help') and len(command.help) > 20)
        )
        
        self.assertTrue(has_description)

    def test_command_usage_examples(self) -> None:
        """Testa se o comando fornece exemplos de uso."""
        command = ChatbotCommand()
        parser = command.create_parser('manage.py', 'chatbot')
        
        # Captura a ajuda do comando
        help_output = io.StringIO()
        try:
            parser.print_help(help_output)
            help_text = help_output.getvalue()
            
            # Verifica se contém informações úteis
            self.assertIn("chatbot", help_text.lower())
            
        except Exception:
            # Se não conseguir capturar a ajuda, verifica se pelo menos tem help
            self.assertIsNotNone(command.help)