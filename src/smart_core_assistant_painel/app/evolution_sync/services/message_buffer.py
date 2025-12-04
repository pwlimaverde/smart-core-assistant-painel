from typing import Any, Dict, List

from django.core.cache import cache
from django.utils import timezone
from django_q.models import Schedule
from loguru import logger

from smart_core_assistant_painel.modules.services import SERVICEHUB


def set_buffer_contact(contact_id: int, envelope: Dict[str, Any]) -> None:
    key = f"evo_buffer_{contact_id}"
    lock_key = f"evo_buffer_lock_{contact_id}"

    # Use lock to ensure atomicity when reading/writing buffer
    with cache.lock(lock_key, timeout=5):
        buf: List[Dict[str, Any]] = cache.get(key, [])

        # Check for duplicates
        new_msg_id = envelope.get("message", {}).get("id")
        if new_msg_id:
            for existing_env in buf:
                if existing_env.get("message", {}).get("id") == new_msg_id:
                    return

        buf.append(envelope)
        logger.debug("envelope: {}", envelope)
        # Aumentado para 300s (5min) para evitar perda de mensagens em caso de delay no worker
        cache.set(key, buf, timeout=300)


def get_and_clear_buffer_contact(contact_id: int) -> List[Dict[str, Any]]:
    """Recupera e limpa o buffer de mensagens de forma atômica."""
    key = f"evo_buffer_{contact_id}"
    lock_key = f"evo_buffer_lock_{contact_id}"

    with cache.lock(lock_key, timeout=5):
        buf: List[Dict[str, Any]] = cache.get(key, [])
        if buf:
            cache.delete(key)

    return buf


def clear_scheduling_lock(contact_id: int) -> None:
    """Limpa apenas o timer de agendamento, permitindo novas tasks."""
    timer_key = f"evo_timer_{contact_id}"
    cache.delete(timer_key)


# Deprecated: alias for backward compatibility if needed, but prefer clear_scheduling_lock
# or get_and_clear_buffer_contact depending on usage.
def clear_buffer_contact(contact_id: int) -> None:
    """DEPRECATED: Use clear_scheduling_lock or get_and_clear_buffer_contact."""
    clear_scheduling_lock(contact_id)
    # We do NOT clear the buffer here anymore to avoid race conditions.
    # The buffer is cleared atomically in get_and_clear_buffer_contact.


def sched_response_contact(params: Dict[str, Any]) -> None:
    cid_val = params.get("contact_id")
    if cid_val is None:
        return
    contact_id = int(cid_val)
    timer_key = f"evo_timer_{contact_id}"
    if cache.get(timer_key):
        return
    cache.set(timer_key, True, timeout=(SERVICEHUB.TIME_CACHE or 20) + 20)
    name = f"process_contact_{contact_id}"
    next_run = timezone.now() + timezone.timedelta(
        seconds=SERVICEHUB.TIME_CACHE
    )
    Schedule.objects.filter(name=name).delete()
    Schedule.objects.create(
        name=name,
        func=(
            "smart_core_assistant_painel.app.ui.atendimentos.services.process_contact_response_task"
        ),
        args=repr((contact_id,)),
        schedule_type=Schedule.ONCE,
        next_run=next_run,
    )
