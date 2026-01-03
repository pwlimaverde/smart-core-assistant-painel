from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Subscription, Tenant


@receiver(post_save, sender=Tenant)
def create_tenant_subscription(sender, instance, created, **kwargs):
    """Cria uma assinatura de Trial automaticamente ao criar um novo Tenant."""
    if created:
        Subscription.objects.create(
            tenant=instance,
            status=Subscription.Status.ACTIVE,
        )
