"""[EVO-API-001] Interface e factory para os adapters da Evolution API.

Define o Protocol ``EvolutionAPIInterface`` que todos os adapters devem
satisfazer, e a factory ``get_evolution_adapter`` que seleciona a
implementação correta com base no campo ``api_version`` de cada
``EvolutionInstance``.

Uso:
    adapter = get_evolution_adapter(instance.api_version)
    adapter.send_text(instance=..., api_key=..., base_url=...,
                      number=..., text=...)
"""

from typing import Protocol, runtime_checkable

from smart_core_assistant_painel.app.evolution_sync.services.evolution_go_adapter import (
    EvolutionGoAdapter,
)
from smart_core_assistant_painel.app.evolution_sync.services.evolution_v2_adapter import (
    EvolutionV2Adapter,
)

# Re-exporta alias retrocompat para não quebrar imports existentes
# (ex.: `from .evolution_api import EvolutionWhatsAppService`)
EvolutionWhatsAppService = EvolutionV2Adapter


@runtime_checkable
class EvolutionAPIInterface(Protocol):
    """[EVO-API-002] Contrato de interface para adapters da Evolution API."""

    def send_text(self, *, instance: str, api_key: str, base_url: str, number: str, text: str, quoted: "dict | None" = None) -> dict: ...
    def send_media(self, *, instance: str, api_key: str, base_url: str, number: str, file_url: str, kind: str, caption: str = "", filename: str = "") -> dict: ...
    def send_audio(self, *, instance: str, api_key: str, base_url: str, number: str, audio_url: str, ptt: bool = True) -> dict: ...
    def send_reaction(self, *, instance: str, api_key: str, base_url: str, number: str, message_id: str, emoji: str, from_me: bool = False) -> dict: ...
    def mark_read(self, *, instance: str, api_key: str, base_url: str, number: str, message_ids: list[str]) -> dict: ...
    def set_presence(self, *, instance: str, api_key: str, base_url: str, number: str, state: str, is_audio: bool = False) -> dict: ...
    def get_profile_picture(self, *, instance: str, api_key: str, base_url: str, number: str) -> str: ...
    def fetch_instances(self, base_url: str, api_key: str) -> list[dict]: ...
    def create_instance(self, *, base_url: str, api_key: str, name: str, token: "str | None" = None) -> dict: ...
    def connect_instance(self, *, base_url: str, api_key: str, name: str, webhook_url: str, subscribe: list[str]) -> dict: ...
    def get_qr_code(self, *, base_url: str, api_key: str, name: str) -> dict: ...
    def get_status(self, *, base_url: str, api_key: str, name: str) -> dict: ...
    def delete_instance(self, *, base_url: str, api_key: str, name: str) -> None: ...
    def logout_instance(self, *, base_url: str, api_key: str, name: str) -> None: ...
    def get_base64_from_media(self, base_url: str, api_key: str, instance_name: str, message_key: dict, message_content: dict) -> str: ...
    def download_media(self, *, base_url: str, api_key: str, instance: str, message_id: str, number: str) -> dict: ...


def get_evolution_adapter(
    api_version: str,
) -> "EvolutionV2Adapter | EvolutionGoAdapter":
    """[EVO-API-003] Factory: retorna o adapter correto com base na ``api_version``.

    Args:
        api_version: Valor de ``EvolutionInstance.api_version``
                     (``"v2"`` ou ``"go"``).

    Returns:
        - ``"go"``  → ``EvolutionGoAdapter``
        - qualquer outro valor → ``EvolutionV2Adapter`` (default seguro)
    """
    if api_version == "go":
        return EvolutionGoAdapter()
    return EvolutionV2Adapter()


__all__ = [
    "EvolutionAPIInterface",
    "EvolutionWhatsAppService",
    "get_evolution_adapter",
]
