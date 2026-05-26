from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import FormView, TemplateView

from ..forms.onboarding import OnboardingConfigForm, TenantRegistrationForm
from ..models import Plan, Tenant
from ..services.provisioning import TenantProvisioningService

SESSION_DATA_KEY = "onboarding_data"
SESSION_PLAN_KEY = "onboarding_plan_id"
SESSION_CONFIG_KEY = "onboarding_config"
SESSION_STEP_KEY = "onboarding_step"


class OnboardingSessionMixin:
    """Mixin para gerenciar o contexto do onboarding na sessão durante o Wizard."""

    def get_onboarding_data(self):
        return self.request.session.get(SESSION_DATA_KEY)

    def dispatch(self, request, *args, **kwargs):
        # Se não tem dados do onboarding, volta pro passo 1 (exceto o próprio passo 1)
        if not self.get_onboarding_data() and not isinstance(
            self, Step1TenantView
        ):
            return redirect("tenants:onboarding_step_1")
        return super().dispatch(request, *args, **kwargs)


class Step1TenantView(FormView):
    template_name = "apps/tenants/onboarding/step_1_tenant.html"
    form_class = TenantRegistrationForm

    def form_valid(self, form):
        data = form.cleaned_data

        # Salva dados na sessão (backup)
        self.request.session[SESSION_DATA_KEY] = data

        try:
            # Cria o tenant imediatamente (Step 1)
            tenant_id = TenantProvisioningService.create_initial_tenant(data)
            self.request.session["onboarding_tenant_id"] = str(tenant_id)
            self.request.session[SESSION_STEP_KEY] = 2

            # Limpa chaves futuras para garantir estado limpo
            self.request.session.pop(SESSION_PLAN_KEY, None)
            self.request.session.pop(SESSION_CONFIG_KEY, None)

            return redirect("tenants:onboarding_step_2")
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)


class Step2PaymentView(OnboardingSessionMixin, TemplateView):
    template_name = "apps/tenants/onboarding/step_2_payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plans"] = Plan.objects.filter(active=True)
        context["onboarding_data"] = self.get_onboarding_data()

        # Verifica estado do tenant para decidir o que mostrar
        tenant_id = self.request.session.get("onboarding_tenant_id")
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                context["tenant"] = tenant

                if tenant.access_code == "AUTHORIZED":
                    context["show_plans"] = True
                elif tenant.access_code:
                    context["show_code_input"] = True
                else:
                    context["show_waiting"] = True

            except Tenant.DoesNotExist:
                pass

        return context

    def post(self, request, *args, **kwargs):
        tenant_id = request.session.get("onboarding_tenant_id")
        if not tenant_id:
            return redirect("tenants:onboarding_step_1")

        tenant = Tenant.objects.get(id=tenant_id)

        # Se já está autorizado ou usuário enviou plano diretamente (caso front mostre)
        # mas precisa garantir segurança
        if tenant.access_code == "AUTHORIZED":
            # Processa plano normalmente lá embaixo
            pass
        elif tenant.access_code:
            # Validação do código
            input_code = (
                request.POST.get("access_code", "")
                .strip()
                .replace("-", "")
                .upper()
            )

            # Se o post contiver 'plan_id', ignora e pede código (segurança)
            if "plan_id" in request.POST and not input_code:
                context = self.get_context_data()
                context["error"] = "Validação necessária."
                return render(request, self.template_name, context)

            stored_code = tenant.access_code.replace("-", "").upper()
            if input_code == stored_code:
                # Código válido!
                tenant.access_code = "AUTHORIZED"
                tenant.save()
                # Reload para mostrar planos
                return redirect("tenants:onboarding_step_2")
            else:
                context = self.get_context_data()
                context["error"] = "Código de acesso inválido."
                return render(request, self.template_name, context)
        else:
            # Tenant access_code is None. Usuário bloqueado.
            # Se tentar bypassar via Postman:
            context = self.get_context_data()
            context["error"] = "Aguardando aprovação do administrador."
            return render(request, self.template_name, context)

        # ====== Processamento do Plano (Só chega aqui se AUTHORIZED) ======
        plan_id = request.POST.get("plan_id")
        if not plan_id:
            return redirect("tenants:onboarding_step_2")

        request.session[SESSION_PLAN_KEY] = int(plan_id)
        TenantProvisioningService.update_plan(tenant, int(plan_id))
        request.session[SESSION_STEP_KEY] = 3

        return redirect("tenants:onboarding_step_3")


class Step3ConfigView(OnboardingSessionMixin, FormView):
    template_name = "apps/tenants/onboarding/step_3_config.html"
    form_class = OnboardingConfigForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["onboarding_data"] = self.get_onboarding_data()
        return context

    def form_valid(self, form):
        data = form.cleaned_data

        if not self.get_onboarding_data():
            return redirect("tenants:onboarding_step_1")
        if not self.request.session.get(SESSION_PLAN_KEY):
            return redirect("tenants:onboarding_step_2")

        self.request.session[SESSION_CONFIG_KEY] = {
            "brand_name": data.get("brand_name", ""),
            "primary_color": data.get("primary_color", "#0d6efd"),
            "secondary_color": data.get("secondary_color", "#6c757d"),
            "timezone": data.get("timezone", "America/Sao_Paulo"),
            "language_code": data.get("language_code", "pt-br"),
        }
        self.request.session[SESSION_STEP_KEY] = 4

        return redirect("tenants:onboarding_step_4")


class Step4ProvisionView(OnboardingSessionMixin, TemplateView):
    template_name = "apps/tenants/onboarding/step_4_provision.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["onboarding_data"] = self.get_onboarding_data()
        return context

    def post(self, request, *args, **kwargs):
        """Action AJAX para finalizar o setup"""
        onboarding_data = self.get_onboarding_data()
        plan_id = request.session.get(SESSION_PLAN_KEY)
        config_data = request.session.get(SESSION_CONFIG_KEY)
        if not onboarding_data or not plan_id or not config_data:
            return JsonResponse({"error": "Sessão expirada"}, status=400)

        try:
            redirect_url = (
                TenantProvisioningService.create_and_activate_tenant(
                    onboarding_data=onboarding_data,
                    plan_id=plan_id,
                    config_data=config_data,
                )
            )

            # Limpa sessão
            for key in (
                SESSION_DATA_KEY,
                SESSION_PLAN_KEY,
                SESSION_CONFIG_KEY,
                SESSION_STEP_KEY,
                "onboarding_tenant_id",
            ):
                request.session.pop(key, None)

            return JsonResponse({"redirect_url": redirect_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(never_cache, name="dispatch")
class CheckSlugView(View):
    def get(self, request):
        slug = request.GET.get("slug", "").strip().lower()
        if not slug:
            return JsonResponse({"available": False, "error": "Slug vazio"})

        reserved = [
            "admin",
            "api",
            "www",
            "app",
            "painel",
            "dashboard",
            "public",
            "static",
            "media",
            "tenant",
            "setup",
        ]

        if slug in reserved:
            return JsonResponse({"available": False, "message": "Reservado"})

        is_taken = Tenant.objects.filter(slug=slug).exists()

        return JsonResponse({"available": not is_taken, "slug": slug})
