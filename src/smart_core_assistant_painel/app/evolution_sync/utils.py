import json
from typing import Any, Dict, List

from django.core.cache import cache
from django_q.models import Schedule
from django.utils import timezone

from smart_core_assistant_painel.modules.services import SERVICEHUB


def set_buffer_contact(contact_id: int, envelope: Dict[str, Any]) -> None:
    key = f"evo_buffer_{contact_id}"
    buf: List[Dict[str, Any]] = cache.get(key, [])
    buf.append(envelope)
    cache.set(key, buf, timeout=(SERVICEHUB.TIME_CACHE or 60) + 60)


def clear_buffer_contact(contact_id: int) -> None:
    key = f"evo_buffer_{contact_id}"
    timer_key = f"evo_timer_{contact_id}"
    cache.delete(key)
    cache.delete(timer_key)


def sched_response_contact(params: Dict[str, Any]) -> None:
    contact_id = int(params.get("contact_id"))
    timer_key = f"evo_timer_{contact_id}"
    if cache.get(timer_key):
        return
    cache.set(timer_key, True, timeout=(SERVICEHUB.TIME_CACHE or 60) + 60)
    name = f"process_contact_{contact_id}"
    next_run = timezone.now() + timezone.timedelta(seconds=SERVICEHUB.TIME_CACHE)
    Schedule.objects.filter(name=name).delete()
    Schedule.objects.create(
        name=name,
        func=(
            "smart_core_assistant_painel.app.ui.atendimentos.utils.send_message_response_by_contact"
        ),
        args=json.dumps(params),
        schedule_type=Schedule.ONCE,
        next_run=next_run,
    )