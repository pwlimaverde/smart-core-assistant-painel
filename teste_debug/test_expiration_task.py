import os
import sys
import django
from django.utils import timezone
from dateutil.relativedelta import relativedelta

# Setup Django
sys.path.append(os.path.join(os.getcwd(), "src"))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)
django.setup()

from smart_core_assistant_painel.app.tenants.models import (
    Tenant,
    Subscription,
    PaymentRecord,
)
from smart_core_assistant_painel.app.tenants.tasks import (
    check_subscription_expirations,
)
from django.contrib.auth import get_user_model

User = get_user_model()


def run_test():
    print("Iniciando teste de verificacao de expiracao...")

    # 1. Clean up
    Tenant.objects.filter(slug="test-exp-tenant").delete()

    # 2. Create User, Tenant
    user = User.objects.first()
    if not user:
        print("Criando usuario teste...")
        user = User.objects.create_superuser(
            "testadmin", "test@example.com", "pass"
        )

    tenant = Tenant.objects.create(
        name="Tenant Expirado Teste",
        slug="test-exp-tenant",
        owner=user,
        active=True,
    )
    print(f"Tenant criado: {tenant}")

    # 3. Create Subscription (Expired)
    # Using PaymentRecord to set logic, or creating direct
    # Vamos criar via PaymentRecord com data passada

    past_date = timezone.now().date() - relativedelta(months=2)  # 2 months ago
    # Period ends 1 month ago (expired)
    period_start = past_date
    period_end = past_date + relativedelta(months=1)

    payment = PaymentRecord.objects.create(
        tenant=tenant,
        amount=100.00,
        payment_date=past_date,
        payment_method=PaymentRecord.PaymentMethod.CASH,
        period_start=period_start,
        period_end=period_end,
        recorded_by=user,
    )
    print(
        f"Pagamento retroativo criado. Periodo: {period_start} a {period_end}"
    )

    # Create/Update Subscription manually to match logic (RegisterPaymentView does this)
    if hasattr(tenant, "subscription"):
        sub = tenant.subscription
    else:
        sub = Subscription.objects.create(tenant=tenant)

    sub.set_manual_period(period_start, period_end)
    print(
        f"Subscription ajustada. Current End: {sub.current_period_end} (Status: {sub.status})"
    )

    # 4. Run Task verify
    sub.refresh_from_db()

    print("Executando task check_subscription_expirations...")
    result = check_subscription_expirations()
    print(f"Task result: {result}")

    # 5. Check status
    sub.refresh_from_db()
    print(f"Status pos-task: {sub.status}")

    if sub.status == Subscription.Status.SUSPENDED:
        print("SUCESSO: Tenant suspenso automaticamente.")
    else:
        print("FALHA: Tenant NAO foi suspenso.")
        # Debug why
        now = timezone.now()
        print(
            f"Debug: Now={now}, End={sub.current_period_end}, Expired? {sub.current_period_end < now}"
        )

    # Cleanup
    # tenant.delete()


if __name__ == "__main__":
    run_test()
