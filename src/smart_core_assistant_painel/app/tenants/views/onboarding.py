from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import FormView, TemplateView
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from ..forms.onboarding import TenantRegistrationForm, TenantConfigForm
from ..services.provisioning import TenantProvisioningService
from ..models import Tenant, Plan

class OnboardingSessionMixin:
    """Mixin para gerenciar o contexto do Tenant na sessão durante o Wizard."""
    def get_tenant(self):
        tenant_id = self.request.session.get("onboarding_tenant_id")
        if not tenant_id:
            return None
        # Garante que só acessa tenants em setup
        return Tenant.objects.filter(id=tenant_id, setup_completed=False).first()

    def dispatch(self, request, *args, **kwargs):
        # Se não tem tenant na sessão, volta pro passo 1 (exceto se for o próprio passo 1)
        if not self.get_tenant() and not isinstance(self, Step1TenantView):
             return redirect("tenants:onboarding_step_1")
        return super().dispatch(request, *args, **kwargs)


class Step1TenantView(FormView):
    template_name = "tenants/onboarding/step_1_tenant.html"
    form_class = TenantRegistrationForm
    
    def form_valid(self, form):
        service = TenantProvisioningService()
        data = form.cleaned_data
        
        # Cria o Tenant Inicial
        tenant = service.create_initial_tenant(data)
        
        # Salva na sessão
        self.request.session["onboarding_tenant_id"] = str(tenant.id)
        
        return redirect("tenants:onboarding_step_2")


class Step2PaymentView(OnboardingSessionMixin, TemplateView):
    template_name = "tenants/onboarding/step_2_payment.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.filter(active=True)
        context['tenant'] = self.get_tenant()
        return context

    def post(self, request, *args, **kwargs):
        tenant = self.get_tenant()
        plan_id = request.POST.get("plan_id")
        
        if not plan_id:
            # Erro
            return redirect("tenants:onboarding_step_2")
            
        # Atualiza Plano
        TenantProvisioningService.update_plan(tenant, plan_id)
        
        # Mock: Assume pagamento OK e avança
        # Em produção, aqui redirecionaria para Gateway ou aguardaria webhook
        return redirect("tenants:onboarding_step_3")


class Step3ConfigView(OnboardingSessionMixin, FormView):
    template_name = "tenants/onboarding/step_3_config.html"
    form_class = TenantConfigForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.get_tenant()
        return context

    def form_valid(self, form):
        tenant = self.get_tenant()
        data = form.cleaned_data
        
        # Atualiza Configurações
        TenantProvisioningService.update_config(tenant, data)
        
        return redirect("tenants:onboarding_step_4")


class Step4ProvisionView(OnboardingSessionMixin, TemplateView):
    template_name = "tenants/onboarding/step_4_provision.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.get_tenant()
        context['tenant'] = tenant
        return context

    def post(self, request, *args, **kwargs):
        """Action AJAX para finalizar o setup"""
        tenant = self.get_tenant()
        if not tenant:
             return JsonResponse({"error": "Sessão expirada"}, status=400)
             
        try:
            redirect_url = TenantProvisioningService.activate_tenant(tenant)
            
            # Limpa sessão
            if "onboarding_tenant_id" in request.session:
                del request.session["onboarding_tenant_id"]
                
            return JsonResponse({"redirect_url": redirect_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(never_cache, name='dispatch')
class CheckSlugView(View):
    def get(self, request):
        slug = request.GET.get("slug", "").strip().lower()
        if not slug:
            return JsonResponse({"available": False, "error": "Slug vazio"})
            
        reserved = [
            'admin', 'api', 'www', 'app', 'painel', 'dashboard',
            'public', 'static', 'media', 'tenant', 'setup'
        ]
        
        if slug in reserved:
            return JsonResponse({"available": False, "message": "Reservado"})

        is_taken = Tenant.objects.filter(slug=slug).exists()
        
        return JsonResponse({
            "available": not is_taken,
            "slug": slug
        })
