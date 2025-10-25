"""
Script para teste da sincronização de Contatos com Notion.

Este script cria um contato de teste e verifica se o signal
dispara corretamente a sincronização com o Notion.
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
from smart_core_assistant_painel.app.ui.clientes.models import Contato
from smart_core_assistant_painel.app.notion_sync.models import ContatoSync, NotionDatabaseConfig


def test_contato_creation():
    """Testa criação de um contato e verificação do sync."""
    print("🧪 Testando criação de contato e sincronização com Notion...")

    # Limpar syncs pendentes antes do teste
    clean_pending_syncs()

    # Verificar configurações do Notion
    try:
        config_contato = NotionDatabaseConfig.objects.get(slug="ui_clientes_contato")
        print(f"✅ Configuração do Notion encontrada: {config_contato.name}")
        print(f"   Database ID: {config_contato.notion_database_id}")
        print(f"   Ready for sync: {config_contato.is_ready_for_sync()}")
    except NotionDatabaseConfig.DoesNotExist:
        print("❌ Configuração do Notion não encontrada!")
        return

    # Criar contato de teste
    try:
        print("\n📝 Criando contato de teste...")
        # Gerar telefone único baseado no timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        telefone_unique = f"55119{timestamp[-8:]}"  # Últimos 8 dígitos do timestamp

        contato = Contato.objects.create(
            telefone=telefone_unique,
            nome_contato="Teste Sync Notion",
            email=f"teste{timestamp}@sync.com",
            nome_perfil_whatsapp="Teste WhatsApp",
            ativo=True
        )
        print(f"✅ Contato criado com ID: {contato.id}")

        # Verificar se o ContatoSync foi criado
        try:
            contato_sync = ContatoSync.objects.get(contato=contato)
            print(f"✅ ContatoSync criado com external_id: {contato_sync.external_id}")
            print(f"   Status: {contato_sync.sync_status}")
            print(f"   Nome formatado: {contato_sync.nome_formatado}")
            print(f"   Email normalizado: {contato_sync.email_normalizado}")
            print(f"   Telefone formatado: {contato_sync.telefone_formatado}")

            # Verificar se tem propriedades do Notion
            if contato_sync.notion_properties:
                print(f"   Propriedades Notion: {len(contato_sync.notion_properties)} campos")
            else:
                print("   ⚠️ Sem propriedades Notion definidas")

        except ContatoSync.DoesNotExist:
            print("❌ ContatoSync não foi criado pelo signal!")
            return

    except Exception as e:
        print(f"❌ Erro ao criar contato: {e}")
        return

    print("\n🎉 Teste concluído com sucesso!")
    print(f"📋 URL do Notion: https://www.notion.so/{config_contato.notion_database_id}")


def check_existing_syncs():
    """Verifica sincronizações existentes."""
    print("\n🔍 Verificando sincronizações existentes...")

    try:
        syncs = ContatoSync.objects.all()
        print(f"📊 Total de ContatoSync: {syncs.count()}")

        for sync in syncs[:5]:  # Mostrar apenas os 5 primeiros
            print(f"   - {sync.contato.nome_contato or 'Sem nome'} | {sync.sync_status} | {sync.external_id}")

    except Exception as e:
        print(f"❌ Erro ao verificar syncs: {e}")


def clean_pending_syncs():
    """Remove sincronizações pendentes para evitar conflitos."""
    try:
        # Remove syncs sem external_id para evitar conflitos
        ContatoSync.objects.filter(external_id="").delete()
        print("🧹 Limpeza de syncs pendentes concluída")
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Teste de Integração Django ↔ Notion")
    print("=" * 60)

    # Verificar sincronizações existentes
    check_existing_syncs()

    # Testar criação
    test_contato_creation()

    # Verificar novamente
    check_existing_syncs()
