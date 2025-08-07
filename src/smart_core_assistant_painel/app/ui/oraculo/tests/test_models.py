"""Testes para os modelos do app Oraculo."""

from django.test import TestCase
from django.utils import timezone

from ..models import (
    AtendenteHumano,
    Atendimento,
    Cliente,
    Contato,
    FluxoConversa,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
    Treinamentos,
    buscar_atendimento_ativo,
    inicializar_atendimento_whatsapp,
)


class TestContato(TestCase):
    """Testes para o modelo Contato."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999",
            nome="Cliente Teste",
            email="cliente@teste.com"
        )

    def test_contato_creation(self) -> None:
        """Testa a criação de um contato."""
        self.assertEqual(self.contato.telefone, "5511999999999")
        self.assertEqual(self.contato.nome, "Cliente Teste")
        self.assertEqual(self.contato.email, "cliente@teste.com")
        self.assertEqual(str(self.contato), "Cliente Teste (5511999999999)")

    def test_contato_telefone_unique(self) -> None:
        """Testa se o telefone é único."""
        with self.assertRaises(Exception):
            Contato.objects.create(
                telefone="5511999999999",
                nome="Outro Cliente"
            )


class TestAtendenteHumano(TestCase):
    """Testes para o modelo AtendenteHumano."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.atendente = AtendenteHumano.objects.create(
            telefone="5511888888888",
            nome="Atendente Teste",
            cargo="Analista",
            email="atendente@teste.com"
        )

    def test_atendente_humano_creation(self) -> None:
        """Testa a criação de um atendente humano."""
        self.assertEqual(self.atendente.nome, "Atendente Teste")
        self.assertEqual(self.atendente.cargo, "Analista")
        self.assertTrue(self.atendente.ativo)
        self.assertTrue(self.atendente.disponivel)
        self.assertEqual(self.atendente.max_atendimentos_simultaneos, 5)

    def test_atendente_str_representation(self) -> None:
        """Testa a representação string do atendente."""
        expected = f"{self.atendente.nome} - {self.atendente.cargo}"
        self.assertEqual(str(self.atendente), expected)


class TestAtendimento(TestCase):
    """Testes para o modelo Atendimento."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999",
            nome="Cliente Teste"
        )
        
        self.atendimento = Atendimento.objects.create(
            contato=self.contato,
            status=StatusAtendimento.ATIVO
        )

    def test_atendimento_creation(self) -> None:
        """Testa a criação de um atendimento."""
        self.assertEqual(self.atendimento.contato, self.contato)
        self.assertEqual(self.atendimento.status, StatusAtendimento.ATIVO)
        self.assertIsNotNone(self.atendimento.data_inicio)
        self.assertIsNone(self.atendimento.data_fim)

    def test_atendimento_finalizacao(self) -> None:
        """Testa a finalização de um atendimento."""
        self.atendimento.status = StatusAtendimento.FINALIZADO
        self.atendimento.data_fim = timezone.now()
        self.atendimento.save()
        
        self.assertEqual(self.atendimento.status, StatusAtendimento.FINALIZADO)
        self.assertIsNotNone(self.atendimento.data_fim)


class TestMensagem(TestCase):
    """Testes para o modelo Mensagem."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999",
            nome="Cliente Teste"
        )
        
        self.atendimento = Atendimento.objects.create(
            contato=self.contato,
            status=StatusAtendimento.ATIVO
        )

    def test_mensagem_creation(self) -> None:
        """Testa a criação de uma mensagem."""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Mensagem de teste",
            message_id_whatsapp="TEST123"
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
            conteudo="Resposta do bot"
        )
        
        self.assertEqual(mensagem.remetente, TipoRemetente.BOT)
        self.assertEqual(mensagem.conteudo, "Resposta do bot")


class TestTreinamentos(TestCase):
    """Testes para o modelo Treinamentos."""

    def test_treinamentos_creation(self) -> None:
        """Testa a criação de um treinamento."""
        treinamento = Treinamentos.objects.create(
            tag="teste",
            grupo="grupo_teste",
            _documentos=[{"content": "Documento de teste"}]
        )
        
        self.assertEqual(treinamento.tag, "teste")
        self.assertEqual(treinamento.grupo, "grupo_teste")
        self.assertFalse(treinamento.treinamento_finalizado)
        self.assertEqual(len(treinamento.documentos), 1)
        self.assertEqual(treinamento.documentos[0]["content"], "Documento de teste")

    def test_treinamentos_finalizacao(self) -> None:
        """Testa a finalização de um treinamento."""
        treinamento = Treinamentos.objects.create(
            tag="teste_finalizado",
            grupo="grupo_teste",
            _documentos=[{"content": "Documento finalizado"}],
            treinamento_finalizado=True
        )
        
        self.assertTrue(treinamento.treinamento_finalizado)


class TestUtilityFunctions(TestCase):
    """Testes para as funções utilitárias dos modelos."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999",
            nome="Cliente Teste"
        )
        
        self.atendimento = Atendimento.objects.create(
            contato=self.contato,
            status=StatusAtendimento.ATIVO
        )

    def test_buscar_atendimento_ativo(self) -> None:
        """Testa a busca por atendimento ativo."""
        atendimento_encontrado = buscar_atendimento_ativo("5511999999999")
        self.assertEqual(atendimento_encontrado, self.atendimento)
        
        # Testa busca com telefone inexistente
        atendimento_inexistente = buscar_atendimento_ativo("5511000000000")
        self.assertIsNone(atendimento_inexistente)

    def test_buscar_atendimento_finalizado(self) -> None:
        """Testa que atendimentos finalizados não são retornados."""
        self.atendimento.status = StatusAtendimento.FINALIZADO
        self.atendimento.save()
        
        atendimento_encontrado = buscar_atendimento_ativo("5511999999999")
        self.assertIsNone(atendimento_encontrado)

    def test_inicializar_atendimento_whatsapp(self) -> None:
        """Testa a inicialização de atendimento via WhatsApp."""
        telefone = "5511777777777"
        conteudo = "Olá, preciso de ajuda"
        nome_perfil = "Novo Cliente"
        
        contato, atendimento = inicializar_atendimento_whatsapp(
            telefone, conteudo, nome_perfil_whatsapp=nome_perfil
        )
        
        self.assertEqual(contato.telefone, telefone)
        self.assertEqual(contato.nome, nome_perfil)
        self.assertEqual(atendimento.contato, contato)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)

    def test_inicializar_atendimento_contato_existente(self) -> None:
        """Testa inicialização com contato já existente."""
        telefone = "5511999999999"  # Contato já existe no setUp
        conteudo = "Nova mensagem"
        
        contato, atendimento = inicializar_atendimento_whatsapp(
            telefone, conteudo
        )
        
        # Deve retornar o contato existente
        self.assertEqual(contato, self.contato)
        # Deve criar um novo atendimento
        self.assertNotEqual(atendimento, self.atendimento)
        self.assertEqual(atendimento.status, StatusAtendimento.ATIVO)


class TestModelPerformance(TestCase):
    """Testes de performance para operações críticas dos modelos."""

    def test_busca_atendimento_ativo_performance(self) -> None:
        """Testa a performance da busca de atendimento ativo."""
        # Cria múltiplos contatos e atendimentos
        contatos = []
        for i in range(100):
            contato = Contato.objects.create(
                telefone=f"551199999{i:04d}",
                nome=f"Cliente {i}"
            )
            contatos.append(contato)
            
            Atendimento.objects.create(
                contato=contato,
                status=StatusAtendimento.ATIVO if i % 2 == 0 else StatusAtendimento.FINALIZADO
            )
        
        # Testa a busca
        import time
        start_time = time.time()
        
        atendimento = buscar_atendimento_ativo("5511999990000")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verifica se a busca foi rápida (menos de 1 segundo)
        self.assertLess(execution_time, 1.0)
        self.assertIsNotNone(atendimento)

    def test_criacao_mensagens_bulk(self) -> None:
        """Testa a criação em lote de mensagens."""
        contato = Contato.objects.create(
            telefone="5511888888888",
            nome="Cliente Bulk"
        )
        
        atendimento = Atendimento.objects.create(
            contato=contato,
            status=StatusAtendimento.ATIVO
        )
        
        # Cria múltiplas mensagens
        mensagens = []
        for i in range(50):
            mensagem = Mensagem(
                atendimento=atendimento,
                tipo=TipoMensagem.TEXTO_FORMATADO,
                remetente=TipoRemetente.CONTATO if i % 2 == 0 else TipoRemetente.BOT,
                conteudo=f"Mensagem {i}",
                message_id_whatsapp=f"BULK_{i}"
            )
            mensagens.append(mensagem)
        
        # Testa criação em lote
        import time
        start_time = time.time()
        
        Mensagem.objects.bulk_create(mensagens)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verifica se a criação foi rápida
        self.assertLess(execution_time, 2.0)
        
        # Verifica se todas as mensagens foram criadas
        total_mensagens = Mensagem.objects.filter(atendimento=atendimento).count()
        self.assertEqual(total_mensagens, 50)