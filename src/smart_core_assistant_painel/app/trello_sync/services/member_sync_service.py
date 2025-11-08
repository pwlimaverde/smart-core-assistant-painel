from __future__ import annotations

from typing import Any, Optional, cast
import unicodedata

from loguru import logger
from django.utils import timezone

from smart_core_assistant_painel.modules.services import (
    FeaturesCompose,
    SERVICEHUB,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.domain.interface.unified_data_service import (
    UnifiedDataService,
)
from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
    TrelloUnifiedDataService,
)
from smart_core_assistant_painel.app.trello_sync.models import TrelloBoard, TrelloMember


class MemberSyncService:
    """
    Serviço de sincronização de membros (Atendente ↔ Trello Member).

    Comentário: convida o e-mail do atendente para o board do fluxo
    e tenta resolver o `external_id` do membro posteriormente.
    """

    def __init__(self) -> None:
        # Comentário (PT-BR): Obtém o UDS do SERVICEHUB. Se necessário,
        # inicializa via FeaturesCompose para registrar a instância.
        try:
            self.client: UnifiedDataService = SERVICEHUB.unified_data_service
        except Exception:
            FeaturesCompose.unifield_data_services()
            self.client = SERVICEHUB.unified_data_service

    def _trello(self) -> TrelloUnifiedDataService:
        """Retorna o adapter Trello com métodos de membros."""
        return cast(TrelloUnifiedDataService, self.client)

    def _normalize_text(self, value: Optional[str]) -> str:
        """Normaliza texto para comparação robusta (sem acentos, minúsculo).

        Comentário: ajuda a casar nomes com/sem acento e variação de caso.
        """
        if not value:
            return ""
        norm = unicodedata.normalize("NFKD", value)
        without_accents = "".join(
            ch for ch in norm if not unicodedata.combining(ch)
        )
        return without_accents.casefold().strip()

    def invite_for_atendente(self, atendente: Any) -> TrelloMember:
        """Envia convite para o board do fluxo e cria/atualiza TrelloMember.

        - Usa `atendente.fluxo.trello_board.external_id` para o board.
        - Envia convite para `atendente.email`.
        - Cria/atualiza TrelloMember com metadados e marca convite enviado.
        """
        email: Optional[str] = getattr(atendente, "email", None)
        fluxo = getattr(atendente, "fluxo", None)
        if not fluxo or not email:
            raise ValueError("Atendente sem fluxo ou email para convite Trello")

        board: Optional[TrelloBoard] = getattr(fluxo, "trello_board", None)
        if board is None:
            from .flow_sync_service import FlowSyncService

            board = FlowSyncService().ensure_board_for_fluxo(fluxo)

        # Envia convite
        try:
            data = self._trello().invite_member_to_board(
                board_id=board.external_id, email=email
            )
        except Exception as exc:
            logger.error("Falha ao convidar membro para board Trello: {}", exc)
            data = {"error": str(exc)}

        # Cria ou atualiza o TrelloMember vinculado ao atendente
        tm: Optional[TrelloMember] = getattr(atendente, "trello_member", None)
        if tm is None:
            tm = TrelloMember.objects.create(
                atendente=atendente,
                external_id=None,
                username="",
                full_name=getattr(atendente, "nome", ""),
                email=email,
                metadata={"invite": data, "invited_at": timezone.now().isoformat()},
                is_invited=True,
                invite_sent_at=timezone.now(),
            )
        else:
            tm.email = email
            tm.full_name = getattr(atendente, "nome", tm.full_name)
            tm.metadata = {**(tm.metadata or {}), "invite": data}
            tm.is_invited = True
            tm.invite_sent_at = timezone.now()
            tm.save(update_fields=[
                "email",
                "full_name",
                "metadata",
                "is_invited",
                "invite_sent_at",
            ])

        return tm

    def resolve_member_external_id(self, atendente: Any) -> Optional[str]:
        """Obtém o `external_id` do membro no Trello, se possível.

        Estratégia:
        - Se já existir `external_id` em TrelloMember, retorna.
        - Senão, lista membros do board do fluxo e tenta casar por
          `fullName` ou `username` se disponível; e atualiza o registro.
        """
        tm: Optional[TrelloMember] = getattr(atendente, "trello_member", None)
        if tm and tm.external_id:
            return tm.external_id

        fluxo = getattr(atendente, "fluxo", None)
        if not fluxo:
            return None
        board: Optional[TrelloBoard] = getattr(fluxo, "trello_board", None)
        if board is None:
            from .flow_sync_service import FlowSyncService

            board = FlowSyncService().ensure_board_for_fluxo(fluxo)

        try:
            members = self._trello().get_board_members(board.external_id)
        except Exception as exc:
            logger.warning("Não foi possível listar membros do board: {}", exc)
            members = []

        # Critérios de matching (tolerante a acentos e caso)
        full_name = getattr(atendente, "nome", None)
        username = getattr(
            getattr(atendente, "usuario", None), "username", None
        )
        target_name = self._normalize_text(full_name)
        target_user = self._normalize_text(username)

        found_id: Optional[str] = None
        for m in members:
            m_name = self._normalize_text(str(m.get("fullName", "")))
            m_user = self._normalize_text(str(m.get("username", "")))
            # Igualdade direta
            if target_name and m_name == target_name:
                found_id = str(m.get("id", ""))
                break
            if target_user and m_user == target_user:
                found_id = str(m.get("id", ""))
                break
            # Fallback: início do nome (evita falsos positivos muito amplos)
            if target_name and (m_name.startswith(target_name) or target_name.startswith(m_name)):
                found_id = str(m.get("id", ""))
                break

        if found_id and tm:
            tm.external_id = found_id
            tm.username = tm.username or str(
                next(
                    (
                        m.get("username")
                        for m in members
                        if m.get("id") == found_id
                    ),
                    "",
                )
            )
            tm.save(update_fields=["external_id", "username"])

        if not found_id:
            # Comentário: ajuda diagnosticar casos de não-resolução
            try:
                sample = [str(m.get("fullName", "")) for m in members][:5]
                logger.warning(
                    "Membro Trello não resolvido por nome/username. Alvo: {} / {}. Candidates: {}",
                    full_name,
                    username,
                    sample,
                )
            except Exception:
                pass

        return found_id