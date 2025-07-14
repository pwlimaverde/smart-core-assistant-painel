#!/usr/bin/env python3
"""
Exemplo de uso do novo modelo AtendenteHumano
===========================================

Este script demonstra como usar a nova entidade AtendenteHumano
que substitui o campo simples 'atendente_humano' no modelo Atendimento.

Funcionalidades implementadas:
- Criação e gerenciamento de atendentes humanos
- Transferência automática de atendimentos
- Controle de disponibilidade e capacidade
- Busca por especialidades e departamentos
"""

import os
import sys

import django
from oraculo.models import (
    AtendenteHumano,
    Atendimento,
    Cliente,
    StatusAtendimento,
    buscar_atendente_disponivel,
    listar_atendentes_por_disponibilidade,
    transferir_atendimento_automatico,
)

# Adiciona o path do Django
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        'src',
        'smart_core_assistant_painel',
        'app',
        'ui'))

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')


django.setup()


def criar_atendentes_exemplo():
    """Cria alguns atendentes de exemplo"""

    print("🔧 Criando atendentes de exemplo...")

    # Atendente 1 - Suporte Técnico
    atendente1, created = AtendenteHumano.objects.get_or_create(
        telefone="+5511999999001",
        defaults={
            'nome': 'João Silva',
            'cargo': 'Analista de Suporte',
            'departamento': 'Suporte Técnico',
            'email': 'joao.silva@empresa.com',
            'especialidades': ['suporte_tecnico', 'troubleshooting', 'hardware'],
            'max_atendimentos_simultaneos': 3,
            'horario_trabalho': {
                'segunda': '08:00-18:00',
                'terca': '08:00-18:00',
                'quarta': '08:00-18:00',
                'quinta': '08:00-18:00',
                'sexta': '08:00-17:00'
            }
        }
    )

    # Atendente 2 - Vendas
    atendente2, created = AtendenteHumano.objects.get_or_create(
        telefone="+5511999999002",
        defaults={
            'nome': 'Maria Santos',
            'cargo': 'Consultora de Vendas',
            'departamento': 'Vendas',
            'email': 'maria.santos@empresa.com',
            'especialidades': ['vendas', 'consultoria', 'produtos'],
            'max_atendimentos_simultaneos': 5,
            'horario_trabalho': {
                'segunda': '09:00-19:00',
                'terca': '09:00-19:00',
                'quarta': '09:00-19:00',
                'quinta': '09:00-19:00',
                'sexta': '09:00-18:00'
            }
        }
    )

    # Atendente 3 - Financeiro
    atendente3, created = AtendenteHumano.objects.get_or_create(
        telefone="+5511999999003",
        defaults={
            'nome': 'Carlos Oliveira',
            'cargo': 'Analista Financeiro',
            'departamento': 'Financeiro',
            'email': 'carlos.oliveira@empresa.com',
            'especialidades': ['financeiro', 'cobranca', 'faturamento'],
            'max_atendimentos_simultaneos': 4,
            'disponivel': False,  # Indisponível para exemplo
            'horario_trabalho': {
                'segunda': '08:00-17:00',
                'terca': '08:00-17:00',
                'quarta': '08:00-17:00',
                'quinta': '08:00-17:00',
                'sexta': '08:00-16:00'
            }
        }
    )

    print("✅ Atendentes criados:")
    print(f"   - {atendente1.nome} ({atendente1.departamento})")
    print(f"   - {atendente2.nome} ({atendente2.departamento})")
    print(f"   - {atendente3.nome} ({atendente3.departamento}) - Indisponível")

    return [atendente1, atendente2, atendente3]


def criar_cliente_e_atendimento_exemplo():
    """Cria um cliente e atendimento de exemplo"""

    print("\n👤 Criando cliente e atendimento de exemplo...")

    # Cria cliente
    cliente, created = Cliente.objects.get_or_create(
        telefone="+5511987654321",
        defaults={
            'nome': 'Ana Paula',
            'metadados': {
                'origem': 'whatsapp',
                'primeira_interacao': True
            }
        }
    )

    # Cria atendimento
    atendimento = Atendimento.objects.create(
        cliente=cliente,
        status=StatusAtendimento.EM_ANDAMENTO,
        assunto='Problema com produto',
        prioridade='alta'
    )

    print(f"✅ Cliente criado: {cliente.nome} ({cliente.telefone})")
    print(f"✅ Atendimento criado: #{atendimento.id}")

    return cliente, atendimento


def demonstrar_busca_atendente():
    """Demonstra a busca por atendentes disponíveis"""

    print("\n🔍 Demonstrando busca por atendentes disponíveis...")

    # Busca qualquer atendente disponível
    atendente = buscar_atendente_disponivel()
    if atendente:
        print(f"✅ Atendente disponível encontrado: {atendente.nome}")
        print(f"   - Departamento: {atendente.departamento}")
        print(f"   - Especialidades: {', '.join(atendente.especialidades)}")
        print(
            f"   - Atendimentos ativos: {atendente.get_atendimentos_ativos()}")
    else:
        print("❌ Nenhum atendente disponível")

    # Busca por especialidade específica
    atendente_vendas = buscar_atendente_disponivel(especialidades=['vendas'])
    if atendente_vendas:
        print(f"✅ Atendente de vendas encontrado: {atendente_vendas.nome}")
    else:
        print("❌ Nenhum atendente de vendas disponível")

    # Busca por departamento específico
    atendente_suporte = buscar_atendente_disponivel(
        departamento='Suporte Técnico')
    if atendente_suporte:
        print(f"✅ Atendente de suporte encontrado: {atendente_suporte.nome}")
    else:
        print("❌ Nenhum atendente de suporte disponível")


def demonstrar_transferencia_automatica():
    """Demonstra a transferência automática de atendimento"""

    print("\n🔄 Demonstrando transferência automática...")

    # Busca um atendimento sem atendente
    atendimento = Atendimento.objects.filter(
        atendente_humano__isnull=True).first()

    if not atendimento:
        print("❌ Nenhum atendimento disponível para transferência")
        return

    print(f"📞 Atendimento #{atendimento.id} precisa ser transferido")
    print(f"   - Cliente: {atendimento.cliente.nome}")
    print(f"   - Assunto: {atendimento.assunto}")

    # Transfere automaticamente para atendente de vendas
    atendente = transferir_atendimento_automatico(
        atendimento,
        especialidades=['vendas'],
        departamento='Vendas'
    )

    if atendente:
        print(f"✅ Atendimento transferido para: {atendente.nome}")
        print(f"   - Status atual: {atendimento.get_status_display()}")
        print(f"   - Atendente: {atendimento.atendente_humano.nome}")
    else:
        print("❌ Não foi possível transferir o atendimento")


def demonstrar_gestao_disponibilidade():
    """Demonstra o gerenciamento de disponibilidade"""

    print("\n⚙️ Demonstrando gestão de disponibilidade...")

    # Lista atendentes por disponibilidade
    disponibilidade = listar_atendentes_por_disponibilidade()

    print("📊 Status dos atendentes:")
    print(f"   - Disponíveis: {len(disponibilidade['disponiveis'])}")
    print(f"   - Ocupados: {len(disponibilidade['ocupados'])}")
    print(f"   - Indisponíveis: {len(disponibilidade['indisponiveis'])}")

    # Mostra detalhes dos disponíveis
    if disponibilidade['disponiveis']:
        print("\n✅ Atendentes disponíveis:")
        for info in disponibilidade['disponiveis']:
            print(f"   - {info['nome']} ({info['departamento']})")
            print(
                f"     Atendimentos: {info['atendimentos_ativos']}/{info['max_atendimentos']}")
            print(f"     Especialidades: {', '.join(info['especialidades'])}")

    # Mostra detalhes dos indisponíveis
    if disponibilidade['indisponiveis']:
        print("\n❌ Atendentes indisponíveis:")
        for info in disponibilidade['indisponiveis']:
            print(f"   - {info['nome']} ({info['departamento']})")


def demonstrar_gestao_especialidades():
    """Demonstra o gerenciamento de especialidades"""

    print("\n🎯 Demonstrando gestão de especialidades...")

    # Busca um atendente
    atendente = AtendenteHumano.objects.first()
    if not atendente:
        print("❌ Nenhum atendente encontrado")
        return

    print(f"👨‍💼 Atendente: {atendente.nome}")
    print(f"📋 Especialidades atuais: {', '.join(atendente.especialidades)}")

    # Adiciona nova especialidade
    nova_especialidade = 'chatbot'
    atendente.adicionar_especialidade(nova_especialidade)
    print(f"➕ Especialidade '{nova_especialidade}' adicionada")
    print(
        f"📋 Especialidades após adição: {
            ', '.join(
                atendente.especialidades)}")

    # Remove especialidade
    atendente.remover_especialidade(nova_especialidade)
    print(f"➖ Especialidade '{nova_especialidade}' removida")
    print(
        f"📋 Especialidades após remoção: {
            ', '.join(
                atendente.especialidades)}")


def main():
    """Função principal que executa todos os exemplos"""

    print("=" * 60)
    print("🤖 DEMONSTRAÇÃO: Nova Entidade AtendenteHumano")
    print("=" * 60)

    try:
        # 1. Criar atendentes de exemplo
        atendentes = criar_atendentes_exemplo()

        # 2. Criar cliente e atendimento
        cliente, atendimento = criar_cliente_e_atendimento_exemplo()

        # 3. Demonstrar busca de atendentes
        demonstrar_busca_atendente()

        # 4. Demonstrar transferência automática
        demonstrar_transferencia_automatica()

        # 5. Demonstrar gestão de disponibilidade
        demonstrar_gestao_disponibilidade()

        # 6. Demonstrar gestão de especialidades
        demonstrar_gestao_especialidades()

        print("\n" + "=" * 60)
        print("✅ Demonstração concluída com sucesso!")
        print("=" * 60)

        print("\n📋 Resumo das funcionalidades implementadas:")
        print("• ✅ Nova entidade AtendenteHumano com campos completos")
        print("• ✅ WhatsApp como identificador único (sessão)")
        print("• ✅ Gestão de especialidades e departamentos")
        print("• ✅ Controle de disponibilidade e capacidade")
        print("• ✅ Transferência automática inteligente")
        print("• ✅ Funções utilitárias para gerenciamento")
        print("• ✅ Admin interface configurada")
        print("• ✅ Validações e métodos auxiliares")

    except Exception as e:
        print(f"\n❌ Erro durante a demonstração: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
