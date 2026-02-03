import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Subscription

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def check_subscription_expirations(self):
    """
    Verifica assinaturas expiradas e suspende o tenant.
    Deve rodar diariamente (ex: 00:05).
    """
    now = timezone.now()
    # Busca subscriptions ativas que já venceram
    expired_subs = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        current_period_end__lt=now,
    )

    count = 0
    for sub in expired_subs:
        logger.warning(
            f"Suspendendo tenant {sub.tenant.slug} (expirou em {sub.current_period_end})"
        )
        sub.status = Subscription.Status.SUSPENDED
        sub.save()
        count += 1

    return f"{count} subscriptions suspended."


@shared_task(bind=True)
def notify_expiring_subscriptions(self):
    """
    Identifica assinaturas vencendo em breve (ex: 7 dias) e notifica (log/email).
    Deve rodar diariamente (ex: 09:00).
    """
    days_ahead = 7
    target_date = timezone.now() + timedelta(days=days_ahead)

    # Range para pegar quem vence EXATAMENTE daqui a 7 dias?
    # Ou pegar quem vence nos PRÓXIMOS 7 dias?
    # Vamos pegar quem vence no range de hoje até target_date

    expiring_soon = Subscription.objects.filter(
        status=Subscription.Status.ACTIVE,
        current_period_end__lte=target_date,
        current_period_end__gte=timezone.now(),
    )

    count = 0
    for sub in expiring_soon:
        # AQUI IMPLEMENTAR ENVIO DE EMAIL FUTURAMENTE
        logger.info(
            f"Aviso: Tenant {sub.tenant.slug} expira em breve ({sub.current_period_end})"
        )
        count += 1

    return f"{count} subscriptions expiring soon notified."
