"""Smart Core Assistant Painel - SaaS Multi-tenant."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("smart-core-assistant-painel")
except PackageNotFoundError:
    # Fallback para desenvolvimento (quando não está instalado como pacote)
    __version__ = "1.0.0"
