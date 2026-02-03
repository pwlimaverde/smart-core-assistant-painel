from celery import shared_task
from loguru import logger

from smart_core_assistant_painel.app.tenants.celery import TenantTask

from smart_core_assistant_painel.app.ui.atendimentos.models import (
    Atendimento,
    Mensagem,
    TipoMensagem,
    TipoRemetente,
)


@shared_task(base=TenantTask)
def process_contact_response_task(tenant_slug: str, contact_id: int) -> None:
    """Tarefa para processar resposta de contato.

    Esta função é o ponto de entrada para o agendamento de tarefas.
    Ela instancia o orquestrador e delega o processamento.

    Args:
        contact_id: ID do contato a ser processado.
    """
    # Import local para evitar ciclos com o pacote services
    from smart_core_assistant_painel.app.ui.atendimentos.services import (
        create_orchestrator,
    )

    try:
        logger.info(
            f"Iniciando task de processamento para contato {contact_id}"
        )
        orchestrator = create_orchestrator()
        orchestrator.process_contact_response(contact_id=contact_id)
    except Exception as e:
        logger.error(
            f"Erro fatal na task de processamento para contato {contact_id}: {e}"
        )
        raise


@shared_task(
    base=TenantTask,
)
def verificar_feedback_atendimento(
    tenant_slug: str, atendimento_id: int
) -> None:
    """
    Verifica se o feedback foi recebido após um tempo determinado.
    Se não houve avaliação, envia mensagem de agradecimento e encerra o ciclo.
    """
    try:
        logger.info(
            f"Executando verificação de feedback para atendimento {atendimento_id}"
        )

        atendimento = Atendimento.objects.filter(id=atendimento_id).first()
        if not atendimento:
            logger.warning(
                f"Atendimento {atendimento_id} não encontrado na task de feedback."
            )
            return

        # Se já tem avaliação, não faz nada (o ciclo já foi encerrado pelo orchestrator)
        if atendimento.avaliacao is not None:
            logger.info(
                f"Atendimento {atendimento_id} já avaliado. Task finalizada."
            )
            return

        # Se não tem avaliação, envia agradecimento por timeout
        msg_agradecimento = "Agradecemos o seu contato! Se precisar de algo mais, estamos à disposição."

        # Tenta usar os metadados da última mensagem para manter consistência de canal/instância
        last_msg = atendimento.mensagens.order_by("-data_criacao").first()
        metadados = getattr(last_msg, "metadados", {}) if last_msg else {}

        Mensagem.objects.create(
            atendimento=atendimento,
            tipo=TipoMensagem.TEXTO_FORMATADO,
            conteudo="",
            remetente=TipoRemetente.BOT,
            resposta_bot=msg_agradecimento,
            metadados=metadados,
            respondida=False,
        )

        # Pode-se marcar algo no atendimento para indicar que o ciclo de feedback expirou?
        # Opcional: Adicionar tag de 'sem_feedback' ou 'timeout_feedback'
        tags = atendimento.tags or []
        if "feedback: timeout" not in tags:
            tags.append("feedback: timeout")
            atendimento.tags = tags
            atendimento.save(update_fields=["tags"])

        logger.info(
            f"Mensagem de agradecimento (timeout) enviada para atendimento {atendimento_id}."
        )

    except Exception as e:
        logger.error(
            f"Erro na task verificar_feedback_atendimento para {atendimento_id}: {e}"
        )
