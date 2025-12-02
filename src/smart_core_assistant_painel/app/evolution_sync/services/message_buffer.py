from typing import Any, Dict, List

from django.core.cache import cache
from django.utils import timezone
from django_q.models import Schedule
from loguru import logger

from smart_core_assistant_painel.modules.services import SERVICEHUB


def set_buffer_contact(contact_id: int, envelope: Dict[str, Any]) -> None:
    key = f"evo_buffer_{contact_id}"
    buf: List[Dict[str, Any]] = cache.get(key, [])

    # Check for duplicates
    new_msg_id = envelope.get("message", {}).get("id")
    if new_msg_id:
        for existing_env in buf:
            if existing_env.get("message", {}).get("id") == new_msg_id:
                return

    buf.append(envelope)
    logger.debug("envelope: {}", envelope)
    cache.set(key, buf, timeout=(SERVICEHUB.TIME_CACHE or 20) + 20)


def clear_buffer_contact(contact_id: int) -> None:
    key = f"evo_buffer_{contact_id}"
    timer_key = f"evo_timer_{contact_id}"
    cache.delete(key)
    cache.delete(timer_key)


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
