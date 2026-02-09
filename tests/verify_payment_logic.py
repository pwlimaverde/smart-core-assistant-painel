import os
import sys
from pathlib import Path

# Add src to path
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.append(str(SRC_DIR))

from datetime import date
from decimal import Decimal

import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.config.settings"
)
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from smart_core_assistant_painel.app.tenants.models import (
    PaymentRecord,
    Plan,
    Subscription,
    Tenant,
)


def verify_payment_logic():
    print("--- Starting Verification ---")
    User = get_user_model()

    # 1. Setup Tenant and User
    user, _ = User.objects.get_or_create(
        username="verify_admin", email="verify@test.com", is_superuser=True
    )
    tenant, _ = Tenant.objects.get_or_create(
        name="Verify Tenant", slug="verify-tenant", owner=user
    )

    # 2. Setup Subscription
    plan, _ = Plan.objects.get_or_create(name="Test Plan", price=100)
    sub, _ = Subscription.objects.get_or_create(
        tenant=tenant, defaults={"plan": plan}
    )
    sub.current_period_end = timezone.now()
    sub.save()

    print(f"Initial Period End: {sub.current_period_end}")

    # 3. Create Payment Record (Manual Logic Simulation)
    payment_date = date.today()
    months = 6
    amount = Decimal("600.00")

    # Calculate period manually (as done in Form)
    from dateutil.relativedelta import relativedelta

    period_start = payment_date
    period_end = period_start + relativedelta(months=months)

    payment = PaymentRecord.objects.create(
        tenant=tenant,
        amount=amount,
        payment_date=payment_date,
        payment_method=PaymentRecord.PaymentMethod.PIX,
        period_start=period_start,
        period_end=period_end,
        recorded_by=user,
    )
    print(f"Payment Created: {payment}")

    # 4. Trigger Subscription Update (Manual Logic Simulation as done in View)
    sub.set_manual_period(payment.period_start, payment.period_end)
    sub.refresh_from_db()

    print(f"Updated Period End: {sub.current_period_end}")
    print(f"Expected Period End Date: {period_end}")

    # Validation
    assert sub.current_period_end.date() == period_end
    assert sub.status == Subscription.Status.ACTIVE

    print("--- Verification SUCCESS ---")


if __name__ == "__main__":
    verify_payment_logic()
