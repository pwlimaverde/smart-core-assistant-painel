import os
import sys
import django
from django.utils import timezone
from datetime import timedelta
import logging

# Configure path and django
sys.path.append(os.path.join(os.getcwd(), "src"))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
django.setup()

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    Contato,
    StatusAtendimento,
    TipoMensagem,
    OrigemMensagem,
)
from smart_core_assistant_painel.app.ui.atendimentos.services.attendance_orchestrator import (
    AttendanceOrchestrator,
)
from smart_core_assistant_painel.app.ui.atendimentos.services.message_analyzer import (
    MessageAnalyzer,
)
from smart_core_assistant_painel.app.ui.atendimentos.services.attendance_structure_manager import (
    AttendanceStructureManager,
)
from smart_core_assistant_painel.app.ui.bot.services.bot_rules_engine import (
    BotRulesEngine,
)

# Configure Logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_test():
    print(">>> Iniciando teste de feedback...")

    # 1. Criar Contato Teste
    contact_phone = "5511999998888"  # Test number
    contato, created = Contato.objects.get_or_create(
        telefone=contact_phone, defaults={"nome": "Teste Feedback Auto"}
    )
    print(f"Contato: {contato.id} (Criado: {created})")

    # 2. Criar Atendimento Resolvido
    # Limpar atendimentos anteriores deste teste para evitar confusão
    Atendimento.objects.filter(contato=contato).delete()

    atd_old = Atendimento.objects.create(
        contato=contato,
        status=StatusAtendimento.RESOLVIDO,
        data_inicio=timezone.now() - timedelta(minutes=20),
        data_fim=timezone.now() - timedelta(minutes=2),  # 2 mins ago
    )
    print(f"Atendimento anterior (Resolvido): {atd_old.id}")

    # 3. Criar Mensagem de Feedback
    msg_content = "10, adorei o atendimento, muito bom!"
    mensagem = Mensagem.objects.create(
        contato=contato,
        conteudo=msg_content,
        tipo=TipoMensagem.TEXTO,
        origem=OrigemMensagem.CLIENTE,
        data_recebimento=timezone.now(),
        atendimento=None,
    )
    print(f"Mensagem criada: {mensagem.id} - Conteúdo: '{msg_content}'")

    # 4. Instantiate Orchestrator
    try:
        orch = AttendanceOrchestrator(
            message_analyzer=MessageAnalyzer(),
            structure_manager=AttendanceStructureManager(),
            rules_engine=BotRulesEngine(),
        )

        print(">>> Chamando _process_message_and_respond...")

        # 5. Call processing
        orch._process_message_and_respond(
            message_id=mensagem.id,
            contact_id=contato.id,
            api_key="test_key",
            env_list=[],
        )
    except Exception as e:
        print(f"!!! Erro na execução: {e}")
        import traceback

        traceback.print_exc()

    # 6. Verify Results
    atd_old.refresh_from_db()
    print(f"<<< Resultado Atendimento {atd_old.id}:")
    print(f"   Avaliação: {atd_old.avaliacao} (Esperado: 5)")
    print(f"   Feedback: {atd_old.feedback}")
    print(f"   Tags: {atd_old.tags}")

    mensagem.refresh_from_db()

    passed = False
    if (
        atd_old.avaliacao == 5
        and atd_old.feedback
        and "Sentimento:" in str(atd_old.tags)
    ):
        print(">>> TESTE SUCESSO: Feedback registrado e processado!")
        passed = True
    else:
        print(">>> TESTE FALHOU: Dados não atualizados corretamente.")

    if passed:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    run_test()
