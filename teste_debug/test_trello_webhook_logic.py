import pytest
from unittest.mock import MagicMock, patch
from smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service import (
    TicketSyncService,
)
from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    StatusAtendimento,
)
from smart_core_assistant_painel.app.operacional.models import (
    TipoEtapa,
    EtapaFluxo,
)


@pytest.mark.django_db
def test_sync_status_from_etapa_logica():
    service = TicketSyncService()

    # --- TESTE 1: TRABALHO -> ESPERA (Sync Status) ---
    atendimento = MagicMock(spec=Atendimento)
    atendimento.id = 1
    atendimento.status = StatusAtendimento.EM_ATENDIMENTO

    # Mock Etapa Destino
    etapa_destino = MagicMock(spec=EtapaFluxo)
    etapa_destino.tipo_etapa = TipoEtapa.ESPERA
    etapa_destino.nome = "Aguardando"

    # Testar sync diretamente
    service._sync_status_from_etapa(atendimento, etapa_destino)

    # Verificar se status mudou
    assert atendimento.status == StatusAtendimento.PENDENCIA, (
        f"Status deveria ser PENDENCIA, mas foi {atendimento.status}"
    )
    atendimento.save.assert_called_with(update_fields=["status"])


@pytest.mark.django_db
def test_sync_status_ignores_finalizacao():
    service = TicketSyncService()

    # --- TESTE 2: TRABALHO -> FINALIZACAO (Sync Ignora) ---
    atendimento = MagicMock(spec=Atendimento)
    atendimento.status = StatusAtendimento.EM_ATENDIMENTO

    etapa_final = MagicMock(spec=EtapaFluxo)
    etapa_final.tipo_etapa = TipoEtapa.FINALIZACAO
    etapa_final.nome = "Resolvido"

    service._sync_status_from_etapa(atendimento, etapa_final)

    # Verificar que status NÃO mudou e save NÃO foi chamado pelo sync
    assert atendimento.status == StatusAtendimento.EM_ATENDIMENTO, (
        "Status não deveria ser alterado pelo sync em FINALIZACAO"
    )
    atendimento.save.assert_not_called()
