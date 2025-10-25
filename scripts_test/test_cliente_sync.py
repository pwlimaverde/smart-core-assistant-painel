"""
Script completo para teste de sincronização de Cliente e vínculo com Contatos.

Este script cria:
1. Contatos de teste no Django
2. Um cliente de teste
3. Testa a sincronização de ambos
4. Verifica o vínculo entre cliente e contatos

Uso:
    uv run python scripts_test/test_cliente_sync.py
"""
import os
import sys

# Adicionar path do projeto
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')

import django
django.setup()

from datetime import datetime
from smart_core_assistant_painel.app.ui.clientes.models import Contato, Cliente
from smart_core_assistant_painel.app.notion_sync.models import ContatoSync, ClienteSync, NotionDatabaseConfig


def verify_notion_configs():
    """Verifica se as configurações do Notion estão ok."""
    print("🔍 Verificando configurações do Notion...")

    try:
        config_contato = NotionDatabaseConfig.objects.get(slug="ui_clientes_contato")
        config_cliente = NotionDatabaseConfig.objects.get(slug="ui_clientes_cliente")

        print(f"✅ Configuração Contatos: {config_contato.name}")
        print(f"   Database ID: {config_contato.notion_database_id}")
        print(f"   Ready: {config_contato.is_ready_for_sync()}")

        print(f"✅ Configuração Clientes: {config_cliente.name}")
        print(f"   Database ID: {config_cliente.notion_database_id}")
        print(f"   Ready: {config_cliente.is_ready_for_sync()}")

        return True

    except Exception as e:
        print(f"❌ Erro ao verificar configurações: {e}")
        return False


def create_test_contacts():
    """Cria contatos de teste para vincular ao cliente."""
    print("\n👥 Criando contatos de teste...")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    contatos_data = [
        {
            "telefone": f"55119{timestamp[-6:]}",
            "nome_contato": "João Silva - Contato Principal",
            "email": f"joao.silva{timestamp}@empresa.com",
            "nome_perfil_whatsapp": "João da Silva Ltda",
            "ativo": True
        },
        {
            "telefone": f"55119{int(timestamp[-6:]) + 1}",
            "nome_contato": "Maria Santos - Financeiro",
            "email": f"maria.santos{timestamp}@empresa.com",
            "nome_perfil_whatsapp": "Maria Santos Financeiro",
            "ativo": True
        },
        {
            "telefone": f"55119{int(timestamp[-6:]) + 2}",
            "nome_contato": "Pedro Costa - Comercial",
            "email": f"pedro.costa{timestamp}@empresa.com",
            "nome_perfil_whatsapp": "Pedro Costa Comercial",
            "ativo": True
        }
    ]

    contatos_criados = []
    for contato_data in contatos_data:
        try:
            contato = Contato.objects.create(**contato_data)
            contatos_criados.append(contato)
            print(f"✅ Contato criado: {contato.nome_contato} ({contato.telefone})")
        except Exception as e:
            print(f"❌ Erro ao criar contato: {e}")

    return contatos_criados


def create_test_cliente(contatos):
    """Cria um cliente e vincula aos contatos."""
    print("\n🏢 Criando cliente de teste...")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Dados do cliente (respeitando limites do banco)
    cliente_data = {
        "nome_fantasia": f"Empresa{timestamp[-4:]}",
        "razao_social": f"Empresa{timestamp[-4:]}",
        "tipo": "juridica",
        "cnpj": "12.345.678/0001-99",
        "telefone": "5511999999",
        "site": "https://empresa.com.br",
        "ramo_atividade": "Tecnologia",
        "observacoes": "Teste integracao",
        "cep": "01310100",
        "logradouro": "Av Paulista",
        "numero": "1000"
    }

    try:
        # Remover campos que não existem no modelo
        fields_to_remove = ['contatos', 'complemento']
        for field in fields_to_remove:
            cliente_data.pop(field, None)

        cliente = Cliente.objects.create(**cliente_data)
        print(f"✅ Cliente criado: {cliente.nome_fantasia}")
        print(f"   CNPJ: {cliente.cnpj}")
        print(f"   ID: {cliente.id}")

        # Se o modelo tiver relacionamento com contatos, vincular
        if hasattr(cliente, 'contatos'):
            cliente.contatos.add(*contatos)
            cliente.save()
            print(f"✅ {len(contatos)} contatos vinculados ao cliente")

        return cliente

    except Exception as e:
        print(f"❌ Erro ao criar cliente: {e}")
        return None


def verify_sync_records(contatos, cliente):
    """Verifica se os registros de sincronização foram criados."""
    print("\n🔍 Verificando registros de sincronização...")

    # Verificar ContatoSync
    contato_syncs = ContatoSync.objects.filter(contato__in=contatos)
    print(f"📊 ContatoSync encontrados: {contato_syncs.count()}")

    for sync in contato_syncs:
        status_emoji = {
            'pending': '⏳',
            'synced': '✅',
            'error': '❌'
        }.get(sync.sync_status, '❓')

        print(f"   {status_emoji} {sync.contato.nome_contato} - {sync.sync_status} - {sync.external_id or 'Sem ID'}")
        if sync.notion_properties:
            print(f"      Propriedades: {len(sync.notion_properties)} campos")

    # Verificar ClienteSync
    try:
        cliente_sync = ClienteSync.objects.get(cliente=cliente)
        status_emoji = {
            'pending': '⏳',
            'synced': '✅',
            'error': '❌'
        }.get(cliente_sync.sync_status, '❓')

        print(f"📊 ClienteSync encontrado:")
        print(f"   {status_emoji} {cliente_sync.cliente.nome_fantasia} - {cliente_sync.sync_status}")
        if cliente_sync.external_id:
            print(f"      External ID: {cliente_sync.external_id}")
        if cliente_sync.notion_properties:
            print(f"      Propriedades: {len(cliente_sync.notion_properties)} campos")

    except ClienteSync.DoesNotExist:
        print("❌ ClienteSync não encontrado")

    # Verificar logs de sincronização
    from smart_core_assistant_painel.app.notion_sync.models import SyncLog
    recent_logs = SyncLog.objects.order_by('-created_at')[:10]

    if recent_logs.exists():
        print(f"\n📋 Logs recentes ({recent_logs.count()} mais recentes):")
        for log in recent_logs:
            status_emoji = {
                'success': '✅',
                'error': '❌',
                'pending': '⏳'
            }.get(log.status, '❓')

            print(f"   {status_emoji} {log.operation} - {log.model_name} - {log.status}")
            if log.error_message:
                print(f"      Erro: {log.error_message}")


def test_update_scenario(contato, cliente):
    """Testa cenário de atualização."""
    print("\n🔄 Testando cenário de atualização...")

    try:
        # Atualizar contato
        contato.nome_contato += " [ATUALIZADO]"
        contato.email = f"atualizado-{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
        contato.save(skip_sync=False)  # Forçar sincronização

        print(f"✅ Contato atualizado: {contato.nome_contato}")

        # Atualizar cliente
        cliente.observacoes += f"\n\nAtualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        cliente.save(skip_sync=False)

        print(f"✅ Cliente atualizado: {cliente.nome_fantasia}")

    except Exception as e:
        print(f"❌ Erro no teste de atualização: {e}")


def display_summary():
    """Exibe resumo final do teste."""
    print("\n" + "="*60)
    print("📊 RESUMO FINAL DO TESTE DE INTEGRAÇÃO")
    print("="*60)

    # Estatísticas dos modelos
    total_contatos = Contato.objects.count()
    total_clientes = Cliente.objects.count()
    total_contato_sync = ContatoSync.objects.count()
    total_cliente_sync = ClienteSync.objects.count()

    print(f"\n📈 Estatísticas:")
    print(f"   Contatos (Django): {total_contatos}")
    print(f"   Clientes (Django): {total_clientes}")
    print(f"   ContatoSync: {total_contato_sync}")
    print(f"   ClienteSync: {total_cliente_sync}")

    # Status da sincronização
    synced_contatos = ContatoSync.objects.filter(sync_status='synced').count()
    synced_clientes = ClienteSync.objects.filter(sync_status='synced').count()
    error_contatos = ContatoSync.objects.filter(sync_status='error').count()
    error_clientes = ClienteSync.objects.filter(sync_status='error').count()

    print(f"\n📊 Status da Sincronização:")
    print(f"   Contatos sincronizados: {synced_contatos}/{total_contato_sync}")
    print(f"   Clientes sincronizados: {synced_clientes}/{total_cliente_sync}")
    print(f"   Contatos com erro: {error_contatos}")
    print(f"   Clientes com erro: {error_clientes}")

    # Links úteis
    try:
        config_contato = NotionDatabaseConfig.objects.get(slug="ui_clientes_contato")
        config_cliente = NotionDatabaseConfig.objects.get(slug="ui_clientes_cliente")

        print(f"\n🔗 Links úteis:")
        print(f"   Database Contatos: https://www.notion.so/{config_contato.notion_database_id}")
        print(f"   Database Clientes: https://www.notion.so/{config_cliente.notion_database_id}")

    except Exception:
        pass

    print("\n" + "="*60)


def main():
    """Função principal do teste."""
    print("🚀 Teste Completo de Integração Django ↔ Notion")
    print("="*60)

    # 1. Verificar configurações
    if not verify_notion_configs():
        print("❌ Configurações do Notion não estão OK. Abortando.")
        return

    # 2. Criar contatos de teste
    contatos = create_test_contacts()
    if not contatos:
        print("❌ Não foi possível criar contatos. Abortando.")
        return

    # Aguardar um pouco para os signals processarem
    print("\n⏳ Aguardando processamento dos signals...")
    import time
    time.sleep(2)

    # 3. Criar cliente
    cliente = create_test_cliente(contatos)
    if not cliente:
        print("❌ Não foi possível criar cliente. Abortando.")
        return

    # 4. Aguardar processamento
    print("\n⏳ Aguardando processamento da sincronização...")
    time.sleep(3)

    # 5. Verificar registros de sincronização
    verify_sync_records(contatos, cliente)

    # 6. Testar cenário de atualização
    if contatos:
        test_update_scenario(contatos[0], cliente)

    # 7. Aguardar processamento das atualizações
    print("\n⏳ Aguardando processamento das atualizações...")
    time.sleep(3)

    # 8. Verificar registros após atualização
    print("\n🔍 Verificando registros pós-atualização...")
    verify_sync_records(contatos, cliente)

    # 9. Exibir resumo final
    display_summary()


if __name__ == "__main__":
    main()
