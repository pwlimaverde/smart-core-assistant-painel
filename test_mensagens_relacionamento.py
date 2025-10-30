#!/usr/bin/env python
"""Script para testar relacionamento de mensagens com atendimentos."""

import os
import sys
import django

# Adicionar o path do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import AtendimentoSync, MensagemSync
from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento, Mensagem

def main():
    """Testa relacionamento de mensagens com atendimentos."""
    print("=== TESTANDO RELACIONAMENTO DE MENSAGENS ===\n")

    # 1. Verificar atendimentos e suas mensagens
    print("1. ATENDIMENTOS E SUAS MENSAGENS:")
    atendimentos = Atendimento.objects.all()[:3]  # Limitar para não sobrecarregar

    for atendimento in atendimentos:
        print(f"\n📋 Atendimento #{atendimento.id}:")
        print(f"   - Título: {atendimento.assunto or 'Sem assunto'}")
        print(f"   - Status: {atendimento.status}")

        # Verificar mensagens no Django
        mensagens_django = Mensagem.objects.filter(atendimento=atendimento)
        print(f"   - Mensagens no Django: {mensagens_django.count()}")

        # Verificar sync do atendimento
        try:
            sync_atendimento = atendimento.notion_sync
            print(f"   - Sync ID: {sync_atendimento.id}")
            print(f"   - External ID: {sync_atendimento.external_id or 'NÃO SINCRONIZADO'}")
            print(f"   - Sync Status: {sync_atendimento.sync_status}")

            # Verificar mensagens relacionadas no sync
            mensagens_sync = sync_atendimento.mensagens_sync.all()
            print(f"   - Mensagens no Sync: {mensagens_sync.count()}")

            for msg_sync in mensagens_sync:
                print(f"     • Mensagem #{msg_sync.mensagem.id}:")
                print(f"       - External ID: {msg_sync.external_id or 'NÃO SINCRONIZADO'}")
                print(f"       - Sync Status: {msg_sync.sync_status}")
                print(f"       - Conteúdo: {msg_sync.mensagem.conteudo[:50]}...")
        except Exception as e:
            print(f"   - ❌ Erro ao acessar sync: {e}")

    # 2. Verificar mensagens sync e seus relacionamentos
    print(f"\n\n2. MENSAGENS SYNC E RELACIONAMENTOS:")
    mensagens_sync = MensagemSync.objects.all()[:5]  # Limitar

    for msg_sync in mensagens_sync:
        print(f"\n💬 Mensagem Sync #{msg_sync.id}:")
        print(f"   - Mensagem ID: {msg_sync.mensagem.id}")
        print(f"   - External ID: {msg_sync.external_id or 'NÃO SINCRONIZADO'}")
        print(f"   - Sync Status: {msg_sync.sync_status}")

        if msg_sync.atendimento_sync:
            print(f"   - Atendimento Sync ID: {msg_sync.atendimento_sync.id}")
            print(f"   - Atendimento ID: {msg_sync.atendimento_sync.atendimento.id}")
            print(f"   - Atendimento External ID: {msg_sync.atendimento_sync.external_id or 'NÃO SINCRONIZADO'}")
        else:
            print(f"   - ❌ Sem relacionamento com atendimento sync")

    # 3. Testar o mapper com um atendimento específico
    print(f"\n\n3. TESTE DO MAPPER:")
    try:
        atendimento_teste = Atendimento.objects.first()
        if atendimento_teste:
            sync_teste, _ = AtendimentoSync.objects.get_or_create(
                atendimento=atendimento_teste,
                defaults={'sync_status': 'pending'}
            )

            print(f"📋 Testando com atendimento #{atendimento_teste.id}")

            # Preparar dados usando o mapper
            sync_teste.prepare_notion_data()

            if sync_teste.notion_properties:
                print("✅ Propriedades preparadas:")
                for key, value in sync_teste.notion_properties.items():
                    if key == "Mensagens Relacionadas":
                        print(f"   📎 {key}: {len(value.get('relation', []))} mensagens")
                        for msg_rel in value.get('relation', []):
                            print(f"     • ID: {msg_rel['id']}")
                    elif 'relation' in str(value):
                        print(f"   🔗 {key}: {type(value).__name__}")
                    else:
                        print(f"   📄 {key}: {type(value).__name__}")
            else:
                print("❌ Nenhuma propriedade preparada")
    except Exception as e:
        print(f"❌ Erro no teste do mapper: {e}")
        import traceback
        traceback.print_exc()

    # 4. Verificar schema da configuração
    print(f"\n\n4. SCHEMA DA CONFIGURAÇÃO:")
    try:
        from smart_core_assistant_painel.app.notion_sync.models import NotionDatabaseConfig

        config = NotionDatabaseConfig.objects.get(slug="ui_atendimentos_atendimento")
        if config.notion_schema:
            print("✅ Schema local encontrado:")
            for prop_name, prop_config in config.notion_schema.items():
                if 'relation' in str(prop_config):
                    print(f"   🔗 {prop_name}: {prop_config}")
        else:
            print("❌ Schema não encontrado na configuração")
    except Exception as e:
        print(f"❌ Erro ao verificar schema: {e}")

    print("\n=== FIM DO TESTE ===")

if __name__ == "__main__":
    main()
