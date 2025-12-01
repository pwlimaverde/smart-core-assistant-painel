
import pytest
from django.core.exceptions import ValidationError
from smart_core_assistant_painel.app.ui.clientes.models import (
    Contato, Cliente, validate_telefone, validate_cnpj, validate_cpf, validate_cep
)

@pytest.mark.django_db
class TestClientesModels:
    def test_validators(self):
        validate_telefone("5511999999999")
        with pytest.raises(ValidationError):
            validate_telefone("123")
        with pytest.raises(ValidationError):
            validate_telefone("abc")

        validate_cnpj("12345678000199")
        with pytest.raises(ValidationError):
            validate_cnpj("123")
        with pytest.raises(ValidationError):
            validate_cnpj("00000000000000")

        validate_cpf("12345678901")
        with pytest.raises(ValidationError):
            validate_cpf("123")
        with pytest.raises(ValidationError):
            validate_cpf("00000000000")

        validate_cep("12345678")
        with pytest.raises(ValidationError):
            validate_cep("123")

    def test_contato_creation(self):
        c = Contato.objects.create(nome_contato="João Silva", telefone="11999999999")
        assert c.slug == "joao-silva"
        assert c.telefone == "5511999999999"
        assert str(c) == "João Silva (5511999999999)"

    def test_contato_slug_uniqueness(self):
        c1 = Contato.objects.create(nome_contato="João", telefone="11999999991")
        c2 = Contato.objects.create(nome_contato="João", telefone="11999999992")
        assert c1.slug == "joao"
        assert c2.slug == "joao-1"

    def test_cliente_creation(self):
        cli = Cliente.objects.create(
            nome_fantasia="Empresa X",
            cnpj="12345678000199",
            cpf="12345678901",
            cep="12345678",
            telefone="1133334444",
            uf="sp"
        )
        assert cli.slug == "empresa-x"
        assert cli.cnpj == "12.345.678/0001-99"
        assert cli.cpf == "123.456.789-01"
        assert cli.cep == "12345-678"
        assert cli.telefone == "(11) 3333-4444" # Formatted
        assert cli.uf == "SP"
        assert str(cli) == "Empresa X"

    def test_cliente_clean(self):
        cli = Cliente(nome_fantasia="")
        with pytest.raises(ValidationError):
            cli.clean()

    def test_cliente_endereco_completo(self):
        cli = Cliente.objects.create(
            nome_fantasia="Empresa Y",
            logradouro="Rua A",
            numero="100",
            complemento="Sala 1",
            bairro="Centro",
            cidade="São Paulo",
            uf="SP",
            cep="01000000",
            pais="Brasil"
        )
        end = cli.get_endereco_completo()
        assert "Rua A, 100, Sala 1" in end
        assert "Centro" in end
        assert "São Paulo - SP" in end
        assert "CEP: 01000-000" in end
        assert "Brasil" not in end # Default country omitted if logic matches

    def test_cliente_contatos(self):
        cli = Cliente.objects.create(nome_fantasia="Empresa Z")
        c = Contato.objects.create(nome_contato="Maria", telefone="11888888888")
        cli.adicionar_contato(c)
        assert c in cli.contatos.all()

        cli.remover_contato(c)
        assert c not in cli.contatos.all()

    def test_metadados(self):
        cli = Cliente.objects.create(nome_fantasia="Empresa W")
        cli.atualizar_metadados("k", "v")
        cli.refresh_from_db()
        assert cli.get_metadados("k") == "v"
