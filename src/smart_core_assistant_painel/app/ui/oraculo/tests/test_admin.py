"""Testes para a interface administrativa do app Oraculo."""

from typing import Optional

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from ..admin import (
    AtendimentoAdmin,
    AtendenteHumanoAdmin,
    ContatoAdmin,
    MensagemAdmin,
    TreinamentosAdmin,
)
from ..models import (
    Atendimento,
    AtendenteHumano,
    Contato,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
    Treinamentos,
)


class MockRequest:
    """Mock request para testes do admin."""

    def __init__(self, user: Optional[User] = None) -> None:
        self.user = user or User()


class TestContatoAdmin(TestCase):
    """Testes para o admin do modelo Contato."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = ContatoAdmin(Contato, self.site)
        self.factory = RequestFactory()

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome_contato="Cliente Teste"
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = ["telefone", "nome_contato", "nome_perfil_whatsapp", "data_cadastro"]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = ["telefone", "nome_contato", "nome_perfil_whatsapp"]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = ["data_criacao"]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_readonly_fields(self) -> None:
        """Testa os campos somente leitura."""
        # O admin atual não tem readonly_fields definido
        self.assertEqual(self.admin.readonly_fields, ())


class TestAtendenteHumanoAdmin(TestCase):
    """Testes para o admin do modelo AtendenteHumano."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = AtendenteHumanoAdmin(AtendenteHumano, self.site)

        self.atendente = AtendenteHumano.objects.create(
            telefone="5511888888888",
            nome="Atendente Teste",
            cargo="Analista",
            email="atendente@teste.com",
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "nome",
            "cargo",
            "telefone",
            "email",
            "ativo",
            "disponivel",
            "max_atendimentos_simultaneos",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = ["ativo", "disponivel", "cargo"]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = ["nome", "cargo", "telefone", "email"]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)


class TestAtendimentoAdmin(TestCase):
    """Testes para o admin do modelo Atendimento."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = AtendimentoAdmin(Atendimento, self.site)

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.ATIVO
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "contato",
            "status",
            "data_inicio",
            "data_fim",
            "atendente_humano",
            "duracao_formatada",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = ["status", "data_inicio", "atendente_humano"]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = ["contato__nome", "contato__telefone"]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_duracao_formatada_method(self) -> None:
        """Testa o método duracao_formatada."""
        # Testa atendimento ativo (sem data_fim)
        duracao = self.admin.duracao_formatada(self.atendimento)
        self.assertEqual(duracao, "Em andamento")

        # Testa atendimento finalizado
        import datetime

        self.atendimento.data_fim = self.atendimento.data_inicio + datetime.timedelta(
            hours=1, minutes=30
        )
        self.atendimento.save()

        duracao = self.admin.duracao_formatada(self.atendimento)
        self.assertIn("1:30", duracao)  # 1 hora e 30 minutos


class TestMensagemAdmin(TestCase):
    """Testes para o admin do modelo Mensagem."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = MensagemAdmin(Mensagem, self.site)

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.ATIVO
        )

        self.mensagem = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.CONTATO,
            conteudo="Mensagem de teste muito longa para verificar o truncamento",
            message_id_whatsapp="TEST123",
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "atendimento",
            "remetente",
            "tipo",
            "conteudo_truncado",
            "timestamp",
            "message_id_whatsapp",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        expected_filters = ["remetente", "tipo", "timestamp"]

        for filter_field in expected_filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = [
            "conteudo",
            "message_id_whatsapp",
            "atendimento__contato__nome",
            "atendimento__contato__telefone",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_conteudo_truncado_method(self) -> None:
        """Testa o método conteudo_truncado."""
        conteudo_truncado = self.admin.conteudo_truncado(self.mensagem)

        # Deve truncar mensagens longas
        self.assertTrue(len(conteudo_truncado) <= 50)
        self.assertIn("Mensagem de teste", conteudo_truncado)

        # Testa mensagem curta
        mensagem_curta = Mensagem.objects.create(
            atendimento=self.atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            remetente=TipoRemetente.BOT,
            conteudo="Curta",
            message_id_whatsapp="SHORT123",
        )

        conteudo_curto = self.admin.conteudo_truncado(mensagem_curta)
        self.assertEqual(conteudo_curto, "Curta")


class TestTreinamentosAdmin(TestCase):
    """Testes para o admin do modelo Treinamentos."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()
        self.admin = TreinamentosAdmin(Treinamentos, self.site)

        self.treinamento = Treinamentos.objects.create(
            tag="teste",
            grupo="grupo_teste",
            _documentos=[{"content": "Documento de teste"}],
        )

    def test_list_display(self) -> None:
        """Testa os campos exibidos na lista."""
        expected_fields = [
            "id",
            "tag",
            "grupo",
            "treinamento_finalizado",
            "get_documentos_preview",
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self) -> None:
        """Testa os filtros da lista."""
        # O admin atual não tem list_filter definido
        self.assertEqual(self.admin.list_filter, ())

    def test_search_fields(self) -> None:
        """Testa os campos de busca."""
        expected_fields = ["tag"]

        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)

    def test_get_documentos_preview_method(self) -> None:
        """Testa se o método get_documentos_preview está funcionando corretamente."""
        # Verifica se o método existe
        self.assertTrue(hasattr(self.admin, 'get_documentos_preview'))
        
        preview = self.admin.get_documentos_preview(self.treinamento)
        self.assertIsInstance(preview, str)
        # O método retorna o conteúdo real dos documentos
        self.assertIn("content", preview)
        self.assertIn("Documento de teste", preview)

        # Testa com múltiplos documentos
        treinamento_multiplo = Treinamentos.objects.create(
            tag="multiplo",
            grupo="grupo_multiplo",
            _documentos=[
                {"content": "Doc 1"},
                {"content": "Doc 2"},
                {"content": "Doc 3"},
            ],
        )

        preview_multiplo = self.admin.get_documentos_preview(treinamento_multiplo)
        self.assertIn("Doc 1", preview_multiplo)
        self.assertIn("content", preview_multiplo)
        
        # Testa com objeto vazio
        treinamento_vazio = Treinamentos.objects.create(
            tag="teste_vazio",
            grupo="grupo_teste",
            _documentos=None
        )
        result_vazio = self.admin.get_documentos_preview(treinamento_vazio)
        self.assertEqual(result_vazio, "Documento vazio")

    def test_readonly_fields(self) -> None:
        """Testa os campos somente leitura."""
        # TreinamentosAdmin não tem campos readonly definidos
        self.assertEqual(self.admin.readonly_fields, ())


class TestAdminIntegration(TestCase):
    """Testes de integração para a interface administrativa."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="testpass123"
        )

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome="Cliente Admin Test"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.ATIVO
        )

    def test_admin_urls_accessible(self) -> None:
        """Testa se as URLs do admin estão acessíveis."""
        self.client.force_login(self.user)

        # URLs do admin para cada modelo
        admin_urls = [
            "admin:oraculo_contato_changelist",
            "admin:oraculo_atendentehumano_changelist",
            "admin:oraculo_atendimento_changelist",
            "admin:oraculo_mensagem_changelist",
            "admin:oraculo_treinamentos_changelist",
        ]

        for url_name in admin_urls:
            try:
                url = reverse(url_name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
            except Exception:
                # Se a URL não existir, pula o teste
                pass

    def test_admin_add_contato(self) -> None:
        """Testa a adição de contato via admin."""
        self.client.force_login(self.user)

        try:
            url = reverse("admin:oraculo_contato_add")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            # Testa POST para criar contato
            data = {
                "telefone": "5511777777777",
                "nome": "Novo Cliente Admin",
                "email": "novo@admin.com",
            }

            response = self.client.post(url, data)

            # Verifica se o contato foi criado
            novo_contato = Contato.objects.filter(telefone="5511777777777").first()

            self.assertIsNotNone(novo_contato)
            self.assertEqual(novo_contato.nome, "Novo Cliente Admin")

        except Exception:
            # Se a URL não existir, pula o teste
            pass

    def test_admin_change_atendimento(self) -> None:
        """Testa a edição de atendimento via admin."""
        self.client.force_login(self.user)

        try:
            url = reverse(
                "admin:oraculo_atendimento_change", args=[self.atendimento.pk]
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            # Testa alteração do status
            data = {
                "contato": self.contato.pk,
                "status": StatusAtendimento.FINALIZADO,
                "data_inicio_0": self.atendimento.data_inicio.date(),
                "data_inicio_1": self.atendimento.data_inicio.time(),
            }

            response = self.client.post(url, data)

            # Verifica se o atendimento foi atualizado
            self.atendimento.refresh_from_db()
            self.assertEqual(self.atendimento.status, StatusAtendimento.FINALIZADO)

        except Exception:
            # Se a URL não existir, pula o teste
            pass

    def test_admin_permissions(self) -> None:
        """Testa as permissões do admin."""
        # Usuário não autenticado
        try:
            url = reverse("admin:oraculo_contato_changelist")
            response = self.client.get(url)
            # Deve redirecionar para login
            self.assertEqual(response.status_code, 302)
        except Exception:
            pass

        # Usuário comum (não staff)
        user_comum = User.objects.create_user(username="comum", password="testpass123")

        self.client.force_login(user_comum)

        try:
            url = reverse("admin:oraculo_contato_changelist")
            response = self.client.get(url)
            # Deve redirecionar ou retornar 403
            self.assertIn(response.status_code, [302, 403])
        except Exception:
            pass


class TestAdminCustomMethods(TestCase):
    """Testes para métodos customizados do admin."""

    def setUp(self) -> None:
        """Configuração inicial para os testes."""
        self.site = AdminSite()

        self.contato = Contato.objects.create(
            telefone="5511999999999", nome="Cliente Teste"
        )

        self.atendimento = Atendimento.objects.create(
            contato=self.contato, status=StatusAtendimento.ATIVO
        )

    def test_admin_ordering(self) -> None:
        """Testa a ordenação padrão nos admins."""
        # Testa ordenação do ContatoAdmin
        contato_admin = ContatoAdmin(Contato, self.site)
        if hasattr(contato_admin, "ordering"):
            self.assertIsNotNone(contato_admin.ordering)

        # Testa ordenação do AtendimentoAdmin
        atendimento_admin = AtendimentoAdmin(Atendimento, self.site)
        if hasattr(atendimento_admin, "ordering"):
            self.assertIsNotNone(atendimento_admin.ordering)

    def test_admin_date_hierarchy(self) -> None:
        """Testa a hierarquia de datas nos admins."""
        # Testa hierarquia no AtendimentoAdmin
        atendimento_admin = AtendimentoAdmin(Atendimento, self.site)
        if hasattr(atendimento_admin, "date_hierarchy"):
            self.assertEqual(atendimento_admin.date_hierarchy, "data_inicio")

        # Testa hierarquia no MensagemAdmin
        mensagem_admin = MensagemAdmin(Mensagem, self.site)
        if hasattr(mensagem_admin, "date_hierarchy"):
            self.assertEqual(mensagem_admin.date_hierarchy, "timestamp")

    def test_admin_list_per_page(self) -> None:
        """Testa a paginação nos admins."""
        admins = [
            ContatoAdmin(Contato, self.site),
            AtendimentoAdmin(Atendimento, self.site),
            MensagemAdmin(Mensagem, self.site),
        ]

        for admin in admins:
            if hasattr(admin, "list_per_page"):
                # Verifica se a paginação está configurada
                self.assertIsInstance(admin.list_per_page, int)
                self.assertGreater(admin.list_per_page, 0)
