import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append("c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/src")
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
django.setup()

try:
    from smart_core_assistant_painel.app.evolution_sync.services import (
        get_and_clear_buffer_contact,
        clear_scheduling_lock,
    )

    print("Successfully imported new services.")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

try:
    from smart_core_assistant_painel.app.ui.atendimentos.services.attendance_orchestrator import (
        AttendanceOrchestrator,
    )

    print("Successfully imported AttendanceOrchestrator.")
except ImportError as e:
    print(f"ImportError in AttendanceOrchestrator: {e}")
    sys.exit(1)

print("Verification successful.")
