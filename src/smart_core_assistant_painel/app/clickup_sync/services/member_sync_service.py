from typing import Any

from loguru import logger

from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.clicup_adapter import (
    ClicupUnifiedDataService,
)
from smart_core_assistant_painel.modules.services.utils.parameters import (
    UnifieldDataServicesParameters,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    UnifieldDataServicesError,
)

from ..models import ClickupMember


class MemberSyncService:
    """Sincroniza Atendente com membro do ClickUp."""

    def __init__(self) -> None:
        # Comentário: inicializa adapter com parâmetros e observabilidade ativa
        params = UnifieldDataServicesParameters(
            data_source_id="",
            provider="clickup",
            root_container_name="Unified Data Root",
            enable_observability=True,
            error=UnifieldDataServicesError(message="UDS ClickUp error"),
        )
        self.udservice = ClicupUnifiedDataService(params)

    def invite_for_atendente(self, atendente: Any, username: str) -> None:
        """Registra um membro localmente (convite real pode ser futuro)."""
        existing = ClickupMember.objects.filter(
            atendente_id=atendente.id
        ).first()
        if existing:
            existing.username = username
            existing.save(update_fields=["username"])
            logger.info(
                "Atualizado membro ClickUp para atendente {}", atendente.id
            )
            return

        ClickupMember.objects.create(
            atendente_id=atendente.id,
            external_id=f"local-{atendente.id}",
            username=username,
        )
        logger.info(
            "Criado membro ClickUp (local) para atendente {}", atendente.id
        )

    def remove_member(self, atendente_id: int) -> bool:
        """Remove um membro do ClickUp correspondente ao Atendente."""
        member = ClickupMember.objects.filter(
            atendente_id=atendente_id
        ).first()
        if not member:
            logger.warning(
                "Membro não encontrado para atendente {}", atendente_id
            )
            return False

        try:
            # Primeiro remove o registro local
            member.delete()

            # Se o external_id não for apenas local, tenta remover do ClickUp
            if not member.external_id.startswith("local-"):
                success = self.udservice.remove_member(member.external_id)

                if success:
                    logger.info(
                        "Membro removido do ClickUp para atendente {} -> {}",
                        atendente_id,
                        member.external_id,
                    )
                    return True
                else:
                    logger.error(
                        "Falha ao remover membro do ClickUp: {}",
                        member.external_id,
                    )
                    return False
            else:
                logger.info(
                    "Membro local removido para atendente {} (sem remoção do ClickUp)",
                    atendente_id,
                )
                return True
        except Exception as exc:
            logger.error(
                "Falha ao remover membro {}: {}", member.external_id, exc
            )
            return False
