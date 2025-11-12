from typing import Any

from loguru import logger

from ..models import ClickupMember


class MemberSyncService:
    """Sincroniza Atendente com membro do ClickUp.

    Implementação mínima: registra/atualiza mapeamento local.
    """

    def invite_for_atendente(self, atendente: Any, username: str) -> None:
        """Registra um membro localmente (convite real pode ser futuro)."""
        existing = ClickupMember.objects.filter(atendente_id=atendente.id).first()
        if existing:
            existing.username = username
            existing.save(update_fields=["username"])
            logger.info("Atualizado membro ClickUp para atendente {}", atendente.id)
            return

        ClickupMember.objects.create(
            atendente_id=atendente.id,
            external_id=f"local-{atendente.id}",
            username=username,
        )
        logger.info("Criado membro ClickUp (local) para atendente {}", atendente.id)