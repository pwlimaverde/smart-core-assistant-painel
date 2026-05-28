from datetime import timedelta

from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from django.views.generic import TemplateView

from smart_core_assistant_painel.app.tenants.models import Subscription, Tenant


class BackofficeDashboardView(UserPassesTestMixin, TemplateView):
    template_name = "apps/tenants/backoffice/dashboard.html"

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        thirty_days_future = today + timedelta(days=30)
        seven_days_future = today + timedelta(days=7)

        # Metrics
        context["total_tenants"] = Tenant.objects.count()
        context["active_tenants"] = Tenant.objects.filter(active=True).count()
        context["subscriptions_active"] = Subscription.objects.filter(
            status=Subscription.Status.ACTIVE
        ).count()

        # Subscriptions expiring in the next 30 days (ACTIVE only)
        context["expiring_soon_count"] = Subscription.objects.filter(
            status=Subscription.Status.ACTIVE,
            current_period_end__lte=thirty_days_future,
            current_period_end__gte=today,
        ).count()

        # Lists
        context["recent_tenants"] = Tenant.objects.select_related(
            "subscription"
        ).order_by("-created_at")[:5]

        context["expiring_subscriptions_list"] = (
            Subscription.objects.filter(
                status=Subscription.Status.ACTIVE,
                current_period_end__lte=seven_days_future,
                current_period_end__gte=today,
            )
            .select_related("tenant", "plan")
            .order_by("current_period_end")
        )

        context["site_header"] = "Smart Core Backoffice"
        context["site_title"] = "Smart Core Admin"
        context["index_title"] = "Dashboard"

        return context
