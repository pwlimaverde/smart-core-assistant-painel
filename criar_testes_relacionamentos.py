"""
Script para criar clientes e contatos de teste com relacionamentos.

Este script cria dados de teste para validar a sincronização dos
relacionamentos many-to-many entre Clientes e Contatos no Notion.

Uso:
    uv run python criar_testes_relacionamentos.py
"""
import os
import sys
import argparse
from datetime import datetime
from typing import Any

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import django
django.setup()

from django.utils import timezone
from loguru import logger

from smart_core_assistant_painel.app.ui.clientes.models import Cliente, Contato


def criar_dados_teste() -> None:
    """Cria clientes e contatos de teste com relacionamentos."""
    logger.info("🚀 Iniciando criação de dados de teste...")

    try:
        # Limpar dados existentes (opcional)
        if Contato.objects.exists() or Cliente.objects.exists():
            logger.warning("⚠️ Já existem dados no sistema. Use --limpar para remover primeiro.")
            return

        # Criar Contatos de Teste
        logger.info("📝 Criando contatos de teste...")

        contato1 = Contato.objects.create(
            telefone="5511912345678",
            nome_contato="João Silva",
            email="joao.silva@empresa1.com.br",
            nome_perfil_whatsapp="João Silva",
            ativo=True
        )
        logger.info(f"✅ Contato criado: {contato1}")

        contato2 = Contato.objects.create(
            telefone="5511987654321",
            nome_contato="Maria Santos",
            email="maria.santos@empresa2.com.br",
            nome_perfil_whatsapp="Maria Santos",
            ativo=True
        )
        logger.info(f"✅ Contato criado: {contato2}")

        contato3 = Contato.objects.create(
            telefone="551155559999",
            nome_contato="Pedro Oliveira",
            email="pedro.oliveira@empresa1.com.br",
            nome_perfil_whatsapp="Pedro Oliveira",
            ativo=True
        )
        logger.info(f"✅ Contato criado: {contato3}")

        # Criar Clientes de Teste
        logger.info("🏢 Criando clientes de teste...")

        cliente1 = Cliente.objects.create(
            nome_fantasia="Empresa Tecnologia SA",
            razao_social="Empresa Tecnologia S.A.",
            tipo="juridica",
            cnpj="12.345.678/0001-99",
            telefone="(11) 5555-1234",
            site="https://empresatecnologia.com.br",
            ramo_atividade="Tecnologia da Informação",
            cep="01234-567",
            logradouro="Rua da Tecnologia",
            numero="100",
            complemento="Sala 1500",
            bairro="Vila Olímpia",
            cidade="São Paulo",
            uf="SP",
            observacoes="Cliente corporativo grande porte"
        )
        logger.info(f"✅ Cliente criado: {cliente1}")

        cliente2 = Cliente.objects.create(
            nome_fantasia="Comércio Local Ltda",
            razao_social="Comércio Local de Varejo Ltda",
            tipo="juridica",
            cnpj="98.765.432/0001-88",
            telefone="(11) 6666-9876",
            site="https://comerciolocal.com.br",
            ramo_atividade="Comércio Varejista",
            cep="04567-890",
            logradouro="Avenida do Comércio",
            numero="250",
            complemento="Loja B",
            bairro="Moema",
            cidade="São Paulo",
            uf="SP",
            observacoes="Cliente de médio porte, foco em varejo"
        )
        logger.info(f"✅ Cliente criado: {cliente2}")

        # Cliente do tipo Pessoa Física
        cliente3 = Cliente.objects.create(
            nome_fantasia="Ana Paula Costa",
            tipo="fisica",
            cpf="123.456.789-00",
            telefone="(11) 7777-4321",
            ramo_atividade="Consultoria",
            cep="05678-901",
            logradouro="Rua das Flores",
            numero="50",
            bairro="Pinheiros",
            cidade="São Paulo",
            uf="SP",
            observacoes="Cliente pessoa física, consultora independente"
        )
        logger.info(f"✅ Cliente criado: {cliente3}")

        # Criar Relacionamentos
        logger.info("🔗 Criando relacionamentos entre clientes e contatos...")

        # Empresa 1 tem dois contatos
        cliente1.contatos.add(contato1, contato3)
        logger.info(f"✅ {cliente1.nome_fantasia} vinculado a {cliente1.contatos.count()} contatos")

        # Empresa 2 tem um contato
        cliente2.contatos.add(contato2)
        logger.info(f"✅ {cliente2.nome_fantasia} vinculado a {cliente2.contatos.count()} contatos")

        # Cliente 3 (pessoa física) usa o mesmo contato como representante
        cliente3.contatos.add(contato2)
        logger.info(f"✅ {cliente3.nome_fantasia} vinculado a {cliente3.contatos.count()} contatos")

        # Verificar relacionamentos do lado dos contatos
        logger.info("📊 Verificando relacionamentos dos contatos...")

        contato1.refresh_from_db()
        contato2.refresh_from_db()
        contato3.refresh_from_db()

        logger.info(f"📞 {contato1.nome_contato} está vinculado a {contato1.clientes.count()} clientes:")
        for cliente in contato1.clientes.all():
            logger.info(f"   - {cliente.nome_fantasia}")

        logger.info(f"📞 {contato2.nome_contato} está vinculado a {contato2.clientes.count()} clientes:")
        for cliente in contato2.clientes.all():
            logger.info(f"   - {cliente.nome_fantasia}")

        logger.info(f"📞 {contato3.nome_contato} está vinculado a {contato3.clientes.count()} clientes:")
        for cliente in contato3.clientes.all():
            logger.info(f"   - {cliente.nome_fantasia}")

        # Adicionar metadados aos contatos para testar sync
        logger.info("📝 Adicionando metadados de teste...")

        contato1.metadados = {
            "principal": True,
            "cargo": "Gerente de TI",
            "departamento": "Tecnologia",
            "tags": ["cliente-premium", "tecnologia", "decisor"]
        }
        contato1.save()

        contato2.metadados = {
            "principal": True,
            "cargo": "Sócio-Diretor",
            "departamento": "Diretoria",
            "tags": ["cliente-novo", "varejo", "societario"]
        }
        contato2.save()

        contato3.metadados = {
            "principal": False,
            "cargo": "Analista de Suporte",
            "departamento": "Su Técnico",
            "tags": ["tecnologia", "suporte", "interno"]
        }
        contato3.save()

        # Adicionar metadados aos clientes
        logger.info("📝 Adicionando metadados aos clientes...")

        cliente1.metadados = {
            "segmento": "enterprise",
            "faturamento_anual": "10M+",
            "quantidade_funcionarios": 500,
            "tags": ["cliente-corporativo", "tecnologia", "grande-porte"]
        }
        cliente1.save()

        cliente2.metadados = {
            "segmento": "medium",
            "faturamento_anual": "1M-5M",
            "quantidade_funcionarios": 50,
            "tags": ["cliente-medio", "varejo", "crescimento"]
        }
        cliente2.save()

        cliente3.metadados = {
            "segmento": "individual",
            "profissao": "Consultora",
            "especialidade": "Gestão Empresarial",
            "tags": ["pessoa-fisica", "consultoria", "independente"]
        }
        cliente3.save()

        # Resumo final
        logger.info("🎉 Dados de teste criados com sucesso!")
        logger.info("📊 Resumo dos dados criados:")
        logger.info(f"   - Total de Contatos: {Contato.objects.count()}")
        logger.info(f"   - Total de Clientes: {Cliente.objects.count()}")
        logger.info(f"   - Cliente 1: {cliente1.nome_fantasia} ({cliente1.contatos.count()} contatos)")
        logger.info(f"   - Cliente 2: {cliente2.nome_fantasia} ({cliente2.contatos.count()} contatos)")
        logger.info(f"   - Cliente 3: {cliente3.nome_fantasia} ({cliente3.contatos.count()} contatos)")

        logger.info("💡 Próximos passos:")
        logger.info("   1. Verifique os registros de sincronização no admin do Django")
        logger.info("   2. Execute os testes de sincronização com: uv run task test-docker")
        logger.info("   3. Acompanhe os logs para ver se os relacionamentos são sincronizados")
        logger.info("   4. Verifique as databases no Notion para confirmar os relacionamentos")

    except Exception as e:
        logger.error(f"❌ Erro ao criar dados de teste: {e}")
        raise


def limpar_dados_teste() -> None:
    """Remove todos os dados de teste criados."""
    logger.info("🧹 Limpando dados de teste...")

    try:
        # Remover relacionamentos
        for cliente in Cliente.objects.all():
            cliente.contatos.clear()

        # Remover clientes
        clientes_removidos = Cliente.objects.count()
        Cliente.objects.all().delete()
        logger.info(f"✅ {clientes_removidos} clientes removidos")

        # Remover contatos
        contatos_removidos = Contato.objects.count()
        Contato.objects.all().delete()
        logger.info(f"✅ {contatos_removidos} contatos removidos")

        logger.info("🎉 Dados de teste removidos com sucesso!")

    except Exception as e:
        logger.error(f"❌ Erro ao limpar dados de teste: {e}")
        raise


def verificar_relacionamentos() -> None:
    """Verifica os relacionamentos existentes."""
    logger.info("🔍 Verificando relacionamentos existentes...")

    try:
        clientes = Cliente.objects.all()
        contatos = Contato.objects.all()

        logger.info(f"📊 Total de Clientes: {clientes.count()}")
        logger.info(f"📊 Total de Contatos: {contatos.count()}")

        for cliente in clientes:
            logger.info(f"🏢 {cliente.nome_fantasia}: {cliente.contatos.count()} contatos")
            for contato in cliente.contatos.all():
                logger.info(f"   📞 {contato.nome_contato} ({contato.telefone})")

        for contato in contatos:
            logger.info(f"📞 {contato.nome_contato}: {contato.clientes.count()} clientes")
            for cliente in contato.clientes.all():
                logger.info(f"   🏢 {cliente.nome_fantasia}")

    except Exception as e:
        logger.error(f"❌ Erro ao verificar relacionamentos: {e}")
        raise


def main() -> None:
    """Função principal."""
    parser = argparse.ArgumentParser(description="Script para testar relacionamentos Cliente-Contato")
    parser.add_argument(
        "--limpar",
        action="store_true",
        help="Remove todos os dados de teste"
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="Verifica os relacionamentos existentes"
    )
    parser.add_argument(
        "--criar",
        action="store_true",
        help="Cria dados de teste (ação padrão)"
    )

    args = parser.parse_args()

    if args.limpar:
        limpar_dados_teste()
    elif args.verificar:
        verificar_relacionamentos()
    else:
        # Padrão é criar
        criar_dados_teste()


if __name__ == "__main__":
    main()
