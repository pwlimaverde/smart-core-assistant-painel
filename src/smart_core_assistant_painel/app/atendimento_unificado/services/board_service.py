# pyright: reportAttributeAccessIssue=false, reportUnknownArgumentType=false, reportUnnecessaryComparison=false
"""Mover atendimento entre etapas / quadros do Kanban interno.

Paridade funcional total com Trello: ao mover para uma `EtapaFluxo`
com determinado `tipo_etapa`, dispara o comportamento equivalente ao
que `trello_sync.services.ticket_sync_service` faz quando o card é
movido pelo webhook.

| `TipoEtapa`     | Ação                                                    |
|------------------|---------------------------------------------------------|
| FILA            | Apenas movimento + status FILA, remove atendente        |
| TRABALHO        | Assume: atribui atendente + saudação automática         |
| ESPERA          | Status PENDENCIA                                        |
| FINALIZACAO     | `finalizar_atendimento` (RESOLVIDO ou CANCELADO)        |

Cross-board: detecta se a etapa destino pertence a outro
`FluxoAtendimento` e ajusta `fluxo_atendimento_id`/`departamento_id`
em uma única transação.
"""

from __future__ import annotations

from typing import Any, Optional

from django.db import router, transaction
from loguru import logger

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    MovimentoFluxo,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.operacional.models import (
    Atendente,
    EtapaFluxo,
    TipoEtapa,
)


class BoardMoveError(Exception):
    """Erro ao mover atendimento (validação, permissão, etc.)."""


class BoardMoveResult:
    """Resumo do resultado de um move (consumido pelo SSE)."""

    def __init__(
        self,
        atendimento: Atendimento,
        movimento: Optional[MovimentoFluxo],
        cross_board: bool,
        novo_status: Optional[str],
        finalizou: bool,
    ) -> None:
        self.atendimento = atendimento
        self.movimento = movimento
        self.cross_board = cross_board
        self.novo_status = novo_status
        self.finalizou = finalizou


def move_atendimento(
    atendimento_id: int,
    etapa_destino_id: int,
    atendente_actor: Optional[Atendente] = None,
    motivo: Optional[str] = None,
) -> BoardMoveResult:
    """Move o atendimento para a etapa destino aplicando regras.

    Args:
        atendimento_id: ID do `Atendimento`.
        etapa_destino_id: ID da `EtapaFluxo` alvo.
        atendente_actor: Atendente que disparou a movimentação (usado
            quando a etapa for TRABALHO).
        motivo: Texto descritivo para histórico.

    Returns:
        ``BoardMoveResult`` com flags úteis para publicar SSE.
    """
    # IMPORTANTE: passar `using=router.db_for_write(Atendimento)` no
    # transaction.atomic() é obrigatório em ambiente multi-tenant. Sem ele,
    # `transaction.atomic()` abre a transação no banco DEFAULT, mas o
    # `select_for_update()` é roteado para o banco do tenant — que não está
    # em transação — disparando `TransactionManagementError`. Mesmo padrão
    # usado em trello_sync.ticket_sync_service.process_webhook_card_move.
    with transaction.atomic(using=router.db_for_write(Atendimento)):
        atend = (
            Atendimento.objects.select_for_update()
            .select_related("fluxo_atendimento", "etapa_atual")
            .get(id=atendimento_id)
        )
        etapa_destino = (
            EtapaFluxo.objects.select_related("fluxo", "fluxo__departamento")
            .filter(id=etapa_destino_id, ativo=True)
            .first()
        )
        if etapa_destino is None:
            raise BoardMoveError(
                f"Etapa destino {etapa_destino_id} não encontrada/ativa."
            )

        # Idempotência: se o card já está na etapa destino e no mesmo fluxo,
        # nada a fazer (evita movimentos espúrios e signals duplicados).
        if (
            atend.etapa_atual_id == etapa_destino.id
            and atend.fluxo_atendimento_id == etapa_destino.fluxo_id
        ):
            return BoardMoveResult(
                atendimento=atend,
                movimento=None,
                cross_board=False,
                novo_status=None,
                finalizou=False,
            )

        # Detecta cross-board (mudança de fluxo)
        cross_board = (
            atend.fluxo_atendimento_id != etapa_destino.fluxo_id
            and etapa_destino.fluxo_id is not None
        )

        if cross_board:
            atend.fluxo_atendimento_id = etapa_destino.fluxo_id
            atend.departamento_id = etapa_destino.fluxo.departamento_id
            atend.save(update_fields=["fluxo_atendimento", "departamento"])

        # Cria movimento (atualiza etapa_atual + atendente_humano se houver
        # atendente_destino), seguindo `MovimentoFluxo.criar_movimento`.
        movimento = MovimentoFluxo.criar_movimento(
            atendimento=atend,
            etapa_destino=etapa_destino,
            atendente_destino=None,
            motivo=motivo or _default_motivo(cross_board, atendente_actor),
            automatico=False,
            atendente_origem=atendente_actor,
        )

        novo_status, finalizou = _aplicar_regras_tipo_etapa(
            atend, etapa_destino, atendente_actor
        )

    return BoardMoveResult(
        atendimento=atend,
        movimento=movimento,
        cross_board=cross_board,
        novo_status=novo_status,
        finalizou=finalizou,
    )


def assign_atendimento(
    atendimento_id: int,
    atendente: Atendente,
    com_saudacao: bool = True,
) -> Atendimento:
    """Atribui atendente a um atendimento (override manual)."""
    with transaction.atomic(using=router.db_for_write(Atendimento)):
        atend = Atendimento.objects.select_for_update().get(id=atendimento_id)
        if com_saudacao:
            atend.transferir_para_humano_com_saudacao(
                atendente_id=atendente.id,
                observacao=f"Atribuído via Workspace por {atendente.nome}",
            )
        else:
            atend.assign_to_agent(
                atendente=atendente,
                observacao=f"Atribuído via Workspace por {atendente.nome}",
            )
    return atend


def mark_read(
    atendimento_id: int,
    atendente_id: int,
) -> Any:
    """Cria/atualiza ``LeituraAtendimento`` para o atendente atual."""
    from ..models import LeituraAtendimento

    obj, _created = LeituraAtendimento.objects.update_or_create(
        atendimento_id=atendimento_id,
        atendente_id=atendente_id,
        defaults={},
    )
    return obj


def _aplicar_regras_tipo_etapa(
    atend: Atendimento,
    etapa_destino: EtapaFluxo,
    atendente_actor: Optional[Atendente],
) -> tuple[Optional[str], bool]:
    """Aplica regra de transição conforme `tipo_etapa`.

    Retorna ``(novo_status_str, finalizou)``.
    """
    tipo = etapa_destino.tipo_etapa
    novo_status: Optional[str] = None
    finalizou = False

    if tipo == TipoEtapa.FILA.value:
        # Volta para fila: desatribui atendente e zera bot_pode_atender? não
        # — manter `bot_pode_atender` como está; só atualiza status.
        if atend.status != StatusAtendimento.FILA:
            atend.status = StatusAtendimento.FILA
            atend.atendente_humano = None
            atend.adicionar_historico_status(
                StatusAtendimento.FILA.value,
                "Movido para fila via Workspace",
            )
            atend.save(
                update_fields=[
                    "status",
                    "atendente_humano",
                    "historico_status",
                ]
            )
            novo_status = atend.status

    elif tipo == TipoEtapa.TRABALHO.value:
        # Assume atendimento (regra-chave de paridade com Trello)
        if atendente_actor is not None:
            try:
                atend.transferir_para_humano_com_saudacao(
                    atendente_id=atendente_actor.id,
                    observacao=(
                        f"Assumido via Workspace por {atendente_actor.nome}"
                    ),
                )
                novo_status = StatusAtendimento.EM_ATENDIMENTO.value
            except Exception as exc:
                logger.error(
                    "Falha ao assumir atendimento {} pelo atendente {}: {}",
                    atend.id,
                    atendente_actor.id,
                    exc,
                )
                raise BoardMoveError(
                    "Não foi possível assumir o atendimento. "
                    "Verifique se o atendente está cadastrado."
                ) from exc
        else:
            # Sem actor: apenas muda status, sem saudação.
            if atend.status != StatusAtendimento.EM_ATENDIMENTO:
                atend.status = StatusAtendimento.EM_ATENDIMENTO
                atend.adicionar_historico_status(
                    StatusAtendimento.EM_ATENDIMENTO.value,
                    "Movido para Em Trabalho via Workspace",
                )
                atend.save(update_fields=["status", "historico_status"])
                novo_status = atend.status

    elif tipo == TipoEtapa.ESPERA.value:
        if atend.status != StatusAtendimento.PENDENCIA:
            atend.status = StatusAtendimento.PENDENCIA
            atend.adicionar_historico_status(
                StatusAtendimento.PENDENCIA.value,
                "Movido para etapa de espera via Workspace",
            )
            atend.save(update_fields=["status", "historico_status"])
            novo_status = atend.status

    elif tipo == TipoEtapa.FINALIZACAO.value:
        nome_lower = (etapa_destino.nome or "").lower()
        final_status = (
            StatusAtendimento.CANCELADO.value
            if "cancel" in nome_lower
            else StatusAtendimento.RESOLVIDO.value
        )
        try:
            atend.finalizar_atendimento(
                novo_status=final_status,
                solicitar_feedback=False,
            )
            novo_status = final_status
            finalizou = True
        except Exception as exc:
            logger.error(
                "Falha ao finalizar atendimento {}: {}", atend.id, exc
            )
            raise BoardMoveError("Falha ao finalizar atendimento.") from exc

    return novo_status, finalizou


def _default_motivo(
    cross_board: bool, atendente_actor: Optional[Atendente]
) -> str:
    autor = (
        f" por {atendente_actor.nome}" if atendente_actor is not None else ""
    )
    return f"Movido via Workspace{autor}" + (
        " (entre quadros)" if cross_board else ""
    )
