import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append("c:\\PROJETOS\\PYTHON\\APPS\\smart-core-assistant-painel\\src")
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.core.settings",
)
django.setup()

from smart_core_assistant_painel.modules.services.features.service_hub import (
    SERVICEHUB,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.modules.services import FeaturesCompose


def verify_service_hub():
    print("Initializing UnifiedDataService...")
    try:
        FeaturesCompose.unifield_data_services()
    except Exception as e:
        print(f"Error initializing services: {e}")

    print("Accessing SERVICEHUB.unified_data_service...")
    uds = SERVICEHUB.unified_data_service

    print(f"Type of uds: {type(uds)}")

    if isinstance(uds, property):
        print("FAIL: uds is a property object!")
    elif isinstance(uds, UnifiedDataService):
        print("SUCCESS: uds is a UnifiedDataService instance.")
    else:
        print(f"WARNING: uds is {type(uds)}, expected UnifiedDataService.")


if __name__ == "__main__":
    verify_service_hub()
