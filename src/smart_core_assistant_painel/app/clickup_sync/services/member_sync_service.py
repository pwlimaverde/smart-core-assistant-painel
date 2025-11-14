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

from ..models import ClickupMember, ClickupList


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

    def find_and_register_by_email(self, atendente: Any) -> ClickupMember | None:
        """Busca membro no ClickUp por e-mail e registra no modelo local.

        Comentário (PT-BR): normaliza o e-mail do atendente, consulta os
        membros do time no ClickUp e persiste o vínculo em `ClickupMember`
        com `external_id` real do usuário do ClickUp. Se já existir um
        registro "local-<id>", atualiza para o ID real e username.

        Retorna o objeto `ClickupMember` criado/atualizado ou `None`.
        """
        try:
            email_raw: str | None = getattr(atendente, "email", None)
            email_norm: str = (email_raw or "").strip().lower()
            if not email_norm:
                logger.warning(
                    "Atendente #{} sem e-mail; não é possível mapear membro ClickUp",
                    atendente.id,
                )
                return None

            # Preferir escopo de List para membros conforme API ClickUp
            list_external_id: str | None = None
            try:
                fluxo_id = getattr(atendente, "fluxo_id", None)
                if fluxo_id:
                    mapping = ClickupList.objects.filter(
                        fluxo_atendimento_id=fluxo_id
                    ).first()
                    if mapping:
                        list_external_id = str(mapping.external_id)
                        logger.info(
                            "Usando List ClickUp {} para busca de membros do atendente #{}",
                            list_external_id,
                            atendente.id,
                        )
            except Exception:
                list_external_id = None

            found = self.udservice.find_member_by_email(
                email_norm, list_id=list_external_id
            )
            if not found:
                logger.info(
                    "Nenhum membro ClickUp encontrado para e-mail {}",
                    email_norm,
                )
                return None

            user = found.get("user") if isinstance(found.get("user"), dict) else found
            external_id: str = str(user.get("id", ""))
            username: str = str(user.get("username", ""))
            if not external_id:
                logger.warning(
                    "Membro ClickUp sem ID válido para e-mail {}",
                    email_norm,
                )
                return None

            existing = ClickupMember.objects.filter(
                atendente_id=atendente.id
            ).first()
            if existing:
                existing.external_id = external_id
                if username:
                    existing.username = username
                existing.save(update_fields=["external_id", "username"])
                logger.info(
                    "Atualizado ClickupMember do atendente #{} -> {}",
                    atendente.id,
                    external_id,
                )
                return existing

            obj = ClickupMember.objects.create(
                atendente_id=atendente.id,
                external_id=external_id,
                username=username or getattr(atendente, "nome", ""),
            )
            logger.info(
                "Criado ClickupMember para atendente #{} -> {}",
                atendente.id,
                external_id,
            )
            return obj
        except Exception as exc:
            logger.error(
                "Falha ao registrar membro ClickUp por e-mail do atendente #{}: {}",
                getattr(atendente, "id", "?"),
                str(exc),
            )
            return None
