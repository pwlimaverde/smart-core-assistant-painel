import os
import sys
import django
from django.utils import timezone
import logging

# Configure path and django
sys.path.append(os.path.join(os.getcwd(), "src"))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.core.settings",
)
django.setup()

from smart_core_assistant_painel.app.atendimentos.models import (
    Atendimento,
    Mensagem,
    StatusAtendimento,
    TipoMensagem,
    TipoRemetente,
)
from smart_core_assistant_painel.app.clientes.models import Contato
from smart_core_assistant_painel.app.operacional.models import (
    Departamento,
    FluxoAtendimento,
    EtapaFluxo,
    TipoEtapa,
)
from smart_core_assistant_painel.app.trello_sync.models import (
    TrelloCard,
    TrelloList,
)
from smart_core_assistant_painel.app.trello_sync.services.ticket_sync_service import (
    TicketSyncService,
)

# Configure Logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_test():
    print(">>> Iniciando teste de TRIGGER de feedback via Trello Sync...")

    # 1. Setup Base Structure (Dept, Flow, Stages)
    dept, _ = Departamento.objects.get_or_create(
        nome="Dept Teste Feedback",
        defaults={"slug": "dept-teste-feedback", "email": "teste@example.com"},
    )
    fluxo, _ = FluxoAtendimento.objects.get_or_create(
        nome="Fluxo Teste", departamento=dept
    )

    etapa_fila, _ = EtapaFluxo.objects.get_or_create(
        fluxo=fluxo,
        tipo_etapa=TipoEtapa.FILA,
        defaults={"nome": "Fila", "ordem": 1},
    )
    etapa_final, _ = EtapaFluxo.objects.get_or_create(
        fluxo=fluxo,
        tipo_etapa=TipoEtapa.FINALIZACAO,
        defaults={"nome": "Finalizado", "ordem": 2},
    )

    trello_list_fila, _ = TrelloList.objects.get_or_create(
        external_id="list_fila_123",
        defaults={"name": "Fila Trello", "etapa": etapa_fila},
    )
    # Ensure association if it existed but bad link
    trello_list_fila.etapa = etapa_fila
    trello_list_fila.save()

    trello_list_final, _ = TrelloList.objects.get_or_create(
        external_id="list_final_456",
        defaults={"name": "Final Trello", "etapa": etapa_final},
    )
    trello_list_final.etapa = etapa_final
    trello_list_final.save()

    # 2. Create Atendimento and Card
    contato, _ = Contato.objects.get_or_create(
        telefone="5511999991234", defaults={"nome": "Tester Trigger"}
    )

    # Cleanup previous runs
    Atendimento.objects.filter(contato=contato).delete()

    atendimento = Atendimento.objects.create(
        contato=contato,
        departamento=dept,
        fluxo_atendimento=fluxo,
        etapa_atual=etapa_fila,
        status=StatusAtendimento.FILA,
    )

    card = TrelloCard.objects.create(
        atendimento=atendimento,
        external_id="card_abc_123",
        name="Card Teste",
        list_sync=trello_list_fila,
    )

    print(
        f"Atendimento criado: {atendimento.id}, Status: {atendimento.status}"
    )

    # 3. Simulate Move in Trello (FILA -> FINALIZACAO)
    print(">>> Simulando movimento do card para lista de finalização...")

    service = TicketSyncService()
    # Mocking ensure_card_for_atendimento or similar if needed?
    # No, process_webhook_card_move mocks the webhook event.

    # We need to ensure we don't actually hit Trello API for updates that might fail if credentials missing
    # But process_webhook_card_move calls update_card_rich_content which calls API.
    # We might see errors in logs but the DB update should happen.

    try:
        service.process_webhook_card_move(
            card_id="card_abc_123",
            list_after_id="list_final_456",
            member_creator_id="member_123",
        )
    except Exception as e:
        print(
            f"Erro no processamento (pode ser API Trello, ignorar se DB atualizou): {e}"
        )

    # 4. Verify Results
    atendimento.refresh_from_db()
    print(f"Status Pós-Move: {atendimento.status}")
    print(f"Etapa Pós-Move: {atendimento.etapa_atual.nome}")
    print(f"Data Fim: {atendimento.data_fim}")

    # Verify Feedback Request Message
    msgs = Mensagem.objects.filter(
        atendimento=atendimento, remetente=TipoRemetente.BOT
    ).order_by("-data_criacao")
    feedback_msg = None
    for m in msgs:
        if (
            "avalie nosso atendimento" in m.resposta_bot
            or "feedback" in m.resposta_bot.lower()
        ):
            feedback_msg = m
            break

    if atendimento.status == StatusAtendimento.RESOLVIDO and feedback_msg:
        print(
            ">>> SUCESSO! Status atualizado para RESOLVIDO e mensagem de feedback criada."
        )
        print(f"Mensagem: {feedback_msg.resposta_bot}")
        exit(0)
    else:
        print(">>> FALHA!")
        print(f"Esperado Status Resolvido, obteve: {atendimento.status}")
        print(f"Mensagem de feedback encontrada: {feedback_msg is not None}")
        exit(1)


if __name__ == "__main__":
    run_test()
