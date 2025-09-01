"""Testes para os modelos do app Oraculo."""

from unittest.mock import patch, MagicMock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from langchain.docstore.document import Document

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
    validate_tag,
    validate_telefone,
    validate_cnpj,
    validate_cpf,
)
from ..models_departamento import Departamento, validate_api_key, validate_telefone_instancia


class TestContato(TestCase):
    """Testes para o modelo Contato."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999",
            nome_contato="Cliente Teste",
            email="cliente@teste.com",
        )

    def test_contato_creation(self) -> None:
        """Testa a criação de um contato."""
        self.assertEqual(self.contato.telefone, "5511999999999")
        self.assertEqual(self.contato.nome_contato, "Cliente Teste")
        self.assertEqual(self.contato.email, "cliente@teste.com")
        self.assertEqual(str(self.contato), "Cliente Teste (5511999999999)")

    def test_contato_telefone_unique(self) -> None:
        """Testa se o telefone é único."""
        with self.assertRaises(Exception):
            Contato.objects.create(
                telefone="5511999999999", nome_contato="Outro Cliente"
            )


class TestAtendenteHumano(TestCase):
    """Testes para o modelo AtendenteHumano."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.atendente = AtendenteHumano.objects.create(
            telefone="5511888888888",
            nome="Atendente Teste",
            cargo="Analista",
            email="atendente@teste.com",
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
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.EM_ANDAMENTO
        )

    def test_atendimento_creation(self) -> None:
        """Testa a criação de um atendimento."""
        self.assertEqual(self.atendimento.contato, self.contato)
        self.assertEqual(self.atendimento.status, StatusAtendimento.EM_ANDAMENTO)
        self.assertIsNotNone(self.atendimento.data_inicio)
        self.assertIsNone(self.atendimento.data_fim)

    def test_atendimento_finalizacao(self) -> None:
        """Testa a finalização de um atendimento."""
        self.atendimento.status = StatusAtendimento.RESOLVIDO
        self.atendimento.data_fim = timezone.now()
        self.atendimento.save()

        self.assertEqual(self.atendimento.status, StatusAtendimento.RESOLVIDO)
        self.assertIsNotNone(self.atendimento.data_fim)


class TestMensagem(TestCase):
    """Testes para o modelo Mensagem."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.EM_ANDAMENTO
        )

    def test_mensagem_creation(self) -> None:
        """Testa a criação de uma mensagem."""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Mensagem de teste",
            message_id_whatsapp="TEST123",
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
            conteudo="Resposta do bot",
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
            _documentos=[{"content": "Documento de teste"}],
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
            treinamento_finalizado=True,
        )

        self.assertTrue(treinamento.treinamento_finalizado)

    def test_clear_all_data(self) -> None:
        """Testa a limpeza completa dos dados de um treinamento."""
        treinamento = Treinamentos.objects.create(
            tag="teste_clear",
            grupo="grupo_teste",
            _documentos=[{"content": "Documento teste"}],
            treinamento_finalizado=True,
            treinamento_vetorizado=True,
        )

        # Verifica que os dados estão lá
        self.assertEqual(len(treinamento.documentos), 1)
        self.assertTrue(treinamento.treinamento_finalizado)
        self.assertTrue(treinamento.treinamento_vetorizado)

        # Limpa todos os dados
        treinamento.clear_all_data()

        # Verifica que tudo foi limpo
        self.assertEqual(len(treinamento.documentos), 0)
        self.assertFalse(treinamento.treinamento_finalizado)
        self.assertFalse(treinamento.treinamento_vetorizado)
        self.assertIsNone(treinamento.embedding)


class TestUtilityFunctions(TestCase):
    """Testes para as funções utilitárias dos modelos."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.EM_ANDAMENTO
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
        self.atendimento.status = StatusAtendimento.RESOLVIDO
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

        # A função normaliza o telefone para formato sem prefixo '+' (55...)
        self.assertEqual(contato.telefone, "5511777777777")
        self.assertEqual(contato.nome_perfil_whatsapp, nome_perfil)
        self.assertEqual(atendimento.contato, contato)
        self.assertEqual(atendimento.status, StatusAtendimento.EM_ANDAMENTO)

    def test_inicializar_atendimento_contato_existente(self) -> None:
        """Testa inicialização com contato já existente."""
        telefone = "5511999999999"  # Contato já existe no setUp
        conteudo = "Nova mensagem"

        contato, atendimento = inicializar_atendimento_whatsapp(telefone, conteudo)

        # Deve retornar o contato existente
        self.assertEqual(contato, self.contato)
        # Deve reutilizar o atendimento ativo existente (não criar novo)
        self.assertEqual(atendimento, self.atendimento)
        self.assertEqual(atendimento.status, StatusAtendimento.EM_ANDAMENTO)


class TestModelPerformance(TestCase):
    """Testes de performance para operações críticas dos modelos."""

    def test_busca_atendimento_ativo_performance(self) -> None:
        """Testa a performance da busca de atendimento ativo."""
        # Cria múltiplos contatos e atendimentos
        contatos = []
        for i in range(100):
            contato = Contato.objects.create(
                telefone=f"551199999{i:04d}", nome_contato=f"Cliente {i}"
            )
            contatos.append(contato)

            Atendimento.objects.create(
                contato=contato,
                status=StatusAtendimento.EM_ANDAMENTO
                if i % 2 == 0
                else StatusAtendimento.RESOLVIDO,
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
            telefone="5511888888888", nome_contato="Cliente Bulk"
        )

        atendimento = Atendimento.objects.create(
            contato=contato, status=StatusAtendimento.EM_ANDAMENTO
        )

        # Cria múltiplas mensagens
        mensagens = []
        for i in range(50):
            mensagem = Mensagem(
                atendimento=atendimento,
                tipo=TipoMensagem.TEXTO_FORMATADO,
                remetente=TipoRemetente.CONTATO if i % 2 == 0 else TipoRemetente.BOT,
                conteudo=f"Mensagem {i}",
                message_id_whatsapp=f"BULK_{i}",
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


class TestValidators(TestCase):
    """Testes para os validadores dos modelos."""

    def test_validate_tag(self):
        """Testa o validador de tags."""
        # Tags válidas
        validate_tag("tag_valida")
        validate_tag("tag123")
        validate_tag("test_tag_123")
        
        # Tags inválidas
        with self.assertRaises(ValidationError):
            validate_tag("Tag com maiúscula")
        
        with self.assertRaises(ValidationError):
            validate_tag("tag com espaço")
            
        with self.assertRaises(ValidationError):
            validate_tag("a" * 41)  # Muito longo
            
        with self.assertRaises(ValidationError):
            validate_tag("tag-com-traço")

    def test_validate_telefone(self):
        """Testa o validador de telefone."""
        # Telefones válidos
        validate_telefone("11999999999")
        validate_telefone("+5511999999999")
        validate_telefone("(11) 99999-9999")
        
        # Telefones inválidos
        with self.assertRaises(ValidationError):
            validate_telefone("123")  # Muito curto
            
        with self.assertRaises(ValidationError):
            validate_telefone("1" * 16)  # Muito longo

    def test_validate_cnpj(self):
        """Testa o validador de CNPJ."""
        # CNPJ válidos
        validate_cnpj("12.345.678/0001-99")
        validate_cnpj("12345678000199")
        
        # CNPJ inválidos
        with self.assertRaises(ValidationError):
            validate_cnpj("123")  # Muito curto
            
        with self.assertRaises(ValidationError):
            validate_cnpj("00000000000000")  # CNPJ inválido conhecido
            
        # Deve aceitar valor vazio
        validate_cnpj("")
        validate_cnpj(None)

    def test_validate_cpf(self):
        """Testa o validador de CPF."""
        # CPF válidos
        validate_cpf("123.456.789-00")
        validate_cpf("12345678900")
        
        # CPF inválidos
        with self.assertRaises(ValidationError):
            validate_cpf("123")  # Muito curto
            
        with self.assertRaises(ValidationError):
            validate_cpf("00000000000")  # CPF inválido conhecido
            
        # Deve aceitar valor vazio
        validate_cpf("")
        validate_cpf(None)

    def test_validate_api_key(self):
        """Testa o validador de chave de API."""
        # Chaves válidas
        validate_api_key("chave123456")
        validate_api_key("api_key_muito_longa")
        
        # Chaves inválidas
        with self.assertRaises(ValidationError):
            validate_api_key("")  # Vazia
            
        with self.assertRaises(ValidationError):
            validate_api_key("curta")  # Muito curta

    def test_validate_telefone_instancia(self):
        """Testa o validador de telefone de instância."""
        # Telefones válidos
        validate_telefone_instancia("11999999999")
        validate_telefone_instancia("+55 (11) 99999-9999")
        
        # Telefones inválidos
        with self.assertRaises(ValidationError):
            validate_telefone_instancia("")  # Vazio
            
        with self.assertRaises(ValidationError):
            validate_telefone_instancia("123")  # Muito curto
            
        with self.assertRaises(ValidationError):
            validate_telefone_instancia("1" * 16)  # Muito longo


class TestTreinamentosAdvanced(TestCase):
    """Testes avançados para o modelo Treinamentos."""

    def setUp(self):
        """Configuração inicial."""
        self.treinamento = Treinamentos.objects.create(
            tag="teste_avancado",
            grupo="grupo_avancado"
        )

    def test_clean_validation_tag_igual_grupo(self):
        """Testa validação que impede tag igual ao grupo."""
        with self.assertRaises(ValidationError):
            treinamento = Treinamentos(
                tag="mesma_tag",
                grupo="mesma_tag"
            )
            treinamento.full_clean()

    def test_save_calls_full_clean(self):
        """Testa que o método save chama full_clean."""
        with patch.object(Treinamentos, 'full_clean') as mock_clean:
            treinamento = Treinamentos(
                tag="save_test",
                grupo="grupo_save"
            )
            treinamento.save()
            mock_clean.assert_called_once()

    def test_str_representation(self):
        """Testa a representação string do treinamento."""
        self.assertEqual(str(self.treinamento), "teste_avancado")
        
        # Testa com treinamento sem tag (criado diretamente no banco)
        treinamento_sem_tag = Treinamentos.objects.create(
            tag="tag_temp",
            grupo="grupo_temp"
        )
        # Define tag como None após salvar
        treinamento_sem_tag.tag = None
        result = str(treinamento_sem_tag)
        self.assertTrue(result.startswith("Treinamento"))

    def test_set_documentos_valid(self):
        """Testa a adição de documentos válidos."""
        docs = [
            Document(page_content="Texto 1", metadata={"source": "doc1.txt"}),
            Document(page_content="Texto 2", metadata={"source": "doc2.txt"})
        ]
        
        self.treinamento.set_documentos(docs)
        self.assertEqual(len(self.treinamento._documentos), 2)

    def test_set_documentos_empty_list(self):
        """Testa a adição de lista vazia de documentos."""
        self.treinamento.set_documentos([])
        self.assertEqual(self.treinamento._documentos, [])

    def test_set_documentos_invalid_type(self):
        """Testa erro ao adicionar item inválido."""
        with self.assertRaises(TypeError):
            self.treinamento.set_documentos(["not_a_document"])

    def test_get_documentos_empty(self):
        """Testa get_documentos com lista vazia."""
        docs = self.treinamento.get_documentos()
        self.assertEqual(docs, [])

    def test_get_documentos_with_json_error(self):
        """Testa get_documentos com erro de JSON."""
        self.treinamento._documentos = ["invalid_json"]
        self.treinamento.save()
        
        with patch('smart_core_assistant_painel.app.ui.oraculo.models.logger') as mock_logger:
            docs = self.treinamento.get_documentos()
            self.assertEqual(docs, [])
            mock_logger.error.assert_called()

    def test_get_conteudo_unificado_empty(self):
        """Testa get_conteudo_unificado com documentos vazios."""
        resultado = self.treinamento.get_conteudo_unificado()
        self.assertEqual(resultado, "")

    def test_get_conteudo_unificado_with_content(self):
        """Testa get_conteudo_unificado com conteúdo."""
        self.treinamento._documentos = [
            '{"page_content": "Conteúdo 1"}',
            '{"page_content": "Conteúdo 2"}'
        ]
        self.treinamento.save()
        
        resultado = self.treinamento.get_conteudo_unificado()
        self.assertIn("Conteúdo 1", resultado)
        self.assertIn("Conteúdo 2", resultado)
        self.assertIn("\n\n", resultado)  # Separador

    def test_finalize(self):
        """Testa o método finalize."""
        self.assertFalse(self.treinamento.treinamento_finalizado)
        self.treinamento.finalize()
        self.treinamento.refresh_from_db()
        self.assertTrue(self.treinamento.treinamento_finalizado)

    def test_documentos_property(self):
        """Testa a propriedade documentos para compatibilidade."""
        test_docs = [{"content": "test"}]
        self.treinamento._documentos = test_docs
        self.assertEqual(self.treinamento.documentos, test_docs)

    @patch('smart_core_assistant_painel.app.ui.oraculo.models.SERVICEHUB')
    def test_embed_text_with_embed_query(self, mock_servicehub):
        """Testa _embed_text usando embed_query."""
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
        
        with patch.object(Treinamentos, '_get_embeddings_instance', return_value=mock_embeddings):
            result = Treinamentos._embed_text("texto teste")
            self.assertEqual(result, [0.1, 0.2, 0.3])
            mock_embeddings.embed_query.assert_called_once_with("texto teste")

    @patch('smart_core_assistant_painel.app.ui.oraculo.models.SERVICEHUB')
    def test_embed_text_with_embed_documents(self, mock_servicehub):
        """Testa _embed_text usando embed_documents como fallback."""
        mock_embeddings = MagicMock()
        del mock_embeddings.embed_query  # Remove o método para forçar fallback
        mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        
        with patch.object(Treinamentos, '_get_embeddings_instance', return_value=mock_embeddings):
            result = Treinamentos._embed_text("texto teste")
            self.assertEqual(result, [0.1, 0.2, 0.3])
            mock_embeddings.embed_documents.assert_called_once_with(["texto teste"])

    def test_cosine_distance(self):
        """Testa o cálculo de distância cosseno."""
        # Vetores idênticos devem ter distância 0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        dist = Treinamentos._cosine_distance(vec1, vec2)
        self.assertAlmostEqual(dist, 0.0, places=5)
        
        # Vetores ortogonais devem ter distância 1
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]
        dist = Treinamentos._cosine_distance(vec3, vec4)
        self.assertAlmostEqual(dist, 1.0, places=5)
        
        # Vetores vazios devem retornar 1.0
        dist = Treinamentos._cosine_distance([], [])
        self.assertEqual(dist, 1.0)
        
        # Vetores com norma zero devem retornar 1.0
        dist = Treinamentos._cosine_distance([0.0, 0.0], [1.0, 1.0])
        self.assertEqual(dist, 1.0)

    def test_search_by_similarity_empty_query(self):
        """Testa busca por similaridade com query vazia."""
        result = Treinamentos.search_by_similarity("")
        self.assertEqual(result, [])
        
        result = Treinamentos.search_by_similarity("   ")
        self.assertEqual(result, [])

    def test_search_by_similarity_invalid_top_k(self):
        """Testa busca por similaridade com top_k inválido."""
        result = Treinamentos.search_by_similarity("query", top_k=0)
        self.assertEqual(result, [])
        
        result = Treinamentos.search_by_similarity("query", top_k=-1)
        self.assertEqual(result, [])

    def test_build_similarity_context_empty_params(self):
        """Testa build_similarity_context com parâmetros vazios."""
        result = Treinamentos.build_similarity_context("")
        self.assertEqual(result, "")
        
        result = Treinamentos.build_similarity_context("query", top_k_docs=0)
        self.assertEqual(result, "")
        
        result = Treinamentos.build_similarity_context("query", top_k_trainings=0)
        self.assertEqual(result, "")


class TestDepartamento(TestCase):
    """Testes para o modelo Departamento."""

    def setUp(self):
        """Configuração inicial."""
        self.departamento = Departamento.objects.create(
            nome="Departamento Teste",
            telefone_instancia="11999999999",
            api_key="chave_teste_12345"
        )

    def test_departamento_creation(self):
        """Testa a criação de um departamento."""
        self.assertEqual(self.departamento.nome, "Departamento Teste")
        self.assertEqual(self.departamento.telefone_instancia, "11999999999")
        self.assertEqual(self.departamento.api_key, "chave_teste_12345")
        self.assertTrue(self.departamento.ativo)

    def test_departamento_str_representation(self):
        """Testa a representação string do departamento."""
        expected = "Departamento Teste (11999999999)"
        self.assertEqual(str(self.departamento), expected)

    def test_departamento_save_normalizes_phone(self):
        """Testa que o save normaliza o telefone."""
        dept = Departamento(
            nome="Teste Normalização",
            telefone_instancia="+55 (11) 99999-9999",
            api_key="chave_normalizar_123"
        )
        dept.save()
        self.assertEqual(dept.telefone_instancia, "5511999999999")

    def test_departamento_clean_validates_api_key(self):
        """Testa que clean valida a API key."""
        dept = Departamento(
            nome="Teste Validação",
            telefone_instancia="11999999999",
            api_key="curta"  # API key muito curta
        )
        with self.assertRaises(ValidationError):
            dept.clean()

    def test_get_atendentes_ativos(self):
        """Testa get_atendentes_ativos."""
        # Cria atendente ativo
        atendente_ativo = AtendenteHumano.objects.create(
            nome="Atendente Ativo",
            cargo="Analista",
            telefone="11888888888",
            departamento=self.departamento,
            ativo=True
        )
        
        # Cria atendente inativo
        AtendenteHumano.objects.create(
            nome="Atendente Inativo",
            cargo="Analista",
            telefone="11777777777",
            departamento=self.departamento,
            ativo=False
        )
        
        atendentes = self.departamento.get_atendentes_ativos()
        self.assertEqual(atendentes.count(), 1)
        self.assertEqual(atendentes.first(), atendente_ativo)

    def test_get_atendentes_disponiveis(self):
        """Testa get_atendentes_disponiveis."""
        # Cria atendente disponível
        atendente_disponivel = AtendenteHumano.objects.create(
            nome="Atendente Disponível",
            cargo="Analista",
            telefone="11888888888",
            departamento=self.departamento,
            ativo=True,
            disponivel=True
        )
        
        # Cria atendente indisponível
        AtendenteHumano.objects.create(
            nome="Atendente Indisponível",
            cargo="Analista",
            telefone="11777777777",
            departamento=self.departamento,
            ativo=True,
            disponivel=False
        )
        
        atendentes = self.departamento.get_atendentes_disponiveis()
        self.assertEqual(atendentes.count(), 1)
        self.assertEqual(atendentes.first(), atendente_disponivel)

    def test_atualizar_configuracao(self):
        """Testa atualizar_configuracao."""
        self.departamento.atualizar_configuracao("timeout", 30)
        self.departamento.refresh_from_db()
        self.assertEqual(self.departamento.configuracoes["timeout"], 30)
        
        # Testa com configuracoes vazio
        dept = Departamento.objects.create(
            nome="Teste Config Vazio",
            telefone_instancia="11888888888",
            api_key="chave_config_vazio_123"
        )
        # O método atualizar_configuracao deve funcionar mesmo com dict vazio
        dept.configuracoes = {}
        dept.save()
        dept.atualizar_configuracao("nova_config", "valor")
        dept.refresh_from_db()
        self.assertEqual(dept.configuracoes["nova_config"], "valor")

    def test_get_configuracao(self):
        """Testa get_configuracao."""
        self.departamento.configuracoes = {"timeout": 30}
        self.departamento.save()
        
        # Testa configuração existente
        valor = self.departamento.get_configuracao("timeout")
        self.assertEqual(valor, 30)
        
        # Testa configuração inexistente
        valor = self.departamento.get_configuracao("inexistente", "padrão")
        self.assertEqual(valor, "padrão")
        
        # Testa com configuracoes vazio
        self.departamento.configuracoes = {}
        self.departamento.save()
        valor = self.departamento.get_configuracao("qualquer", "padrão")
        self.assertEqual(valor, "padrão")

    def test_buscar_por_api_key(self):
        """Testa buscar_por_api_key."""
        result = Departamento.buscar_por_api_key("chave_teste_12345")
        self.assertEqual(result, self.departamento)
        
        # Testa com chave inexistente
        with patch('smart_core_assistant_painel.app.ui.oraculo.models_departamento.logger') as mock_logger:
            result = Departamento.buscar_por_api_key("chave_inexistente")
            self.assertIsNone(result)
            mock_logger.warning.assert_called()

    def test_buscar_por_telefone_instancia(self):
        """Testa buscar_por_telefone_instancia."""
        result = Departamento.buscar_por_telefone_instancia("11999999999")
        self.assertEqual(result, self.departamento)
        
        # Testa com telefone formatado (mesmo padrão, sem +55)
        result = Departamento.buscar_por_telefone_instancia("(11) 99999-9999")
        self.assertEqual(result, self.departamento)
        
        # Testa com telefone inexistente
        with patch('smart_core_assistant_painel.app.ui.oraculo.models_departamento.logger') as mock_logger:
            result = Departamento.buscar_por_telefone_instancia("11000000000")
            self.assertIsNone(result)
            mock_logger.warning.assert_called()

    def test_validar_api_key_method(self):
        """Testa validar_api_key."""
        data = {
            "apikey": "chave_teste_12345",
            "instance": "11999999999"
        }
        result = Departamento.validar_api_key(data)
        self.assertEqual(result, self.departamento)
        
        # Testa sem api_key
        data_sem_key = {"instance": "11999999999"}
        with patch('smart_core_assistant_painel.app.ui.oraculo.models_departamento.logger') as mock_logger:
            result = Departamento.validar_api_key(data_sem_key)
            self.assertIsNone(result)
            mock_logger.warning.assert_called()
        
        # Testa sem instance
        data_sem_instance = {"apikey": "chave_teste_12345"}
        with patch('smart_core_assistant_painel.app.ui.oraculo.models_departamento.logger') as mock_logger:
            result = Departamento.validar_api_key(data_sem_instance)
            self.assertIsNone(result)
            mock_logger.warning.assert_called()
        
        # Testa com dados inválidos
        data_invalida = {
            "apikey": "chave_inexistente",
            "instance": "11000000000"
        }
        with patch('smart_core_assistant_painel.app.ui.oraculo.models_departamento.logger') as mock_logger:
            result = Departamento.validar_api_key(data_invalida)
            self.assertIsNone(result)
            mock_logger.warning.assert_called()


class TestCliente(TestCase):
    """Testes para o modelo Cliente."""

    def setUp(self):
        """Configuração inicial."""
        self.contato = Contato.objects.create(
            telefone="11999999999",
            nome_contato="Contato Cliente"
        )
        
        self.cliente = Cliente.objects.create(
            nome_fantasia="Empresa Teste Ltda",
            razao_social="Empresa Teste Sociedade Limitada",
            tipo="juridica",
            cnpj="12.345.678/0001-99"
        )
        
    def test_cliente_creation(self):
        """Testa a criação de um cliente."""
        self.assertEqual(self.cliente.nome_fantasia, "Empresa Teste Ltda")
        self.assertEqual(self.cliente.razao_social, "Empresa Teste Sociedade Limitada")
        self.assertEqual(self.cliente.tipo, "juridica")
        self.assertEqual(self.cliente.cnpj, "12.345.678/0001-99")
        self.assertTrue(self.cliente.ativo)
        
    def test_cliente_str_representation(self):
        """Testa a representação string do cliente."""
        expected = "Empresa Teste Ltda"
        self.assertEqual(str(self.cliente), expected)
        
    def test_cliente_pessoa_fisica(self):
        """Testa cliente pessoa física."""
        pf = Cliente.objects.create(
            nome_fantasia="João da Silva",
            tipo="fisica",
            cpf="123.456.789-00"
        )
        self.assertEqual(pf.tipo, "fisica")
        self.assertEqual(pf.cpf, "123.456.789-00")
        
    def test_cliente_contatos_relacionamento(self):
        """Testa o relacionamento many-to-many com contatos."""
        self.cliente.contatos.add(self.contato)
        self.assertEqual(self.cliente.contatos.count(), 1)
        self.assertIn(self.contato, self.cliente.contatos.all())
        
        # Testa o relacionamento reverso
        self.assertIn(self.cliente, self.contato.clientes.all())


class TestFluxoConversa(TestCase):
    """Testes para o modelo FluxoConversa."""
    
    def setUp(self):
        """Configuração inicial."""
        self.fluxo = FluxoConversa.objects.create(
            nome="Fluxo Atendimento Básico",
            descricao="Fluxo para atendimento básico de clientes",
            condicoes_entrada={"tipo": "novo_cliente"},
            estados={
                "inicio": {"mensagem": "Olá! Como posso ajudar?"},
                "aguardando_resposta": {"timeout": 300}
            }
        )
        
    def test_fluxo_conversa_creation(self):
        """Testa a criação de um fluxo de conversa."""
        self.assertEqual(self.fluxo.nome, "Fluxo Atendimento Básico")
        self.assertEqual(self.fluxo.descricao, "Fluxo para atendimento básico de clientes")
        self.assertEqual(self.fluxo.condicoes_entrada["tipo"], "novo_cliente")
        self.assertTrue(self.fluxo.ativo)
        
    def test_fluxo_conversa_str_representation(self):
        """Testa a representação string do fluxo."""
        expected = "Fluxo Atendimento Básico"
        self.assertEqual(str(self.fluxo), expected)
        
    def test_fluxo_conversa_estados_complexos(self):
        """Testa estados mais complexos."""
        self.assertIn("inicio", self.fluxo.estados)
        self.assertIn("aguardando_resposta", self.fluxo.estados)
        self.assertEqual(self.fluxo.estados["inicio"]["mensagem"], "Olá! Como posso ajudar?")


class TestMensagemAdvanced(TestCase):
    """Testes avançados para o modelo Mensagem."""
    
    def setUp(self):
        """Configuração inicial."""
        self.contato = Contato.objects.create(
            telefone="11999999999",
            nome_contato="Cliente Teste Avançado"
        )
        
        self.atendimento = Atendimento.objects.create(
            contato=self.contato,
            status=StatusAtendimento.EM_ANDAMENTO
        )
        
    def test_mensagem_diferentes_tipos(self):
        """Testa diferentes tipos de mensagem."""
        # Mensagem de áudio
        msg_audio = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.AUDIO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Audio message",
            metadados={
                "duracao": 30,
                "formato": "mp3"
            }
        )
        self.assertEqual(msg_audio.tipo, TipoMensagem.AUDIO)
        self.assertEqual(msg_audio.metadados["duracao"], 30)
        
        # Mensagem de imagem
        msg_img = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.IMAGEM,
            remetente=TipoRemetente.CONTATO,
            conteudo="Image caption",
            metadados={
                "url": "https://example.com/image.jpg",
                "tamanho": "1024x768"
            }
        )
        self.assertEqual(msg_img.tipo, TipoMensagem.IMAGEM)
        self.assertEqual(msg_img.metadados["url"], "https://example.com/image.jpg")
        
    def test_mensagem_intent_e_entidades(self):
        """Testa detecção de intents e entidades."""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Meu nome é João e preciso de ajuda com meu pedido",
            intent_detectado=[
                {"saudacao": 0.8},
                {"solicitar_ajuda": 0.9}
            ],
            entidades_extraidas=[
                {"pessoa": "João"},
                {"assunto": "pedido"}
            ],
            confianca_resposta=0.85
        )
        
        self.assertEqual(len(mensagem.intent_detectado), 2)
        self.assertEqual(len(mensagem.entidades_extraidas), 2)
        self.assertEqual(mensagem.confianca_resposta, 0.85)
        self.assertIn({"pessoa": "João"}, mensagem.entidades_extraidas)
        
    def test_mensagem_resposta_bot(self):
        """Testa mensagem com resposta do bot."""
        mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Qual o status do meu pedido?",
            respondida=True,
            resposta_bot="Seu pedido está em processo de separação. Prazo de entrega: 2 dias úteis."
        )
        
        self.assertTrue(mensagem.respondida)
        self.assertIn("separação", mensagem.resposta_bot)
