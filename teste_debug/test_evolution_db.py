import os
import django

# Setup Django environment
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.core.settings"
)
django.setup()

from smart_core_assistant_painel.app.evolution_sync.models import (
    EvolutionInstance,
)


def test_db():
    instances = EvolutionInstance.objects.filter(
        name__icontains="paulo-ecoprint"
    )
    if not instances.exists():
        print("Instância paulo-ecoprint não encontrada!")
        for inst in EvolutionInstance.objects.all():
            print(
                f"- {inst.name} | url: {getattr(inst, 'server_url', 'N/A')} | tenant_id: {inst.tenant_id}"
            )
        return

    for inst in instances:
        print(f"Encontrada: {inst.name}")
        print(f"  URL: {getattr(inst, 'server_url', 'N/A')}")
        print(f"  API Key: {inst.api_key}")
        print(f"  ID: {inst.instance_id}")


if __name__ == "__main__":
    test_db()
