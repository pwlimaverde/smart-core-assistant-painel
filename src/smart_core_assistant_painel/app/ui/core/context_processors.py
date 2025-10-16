from typing import Dict

from smart_core_assistant_painel import __version__


def project_version(_: object) -> Dict[str, str]:
    """Injects project version into template context."""
    return {"PROJECT_VERSION": __version__}