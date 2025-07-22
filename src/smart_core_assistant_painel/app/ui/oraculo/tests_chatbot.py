"""
Testes para os modelos de chatbot
"""
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
    Atendimento,
    Contato,
    FluxoConversa,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    buscar_atendimento_ativo,
    inicializar_atendimento_whatsapp,
    processar_mensagem_whatsapp,
    validate_telefone,
)


class ValidateTelefoneTest(TestCase):
    """Testes para validação de telefone"""

    def test_telefone_valido(self) -> None:
        """Teste com telefone válido"""
        # Não deve gerar exceção
        validate_telefone("11999999999")
        validate_telefone("5511999999999")

    def test_telefone_muito_curto(self) -> None:
        """Teste com telefone muito curto"""
        with self.assertRaises(ValidationError):
            validate_telefone("123456789")

    def test_telefone_muito_longo(self) -> None:
        """Teste com telefone muito longo"""
        with self.assertRaises(ValidationError):
            validate_telefone("1234567890123456")

    def test_telefone_com_caracteres_especiais(self) -> None:
        """Teste com telefone contendo caracteres especiais"""
        with self.assertRaises(ValidationError):
            validate_telefone("11999999999abc")


class ContatoTest(TestCase):
    """Testes para o modelo Contato"""

    def test_criar_contato(self) -> None:
        """Teste de criação de contato"""
        contato = Contato.objects.create(
            telefone="11999999999",
            nome_contato="João Silva"
        )

        self.assertEqual(contato.telefone, "+5511999999999")
        self.assertEqual(contato.nome_contato, "João Silva")
        self.assertTrue(contato.ativo)

    def test_normalizacao_telefone(self) -> None:
        """Teste de normalização automática do telefone"""
        # Telefone sem código do país
        contato1 = Contato.objects.create(telefone="11999999999")
        self.assertEqual(contato1.telefone, "+5511999999999")

        # Telefone com código do país
        contato2 = Contato.objects.create(telefone="5511888888888")
        self.assertEqual(contato2.telefone, "+5511888888888")

        # Telefone com formatação
        contato3 = Contato.objects.create(telefone="(11) 99999-9999")
        self.assertEqual(contato3.telefone, "+5511999999999")

    def test_str_cliente(self) -> None:
        """Teste da representação string do contato"""
        contato = Contato.objects.create(
            telefone="11999999999",
            nome_contato="João Silva"
        )
        self.assertEqual(str(contato), "João Silva (+5511999999999)")

        # Contato sem nome
        contato_sem_nome = Contato.objects.create(telefone="11888888888")
        self.assertEqual(str(contato_sem_nome), "Contato (+5511888888888)")


class AtendimentoTest(TestCase):
    """Testes para o modelo Atendimento"""

    def setUp(self) -> None:
        """Configuração inicial para os testes"""
        self.contato = Contato.objects.create(
            telefone="11999999999",
            nome="João Silva"
        )

    def test_criar_atendimento(self) -> None:
        """Teste de criação de atendimento"""
        atendimento = Atendimento.objects.create(
            contato=self.contato,
            assunto="Dúvida sobre pedido"
        )

        self.assertEqual(atendimento.contato, self.contato)
        self.assertEqual(
            atendimento.status,
            StatusAtendimento.AGUARDANDO_INICIAL)
        self.assertEqual(atendimento.prioridade, 'normal')
        self.assertIsNone(atendimento.data_fim)

    def test_finalizar_atendimento(self) -> None:
        """Teste de finalização de atendimento"""
        atendimento = Atendimento.objects.create(contato=self.contato)

        # Verifica estado inicial
        self.assertIsNone(atendimento.data_fim)
        self.assertEqual(
            atendimento.status,
            StatusAtendimento.AGUARDANDO_INICIAL)

        # Finaliza atendimento
        atendimento.finalizar_atendimento(StatusAtendimento.RESOLVIDO)

        # Verifica estado final
        self.assertIsNotNone(atendimento.data_fim)
        self.assertEqual(atendimento.status, StatusAtendimento.RESOLVIDO)
        self.assertTrue(len(atendimento.historico_status) > 0)

    def test_atualizar_contexto(self) -> None:
        """Teste de atualização de contexto"""
        atendimento = Atendimento.objects.create(contato=self.contato)

        # Atualiza contexto
        atendimento.atualizar_contexto('numero_pedido', '12345')
        atendimento.atualizar_contexto('produto', 'Smartphone')

        # Verifica contexto
        self.assertEqual(atendimento.get_contexto('numero_pedido'), '12345')
        self.assertEqual(atendimento.get_contexto('produto'), 'Smartphone')
        self.assertIsNone(atendimento.get_contexto('inexistente'))

    def test_adicionar_historico_status(self) -> None:
        """Teste de adição ao histórico de status"""
        atendimento = Atendimento.objects.create(contato=self.contato)

        # Adiciona entrada no histórico
        atendimento.adicionar_historico_status(
            StatusAtendimento.EM_ANDAMENTO,
            "Iniciando atendimento"
        )

        # Verifica histórico
        self.assertEqual(len(atendimento.historico_status), 1)
        self.assertEqual(
            atendimento.historico_status[0]['status'],
            StatusAtendimento.EM_ANDAMENTO
        )
        self.assertEqual(
            atendimento.historico_status[0]['observacao'],
            "Iniciando atendimento"
        )


class MensagemTest(TestCase):
    """Testes para o modelo Mensagem"""

    def setUp(self) -> None:
        """Configuração inicial para os testes"""
        self.contato = Contato.objects.create(
            telefone="11999999999",
            nome="João Silva"
        )
        self.atendimento = Atendimento.objects.create(contato=self.contato)

    def test_criar_mensagem(self) -> None:
        """Teste de criação de mensagem"""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            conteudo="Olá! Preciso de ajuda.",
            is_from_client=True
        )

        self.assertEqual(mensagem.atendimento, self.atendimento)
        self.assertEqual(mensagem.conteudo, "Olá! Preciso de ajuda.")
        self.assertEqual(mensagem.tipo, TipoMensagem.TEXTO_FORMATADO)
        self.assertTrue(mensagem.is_from_client)
        self.assertFalse(mensagem.respondida)

    def test_marcar_como_respondida(self) -> None:
        """Teste de marcação como respondida"""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            conteudo="Preciso de ajuda",
            is_from_client=True
        )

        # Marca como respondida
        resposta = "Como posso ajudá-lo?"
        mensagem.marcar_como_respondida(resposta, confianca=0.95)

        # Verifica estado
        self.assertTrue(mensagem.respondida)
        self.assertEqual(mensagem.resposta_bot, resposta)
        self.assertEqual(mensagem.confianca_resposta, 0.95)

    def test_str_mensagem(self) -> None:
        """Teste da representação string da mensagem"""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            conteudo="Olá! Como posso ajudá-lo?",
            is_from_client=False
        )

        expected = "Bot/Atendente: Olá! Como posso ajudá-lo?"
        self.assertEqual(str(mensagem), expected)


class FluxoConversaTest(TestCase):
    """Testes para o modelo FluxoConversa"""

    def test_criar_fluxo(self) -> None:
        """Teste de criação de fluxo de conversa"""
        fluxo = FluxoConversa.objects.create(
            nome="Atendimento Básico",
            descricao="Fluxo básico de atendimento",
            condicoes_entrada={"intent": "saudacao"},
            estados={
                "inicio": {"mensagem": "Olá! Como posso ajudá-lo?"}
            }
        )

        self.assertEqual(fluxo.nome, "Atendimento Básico")
        self.assertTrue(fluxo.ativo)
        self.assertEqual(fluxo.condicoes_entrada["intent"], "saudacao")


class FuncoesUtilitariasTest(TestCase):
    """Testes para as funções utilitárias"""

    def test_inicializar_atendimento_whatsapp(self) -> None:
        """Teste de inicialização via WhatsApp"""
        telefone = "+5511999999999"
        primeira_mensagem = "Olá! Preciso de ajuda."
        nome = "João Silva"

        # Inicializa pela primeira vez
        cliente, atendimento = inicializar_atendimento_whatsapp(
            numero_telefone=telefone,
            primeira_mensagem=primeira_mensagem,
            nome_contato=nome
        )

        # Verifica cliente
        self.assertEqual(cliente.telefone, telefone)
        self.assertEqual(cliente.nome_contato, nome)

        # Verifica atendimento
        self.assertEqual(atendimento.contato, cliente)
        self.assertEqual(atendimento.status, StatusAtendimento.EM_ANDAMENTO)

        # Verifica mensagem
        mensagens = atendimento.mensagens.all()  # type: ignore
        self.assertEqual(mensagens.count(), 1)
        self.assertEqual(mensagens.first().conteudo, primeira_mensagem)

    def test_buscar_atendimento_ativo(self) -> None:
        """Teste de busca de atendimento ativo"""
        telefone = "+5511999999999"

        # Sem atendimento ativo
        atendimento = buscar_atendimento_ativo(telefone)
        self.assertIsNone(atendimento)

        # Cria contato e atendimento
        contato = Contato.objects.create(telefone=telefone)
        atendimento_ativo = Atendimento.objects.create(
            contato=contato,
            status=StatusAtendimento.EM_ANDAMENTO
        )

        # Busca atendimento ativo
        resultado = buscar_atendimento_ativo(telefone)
        self.assertEqual(resultado, atendimento_ativo)

        # Finaliza atendimento
        atendimento_ativo.finalizar_atendimento()

        # Não deve encontrar atendimento ativo
        resultado = buscar_atendimento_ativo(telefone)
        self.assertIsNone(resultado)

    def test_processar_mensagem_whatsapp(self) -> None:
        """Teste de processamento de mensagem do WhatsApp"""
        telefone = "+5511999999999"
        conteudo = "Preciso de ajuda com meu pedido"

        # Processa mensagem (cria novo atendimento)
        mensagem_id = processar_mensagem_whatsapp(
            numero_telefone=telefone,
            conteudo=conteudo
        )
        mensagem = Mensagem.objects.get(id=mensagem_id)

        # Verifica mensagem
        self.assertEqual(mensagem.conteudo, conteudo)
        self.assertTrue(mensagem.is_from_client)
        self.assertEqual(mensagem.tipo, TipoMensagem.TEXTO_FORMATADO)

        # Verifica contato e atendimento
        contato = mensagem.atendimento.contato  # type: ignore
        self.assertEqual(contato.telefone, telefone)

        # Processa segunda mensagem (usa atendimento existente)
        segunda_mensagem_id = processar_mensagem_whatsapp(
            numero_telefone=telefone,
            conteudo="Meu pedido é #12345"
        )
        segunda_mensagem = Mensagem.objects.get(id=segunda_mensagem_id)

        # Verifica que usa o mesmo atendimento
        self.assertEqual(
            segunda_mensagem.atendimento,
            mensagem.atendimento
        )

    def test_cliente_ja_existente(self) -> None:
        """Teste com contato já existente"""
        telefone = "+5511999999999"

        # Cria contato existente
        contato_existente = Contato.objects.create(
            telefone=telefone,
            nome="João Existente"
        )

        # Inicializa atendimento
        contato, atendimento = inicializar_atendimento_whatsapp(
            numero_telefone=telefone,
            primeira_mensagem="Nova mensagem",
            nome_contato="João Novo"
        )

        # Verifica que usa o contato existente
        self.assertEqual(contato, contato_existente)
        # Não sobrescreve nome existente
        self.assertEqual(contato.nome_contato, "João Existente")


class IntegracaoTest(TestCase):
    """Testes de integração entre componentes"""

    def test_fluxo_completo_atendimento(self) -> None:
        """Teste de fluxo completo de atendimento"""
        telefone = "+5511999999999"

        # 1. Primeira mensagem
        cliente, atendimento = inicializar_atendimento_whatsapp(
            numero_telefone=telefone,
            primeira_mensagem="Olá! Preciso de ajuda com meu pedido.",
            nome_contato="João Silva"
        )

        # 2. Mensagem subsequente
        mensagem2_id = processar_mensagem_whatsapp(
            numero_telefone=telefone,
            conteudo="Meu pedido é #12345"
        )
        mensagem2 = Mensagem.objects.get(id=mensagem2_id)

        # 3. Atualiza contexto
        atendimento.atualizar_contexto('numero_pedido', '12345')
        atendimento.atualizar_contexto('etapa', 'identificacao_pedido')

        # 4. Marca mensagem como respondida
        mensagem2.marcar_como_respondida(
            "Encontrei seu pedido #12345. Como posso ajudá-lo?"
        )

        # 5. Transfere para humano
        atendimento.status = StatusAtendimento.TRANSFERIDO
        atendimento.atendente_humano = "Maria Santos"
        atendimento.adicionar_historico_status(
            StatusAtendimento.TRANSFERIDO,
            "Transferido para atendente humano"
        )
        atendimento.save()

        # 6. Finaliza atendimento
        atendimento.avaliacao = 5
        atendimento.feedback = "Excelente atendimento!"
        atendimento.finalizar_atendimento(StatusAtendimento.RESOLVIDO)

        # Verificações finais
        self.assertEqual(atendimento.status, StatusAtendimento.RESOLVIDO)
        self.assertIsNotNone(atendimento.data_fim)
        self.assertEqual(atendimento.avaliacao, 5)
        self.assertEqual(atendimento.mensagens.count(), 2)  # type: ignore
        self.assertEqual(atendimento.get_contexto('numero_pedido'), '12345')
        self.assertTrue(len(atendimento.historico_status) >= 2)

    def test_multiplos_atendimentos_mesmo_cliente(self) -> None:
        """Teste de múltiplos atendimentos para o mesmo cliente"""
        telefone = "+5511999999999"

        # Primeiro atendimento
        cliente1, atendimento1 = inicializar_atendimento_whatsapp(
            numero_telefone=telefone,
            primeira_mensagem="Primeira dúvida",
            nome_contato="João Silva"
        )

        # Finaliza primeiro atendimento
        atendimento1.finalizar_atendimento()

        # Segundo atendimento (mesmo cliente)
        cliente2, atendimento2 = inicializar_atendimento_whatsapp(
            numero_telefone=telefone,
            primeira_mensagem="Segunda dúvida"
        )

        # Verifica que é o mesmo cliente
        self.assertEqual(cliente1, cliente2)
        # Mas atendimentos diferentes
        self.assertNotEqual(atendimento1, atendimento2)
        # Verifica que o novo atendimento está ativo
        self.assertEqual(atendimento2.status, StatusAtendimento.EM_ANDAMENTO)
