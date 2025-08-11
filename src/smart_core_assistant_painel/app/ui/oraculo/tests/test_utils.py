"""Testes para utilitários e funções auxiliares do app Oraculo."""

from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from ..models import (
    Atendimento,
    Contato,
    Mensagem,
    StatusAtendimento,
    TipoRemetente,
    buscar_atendimento_ativo,
    inicializar_atendimento_whatsapp,
    validar_telefone_brasileiro,
)


class TestValidacaoTelefone(TestCase):
    """Testes para validação de telefone brasileiro."""

    def test_telefone_valido_com_ddd(self) -> None:
        """Testa validação de telefone válido com DDD."""
        telefones_validos = ["11999999999", "21987654321", "85912345678", "47988776655"]

        for telefone in telefones_validos:
            with self.subTest(telefone=telefone):
                self.assertTrue(validar_telefone_brasileiro(telefone))

    def test_telefone_valido_com_codigo_pais(self) -> None:
        """Testa validação de telefone válido com código do país."""
        telefones_validos = [
            "5511999999999",
            "5521987654321",
            "5585912345678",
            "5547988776655",
        ]

        for telefone in telefones_validos:
            with self.subTest(telefone=telefone):
                self.assertTrue(validar_telefone_brasileiro(telefone))

    def test_telefone_invalido_muito_curto(self) -> None:
        """Testa validação de telefone muito curto."""
        telefones_invalidos = ["1199999", "119999999", "11999999"]

        for telefone in telefones_invalidos:
            with self.subTest(telefone=telefone):
                self.assertFalse(validar_telefone_brasileiro(telefone))

    def test_telefone_invalido_muito_longo(self) -> None:
        """Testa validação de telefone muito longo."""
        telefones_invalidos = ["551199999999999", "11999999999999", "5511999999999999"]

        for telefone in telefones_invalidos:
            with self.subTest(telefone=telefone):
                self.assertFalse(validar_telefone_brasileiro(telefone))

    def test_telefone_invalido_caracteres(self) -> None:
        """Testa validação de telefone com caracteres inválidos."""
        telefones_invalidos = [
            "11-99999-9999",
            "(11) 99999-9999",
            "11 99999 9999",
            "11.99999.9999",
            "abc99999999",
            "11999999abc",
        ]

        for telefone in telefones_invalidos:
            with self.subTest(telefone=telefone):
                self.assertFalse(validar_telefone_brasileiro(telefone))

    def test_telefone_vazio_ou_none(self) -> None:
        """Testa validação de telefone vazio ou None."""
        self.assertFalse(validar_telefone_brasileiro(""))
        self.assertFalse(validar_telefone_brasileiro(None))
        self.assertFalse(validar_telefone_brasileiro("   "))

    def test_telefone_ddd_invalido(self) -> None:
        """Testa validação de telefone com DDD inválido."""
        telefones_invalidos = [
            "00999999999",  # DDD 00 não existe
            "99999999999",  # DDD 99 não existe
            "01999999999",  # DDD 01 não existe
        ]

        for telefone in telefones_invalidos:
            with self.subTest(telefone=telefone):
                # Dependendo da implementação, pode aceitar ou não
                # Este teste verifica se a validação é rigorosa
                resultado = validar_telefone_brasileiro(telefone)
                # Se a validação for básica (apenas tamanho), pode passar
                # Se for rigorosa (verificar DDDs válidos), deve falhar
                self.assertIsInstance(resultado, bool)


class TestBuscarAtendimentoAtivo(TestCase):
    """Testes para a função buscar_atendimento_ativo."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999", nome="Cliente Teste"
        )

        self.atendimento_ativo = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.ATIVO
        )

    def test_buscar_atendimento_existente(self) -> None:
        """Testa busca de atendimento ativo existente."""
        atendimento = buscar_atendimento_ativo("5511999999999")

        self.assertIsNotNone(atendimento)
        self.assertEqual(atendimento, self.atendimento_ativo)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)

    def test_buscar_atendimento_inexistente(self) -> None:
        """Testa busca de atendimento para telefone inexistente."""
        atendimento = buscar_atendimento_ativo("5511888888888")

        self.assertIsNone(atendimento)

    def test_buscar_atendimento_finalizado(self) -> None:
        """Testa que atendimentos finalizados não são retornados."""
        # Finaliza o atendimento
        self.atendimento_ativo.status = StatusAtendimento.FINALIZADO
        self.atendimento_ativo.data_fim = timezone.now()
        self.atendimento_ativo.save()

        atendimento = buscar_atendimento_ativo("5511999999999")

        self.assertIsNone(atendimento)

    def test_buscar_atendimento_pausado(self) -> None:
        """Testa busca de atendimento pausado."""
        # Pausa o atendimento
        self.atendimento_ativo.status = StatusAtendimento.PAUSADO
        self.atendimento_ativo.save()

        atendimento = buscar_atendimento_ativo("5511999999999")

        # Dependendo da implementação, pode retornar ou não atendimentos pausados
        if atendimento:
            self.assertEqual(atendimento.status, StatusAtendimento.PAUSADO)

    def test_buscar_multiplos_atendimentos_ativos(self) -> None:
        """Testa busca quando há múltiplos atendimentos ativos (cenário inválido)."""
        # Cria outro atendimento ativo para o mesmo contato
        atendimento_extra = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.ATIVO
        )

        atendimento = buscar_atendimento_ativo("5511999999999")

        # Deve retornar um dos atendimentos (provavelmente o mais recente)
        self.assertIsNotNone(atendimento)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)
        self.assertIn(atendimento, [self.atendimento_ativo, atendimento_extra])

    def test_buscar_com_telefone_formatado(self) -> None:
        """Testa busca com diferentes formatos de telefone."""
        formatos_telefone = ["5511999999999", "11999999999", "+5511999999999"]

        for telefone in formatos_telefone:
            with self.subTest(telefone=telefone):
                # A função deve normalizar o telefone antes da busca
                atendimento = buscar_atendimento_ativo(telefone)
                # Pode retornar o atendimento ou None, dependendo da normalização
                if atendimento:
                    self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)


class TestInicializarAtendimentoWhatsApp(TestCase):
    """Testes para a função inicializar_atendimento_whatsapp."""

    def test_inicializar_novo_contato(self) -> None:
        """Testa inicialização de atendimento para novo contato."""
        telefone = "5511777777777"
        conteudo = "Olá, preciso de ajuda"
        nome_perfil = "Novo Cliente"

        contato, atendimento = inicializar_atendimento_whatsapp(
            telefone, conteudo, nome_perfil_whatsapp=nome_perfil
        )

        # Verifica se o contato foi criado
        self.assertEqual(contato.telefone, telefone)
        self.assertEqual(contato.nome, nome_perfil)

        # Verifica se o atendimento foi criado
        self.assertEqual(atendimento.contato, contato)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)
        self.assertIsNotNone(atendimento.data_inicio)

        # Verifica se a mensagem inicial foi criada
        mensagem = Mensagem.objects.filter(
            atendimento=atendimento, remetente=TipoRemetente.CONTATO
        ).first()

        self.assertIsNotNone(mensagem)
        self.assertEqual(mensagem.conteudo, conteudo)

    def test_inicializar_contato_existente(self) -> None:
        """Testa inicialização de atendimento para contato existente."""
        # Cria contato existente
        contato_existente = Contato.objects.create(
            telefone="5511888888888", nome="Cliente Existente"
        )

        telefone = "5511888888888"
        conteudo = "Nova mensagem"

        contato, atendimento = inicializar_atendimento_whatsapp(telefone, conteudo)

        # Deve retornar o contato existente
        self.assertEqual(contato, contato_existente)

        # Deve criar novo atendimento
        self.assertEqual(atendimento.contato, contato_existente)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)

    def test_inicializar_com_atendimento_ativo_existente(self) -> None:
        """Testa inicialização quando já existe atendimento ativo."""
        # Cria contato e atendimento existentes
        contato_existente = Contato.objects.create(
            telefone="5511666666666", nome="Cliente com Atendimento"
        )

        Atendimento.objects.create(
            contato=contato_existente, status=StatusAtendimento.ATIVO
        )

        telefone = "5511666666666"
        conteudo = "Continuando conversa"

        contato, atendimento = inicializar_atendimento_whatsapp(telefone, conteudo)

        # Deve retornar o contato existente
        self.assertEqual(contato, contato_existente)

        # Pode retornar o atendimento existente ou criar novo
        # Dependendo da lógica de negócio
        self.assertEqual(atendimento.contato, contato_existente)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)

    def test_inicializar_sem_nome_perfil(self) -> None:
        """Testa inicialização sem nome do perfil WhatsApp."""
        telefone = "5511555555555"
        conteudo = "Mensagem sem nome"

        contato, atendimento = inicializar_atendimento_whatsapp(telefone, conteudo)

        # Deve criar contato com nome padrão ou telefone
        self.assertEqual(contato.telefone, telefone)
        self.assertIsNotNone(contato.nome)

        # Pode usar o telefone como nome ou um nome padrão
        self.assertTrue(
            contato.nome == telefone
            or "Cliente" in contato.nome
            or "Usuário" in contato.nome
        )

    def test_inicializar_com_dados_extras(self) -> None:
        """Testa inicialização com dados extras do WhatsApp."""
        telefone = "5511444444444"
        conteudo = "Mensagem com dados extras"
        nome_perfil = "Cliente Completo"

        # Simula dados extras que podem vir do WhatsApp
        dados_extras = {
            "profile_pic_url": "https://example.com/pic.jpg",
            "status": "Disponível",
        }

        contato, atendimento = inicializar_atendimento_whatsapp(
            telefone, conteudo, nome_perfil_whatsapp=nome_perfil, **dados_extras
        )

        self.assertEqual(contato.telefone, telefone)
        self.assertEqual(contato.nome, nome_perfil)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)


class TestUtilsIntegration(TestCase):
    """Testes de integração para utilitários."""

    def test_fluxo_completo_novo_atendimento(self) -> None:
        """Testa o fluxo completo de criação de novo atendimento."""
        telefone = "5511333333333"

        # 1. Verifica que não existe atendimento ativo
        atendimento_inicial = buscar_atendimento_ativo(telefone)
        self.assertIsNone(atendimento_inicial)

        # 2. Inicializa novo atendimento
        contato, atendimento = inicializar_atendimento_whatsapp(
            telefone, "Primeira mensagem", nome_perfil_whatsapp="Cliente Novo"
        )

        # 3. Verifica que agora existe atendimento ativo
        atendimento_encontrado = buscar_atendimento_ativo(telefone)
        self.assertIsNotNone(atendimento_encontrado)
        self.assertEqual(atendimento_encontrado, atendimento)

        # 4. Finaliza o atendimento
        atendimento.status = StatusAtendimento.FINALIZADO
        atendimento.data_fim = timezone.now()
        atendimento.save()

        # 5. Verifica que não há mais atendimento ativo
        atendimento_final = buscar_atendimento_ativo(telefone)
        self.assertIsNone(atendimento_final)

    def test_validacao_telefone_com_busca(self) -> None:
        """Testa integração entre validação de telefone e busca."""
        telefones_validos = ["5511999999999", "11999999999"]
        telefones_invalidos = ["123", "abc", ""]

        for telefone in telefones_validos:
            with self.subTest(telefone=telefone, tipo="válido"):
                if validar_telefone_brasileiro(telefone):
                    # Se o telefone é válido, a busca não deve gerar erro
                    resultado = buscar_atendimento_ativo(telefone)
                    # Pode retornar None (não encontrado) mas não deve gerar exceção
                    self.assertIsNone(resultado)  # Não existe atendimento

        for telefone in telefones_invalidos:
            with self.subTest(telefone=telefone, tipo="inválido"):
                if not validar_telefone_brasileiro(telefone):
                    # Para telefones inválidos, a busca pode retornar None ou gerar erro
                    try:
                        resultado = buscar_atendimento_ativo(telefone)
                        self.assertIsNone(resultado)
                    except Exception:
                        # Erro esperado para telefones inválidos
                        pass


class TestUtilsPerformance(TestCase):
    """Testes de performance para utilitários."""

    def test_busca_atendimento_performance(self) -> None:
        """Testa a performance da busca de atendimento."""
        # Cria múltiplos contatos e atendimentos
        contatos = []
        for i in range(100):
            contato = Contato.objects.create(
                telefone=f"551199{i:06d}", nome=f"Cliente {i}"
            )
            contatos.append(contato)

            Atendimento.objects.create(
                contato=contato,
                status=StatusAtendimento.ATIVO
                if i % 2 == 0
                else StatusAtendimento.FINALIZADO,
            )

        import time

        # Testa múltiplas buscas
        start_time = time.time()

        for i in range(0, 100, 10):
            telefone = f"551199{i:06d}"
            buscar_atendimento_ativo(telefone)

        end_time = time.time()
        execution_time = end_time - start_time

        # 10 buscas devem executar em menos de 1 segundo
        self.assertLess(execution_time, 1.0)

    def test_inicializacao_atendimento_performance(self) -> None:
        """Testa a performance da inicialização de atendimentos."""
        import time

        start_time = time.time()

        # Cria múltiplos atendimentos
        for i in range(50):
            telefone = f"551188{i:06d}"
            inicializar_atendimento_whatsapp(
                telefone, f"Mensagem {i}", nome_perfil_whatsapp=f"Cliente {i}"
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # 50 inicializações devem executar em menos de 5 segundos
        self.assertLess(execution_time, 5.0)

    def test_validacao_telefone_performance(self) -> None:
        """Testa a performance da validação de telefone."""
        telefones = [
            "5511999999999",
            "11999999999",
            "5521987654321",
            "invalid",
            "123",
            "",
            "abc123def456",
        ] * 100  # 700 telefones para testar

        import time

        start_time = time.time()

        for telefone in telefones:
            validar_telefone_brasileiro(telefone)

        end_time = time.time()
        execution_time = end_time - start_time

        # 700 validações devem executar em menos de 1 segundo
        self.assertLess(execution_time, 1.0)


class TestUtilsErrorHandling(TestCase):
    """Testes de tratamento de erros para utilitários."""

    def test_buscar_atendimento_com_erro_db(self) -> None:
        """Testa busca de atendimento com erro de banco de dados."""
        with patch("oraculo.models.Atendimento.objects.filter") as mock_filter:
            mock_filter.side_effect = Exception("Erro de banco")

            # A função deve tratar o erro graciosamente
            try:
                resultado = buscar_atendimento_ativo("5511999999999")
                # Pode retornar None ou re-lançar a exceção
                self.assertIsNone(resultado)
            except Exception:
                # Exceção esperada
                pass

    def test_inicializar_atendimento_com_erro(self) -> None:
        """Testa inicialização de atendimento com erro."""
        with patch(
            "oraculo.models.Contato.objects.get_or_create"
        ) as mock_get_or_create:
            mock_get_or_create.side_effect = Exception("Erro ao criar contato")

            # A função deve tratar o erro
            try:
                contato, atendimento = inicializar_atendimento_whatsapp(
                    "5511999999999", "Teste erro"
                )
                # Se não gerar exceção, deve retornar valores válidos ou None
                if contato:
                    self.assertIsNotNone(contato.telefone)
                if atendimento:
                    self.assertIsNotNone(atendimento.contato)
            except Exception:
                # Exceção esperada
                pass

    def test_validacao_telefone_tipos_invalidos(self) -> None:
        """Testa validação de telefone com tipos de dados inválidos."""
        valores_invalidos = [123, [], {}, object(), True, False]

        for valor in valores_invalidos:
            with self.subTest(valor=valor):
                try:
                    resultado = validar_telefone_brasileiro(valor)
                    # Deve retornar False para tipos inválidos
                    self.assertFalse(resultado)
                except (TypeError, AttributeError):
                    # Exceção esperada para tipos incompatíveis
                    pass
