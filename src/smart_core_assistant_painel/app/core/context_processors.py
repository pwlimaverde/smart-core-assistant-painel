from typing import Dict

from smart_core_assistant_painel import __version__


def project_version(_: object) -> Dict[str, str]:
    """Injects project version into template context."""
    ver = __version__
    if "+001" not in ver:
        ver = f"{ver}+001"
    return {"PROJECT_VERSION": ver}
