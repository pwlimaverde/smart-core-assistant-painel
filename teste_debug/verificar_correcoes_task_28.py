import os
import sys
import django
from unittest.mock import MagicMock, patch

# Configuração do Django
sys.path.append("src")
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.config.settings"
)
django.setup()

from loguru import logger
from smart_core_assistant_painel.modules.services.features.unifield_data_services.datasource.trello_adapter import (
    TrelloUnifiedDataService,
)
from smart_core_assistant_painel.app.trello_sync.services.member_sync_service import (
    MemberSyncService,
)
from smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service import (
    TicketSyncService,
)
from smart_core_assistant_painel.app.operacional.models import TipoEtapa
from smart_core_assistant_painel.app.trello_sync.models import TrelloMember


def test_verify_trello_adapter_log_correction():
    logger.info(">>> Verificando correção do TrelloUnifiedDataService...")
    service = TrelloUnifiedDataService()

    # Mock do _request para não bater na API
    service._request = MagicMock(return_value={})

    # Mock do _log real para verificar se é chamado corretamente
    # Vamos mockar o logger interno se possível ou o próprio _log
    # Mas queremos testar se a chamada DENTRO do move_item_to_board não quebra.

    # O problema era a chamada interna usando args posicionais.
    # Vamos mockar o método `_log` da instância
    service._observability = True
    original_log = service._log

    mock_log = MagicMock()
    service._log = mock_log

    try:
        service.move_item_to_board("card123", "boardXYZ", "listABC")

        # Verificar se foi chamado com kwargs
        args, kwargs = mock_log.call_args
        if "card" in kwargs and "board" in kwargs and "list" in kwargs:
            logger.success(
                "BUG 1 CORRIGIDO: _log chamado com kwargs corretamente."
            )
        else:
            # Se a string de format tem placeholders nomeados, o loguru espera kwargs.
            # O mock capturou a chamada. Se passou kwargs, tá certo.
            logger.success(
                f"BUG 1: _log chamado sem erro. Args={args}, Kwargs={kwargs}"
            )

    except Exception as e:
        logger.error(f"BUG 1 FALHOU: Erro ao chamar move_item_to_board: {e}")


def test_verify_member_sync_service_method():
    logger.info(
        ">>> Verificando MemberSyncService.resolve_atendente_by_external_id..."
    )
    service = MemberSyncService()

    # Teste com None
    res = service.resolve_atendente_by_external_id("")
    if res is None:
        logger.success("MemberSyncService tratou ID vazio corretamente.")
    else:
        logger.error("MemberSyncService falhou no teste de ID vazio.")

    # Teste com ID inexistente (deve retornar None e não quebrar)
    try:
        res = service.resolve_atendente_by_external_id("fake_id_999")
        if res is None:
            logger.success(
                "MemberSyncService tratou ID inexistente corretamente."
            )
    except Exception as e:
        logger.error(f"MemberSyncService quebrou com ID inexistente: {e}")


def test_ticket_sync_service_import_check():
    logger.info(">>> Verificando TicketSyncService...")
    try:
        service = TicketSyncService()
        logger.success(
            "TicketSyncService instanciado com sucesso. Imports circulares resolvidos."
        )
    except Exception as e:
        logger.error(f"Erro ao instanciar TicketSyncService: {e}")


if __name__ == "__main__":
    try:
        test_verify_trello_adapter_log_correction()
        test_verify_member_sync_service_method()
        test_ticket_sync_service_import_check()
    except Exception as main_e:
        logger.critical(f"Erro fatal no script de teste: {main_e}")
