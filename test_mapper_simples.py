#!/usr/bin/env python
"""Script simples para testar o mapper de atendimento."""

import os
import sys

# Adicionar o path do projeto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"Erro ao configurar Django: {e}")
    sys.exit(1)

def main():
    """Testa o mapper de atendimento."""
    print("=== TESTANDO MAPPER DE ATENDIMENTO ===\n")

    try:
        from smart_core_assistant_painel.app.notion_sync.models import AtendimentoSync
        from smart_core_assistant_painel.app.ui.atendimentos.models import Atendimento

        # Obter um atendimento
        atendimento = Atendimento.objects.first()
        if not atendimento:
            print("❌ Nenhum atendimento encontrado!")
            return

        print(f"📋 Atendimento: #{atendimento.id}")

        # Criar sync
        sync, _ = AtendimentoSync.objects.get_or_create(
            atendimento=atendimento,
            defaults={'sync_status': 'pending'}
        )

        # Preparar dados (isso vai usar nosso mapper)
        sync.prepare_notion_data()

        if sync.notion_properties:
            print("✅ Propriedades preparadas:")
            for key, value in sync.notion_properties.items():
                if key == "Mensagens Relacionadas":
                    if "relation" in value:
                        print(f"   📎 {key}: {len(value['relation'])} mensagens")
                        for msg in value['relation']:
                            print(f"     • ID: {msg.get('id', 'N/A')}")
                    else:
                        print(f"   📎 {key}: {type(value).__name__}")
                elif 'relation' in str(value):
                    print(f"   🔗 {key}: {type(value).__name__}")
                else:
                    print(f"   📄 {key}: {type(value).__name__}")
        else:
            print("❌ Nenhuma propriedade preparada")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
