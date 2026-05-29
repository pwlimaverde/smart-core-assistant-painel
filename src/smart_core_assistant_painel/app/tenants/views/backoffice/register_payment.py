from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView

from ...forms import RegisterPaymentForm
from ...models import Tenant


class RegisterPaymentView(UserPassesTestMixin, FormView):
    template_name = "apps/tenants/backoffice/register_payment.html"
    form_class = RegisterPaymentForm

    def test_func(self):
        return self.request.user.is_superuser

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.tenant = get_object_or_404(Tenant, pk=kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tenant"] = self.tenant
        return context

    def form_valid(self, form):
        payment = form.save(commit=False)
        payment.tenant = self.tenant
        payment.recorded_by = self.request.user

        # O período já foi calculado no clean() do form
        payment.period_start = form.cleaned_data["period_start"]
        payment.period_end = form.cleaned_data["period_end"]
        payment.save()

        # Atualizar Subscription do Tenant
        if hasattr(self.tenant, "subscription"):
            subscription = self.tenant.subscription
            subscription.set_manual_period(
                payment.period_start, payment.period_end
            )
            messages.success(
                self.request,
                f"Pagamento registrado! Assinatura estendida até {payment.period_end}",
            )
        else:
            messages.warning(
                self.request,
                "Pagamento registrado, mas Tenant não possui Subscription ativa.",
            )

        # Redirecionar de volta para o admin do tenant
        # Tenta redirecionar para change list
        return redirect("admin:tenants_tenant_changelist")
