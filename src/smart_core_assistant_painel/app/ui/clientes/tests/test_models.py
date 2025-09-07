"""Testes para os modelos do app Clientes."""

from django.test import TestCase

from ..models import Cliente, Contato


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


class TestCliente(TestCase):
    """Testes para o modelo Cliente."""

    def setUp(self):
        """Configuração inicial."""
        self.contato = Contato.objects.create(
            telefone="11999999999", nome_contato="Contato Cliente"
        )

        self.cliente = Cliente.objects.create(
            nome_fantasia="Empresa Teste Ltda",
            razao_social="Empresa Teste Sociedade Limitada",
            tipo="juridica",
            cnpj="12.345.678/0001-99",
        )

    def test_cliente_creation(self):
        """Testa a criação de um cliente."""
        self.assertEqual(self.cliente.nome_fantasia, "Empresa Teste Ltda")
        self.assertEqual(
            self.cliente.razao_social, "Empresa Teste Sociedade Limitada"
        )
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
            nome_fantasia="João da Silva", tipo="fisica", cpf="123.456.789-00"
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
