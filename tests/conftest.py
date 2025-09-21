"""Configuração global para testes pytest com Django."""

import os
import sys
from pathlib import Path

import django

# Ensure the src directory is in the path
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Adiciona um alias de pacote "ai_engine" apontando para o pacote real
# em src/smart_core_assistant_painel/modules/ai_engine para compatibilizar
# imports absolutos no código (ex.: "from ai_engine.features...") durante os testes.
try:
    ai_engine_dir = (
        src_dir
        / "smart_core_assistant_painel"
        / "modules"
        / "ai_engine"
    )
    if "ai_engine" not in sys.modules and ai_engine_dir.is_dir():
        import types

        alias_pkg = types.ModuleType("ai_engine")
        # Torna o alias um pacote para permitir imports de submódulos reais
        alias_pkg.__path__ = [str(ai_engine_dir)]  # type: ignore[attr-defined]
        sys.modules["ai_engine"] = alias_pkg
except Exception:
    # Caso falhe, os testes indicarão o problema; não interromper a coleta
    pass

# Set the Django settings module
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings_test"
)

# Initialize Django
django.setup()

# Configure pytest-django
