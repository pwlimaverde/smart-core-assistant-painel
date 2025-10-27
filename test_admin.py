"""
Script de teste para o admin de AtendenteHumanoSync
"""
import os
import sys

# Adicionar o path do projeto ao sys.path para importar Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_core_assistant_painel.app.ui.core.settings')
import django
django.setup()

from smart_core_assistant_painel.app.notion_sync.models import AtendenteHumanoSync
from smart_core_assistant_painel.app.notion_sync.admin import AtendenteHumanoSyncAdmin

def test_admin_methods():
    """Testa os métodos do admin de AtendenteHumanoSync."""
    print("🧪 Testando Admin de AtendenteHumanoSync...")

    # Criar instância do admin
        from django.contrib.admin.sites import site
        admin = AtendenteHumanoSyncAdmin(AtendenteHumanoSync, site)

    # Buscar primeiro registro
    sync = AtendenteHumanoSync.objects.first()

    if not sync:
        print("❌ Nenhum registro AtendenteHumanoSync encontrado")
        return

    print(f"📋 Testando com: {sync.atendente.nome}")

    # Testar método carga_info
    try:
        print("🔧 Testando método carga_info...")
        resultado = admin.carga_info(sync)
        print(f"✅ carga_info: {resultado}")
    except Exception as e:
        print(f"❌ Erro em carga_info: {e}")
        import traceback
        traceback.print_exc()

    # Testar método atendente_info
    try:
        print("🔧 Testando método atendente_info...")
        resultado = admin.atendente_info(sync)
        print(f"✅ atendente_info: {resultado}")
    except Exception as e:
        print(f"❌ Erro em atendente_info: {e}")

    # Testar método departamento_nome
    try:
        print("🔧 Testando método departamento_nome...")
        resultado = admin.departamento_nome(sync)
        print(f"✅ departamento_nome: {resultado}")
    except Exception as e:
        print(f"❌ Erro em departamento_nome: {e}")

    # Testar método sync_status_colored
    try:
        print("🔧 Testando método sync_status_colored...")
        resultado = admin.sync_status_colored(sync)
        print(f"✅ sync_status_colored: {resultado}")
    except Exception as e:
        print(f"❌ Erro em sync_status_colored: {e}")

    # Testar método external_id_short
    try:
        print("🔧 Testando método external_id_short...")
        resultado = admin.external_id_short(sync)
        print(f"✅ external_id_short: {resultado}")
    except Exception as e:
        print(f"❌ Erro em external_id_short: {e}")

    print("🎉 Testes concluídos!")

if __name__ == "__main__":
    test_admin_methods()
