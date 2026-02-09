from dataclasses import asdict
from typing import Any

import requests
from decouple import config as decouple_config
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView, UpdateView

from smart_core_assistant_painel.modules.services.config import (
    get_config_or_default,
)

from ..forms import (
    TenantConfigForm,
    TenantDatabaseForm,
    TenantEvolutionForm,
    TenantSignupForm,
    TenantTrelloForm,
)
from ..models import (
    Subscription,
    Tenant,
    TenantConfig,
    TenantDatabase,
    TenantEvolution,
    TenantTrello,
)
from ..services.config_loader import ConfigLoader
from ..services.connection_tester import (
    ConnectionTester,
    TenantMigrationRunner,
)


def _resolve_tenant_and_profile(request):
    """Resolve tenant e perfil do usuário atual para validação de permissões."""
    tenant = Tenant.objects.filter(owner=request.user).first()
    tenant_profile = None

    if not tenant:
        try:
            tenant_profile = request.user.tenant_profile
            tenant = tenant_profile.tenant
        except Exception:
            tenant = None
            tenant_profile = None
    else:
        try:
            profile = request.user.tenant_profile
            if profile.tenant == tenant and profile.is_active:
                tenant_profile = profile
        except Exception:
            tenant_profile = None

    return tenant, tenant_profile


def _can_edit_tenant_configs(request, tenant, tenant_profile=None) -> bool:
    """Retorna True se o usuário pode editar configurações do tenant."""
    user = request.user

    if user.is_superuser:
        return True
    if tenant and user == tenant.owner:
        return True

    if tenant_profile is None:
        try:
            tenant_profile = user.tenant_profile
        except Exception:
            tenant_profile = None

    if not tenant_profile or not tenant_profile.is_active:
        return False

    if tenant and tenant_profile.tenant != tenant:
        return False

    # Compatibilidade: alguns registros antigos podem ter apenas "view=True"
    # para configuracoes; nesses casos, tratamos como permissão de edição.
    return tenant_profile.has_module_permission(
        "configuracoes", "edit"
    ) or tenant_profile.has_module_permission("configuracoes", "view")


class TenantSignupView(FormView):
    template_name = "tenants/signup.html"
    form_class = TenantSignupForm
    success_url = reverse_lazy("tenants:dashboard")

    def form_valid(self, form):
        data = form.cleaned_data

        try:
            with transaction.atomic():
                # 1. Create User
                user = User.objects.create_user(
                    username=data["email"],
                    email=data["email"],
                    password=data["password"],
                    first_name=data["full_name"],
                )

                # 2. Create Tenant
                tenant = Tenant.objects.create(
                    name=data["company_name"],
                    slug=data["slug"],
                    owner=user,
                    active=True,
                )

                # 3. Update Subscription (created by signal)
                # Ensure subscription has the correct plan
                # Note: Signal creates subscription with no plan or default. We want to explicit set it.
                subscription = tenant.subscription
                subscription.plan = data["plan"]
                subscription.status = Subscription.Status.ACTIVE
                subscription.save()

                # Login user
                login(self.request, user)

                messages.success(
                    self.request,
                    _("Cadastro realizado com sucesso! Bem-vindo."),
                )
                return super().form_valid(form)

        except Exception as e:
            form.add_error(None, f"Erro ao processar cadastro: {str(e)}")
            return self.form_invalid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "tenants/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Buscar tenant via owner OU TenantUser
        tenant = Tenant.objects.filter(owner=self.request.user).first()
        if not tenant:
            try:
                tenant_user = self.request.user.tenant_profile
                tenant = tenant_user.tenant
            except Exception:
                pass
        if tenant:
            context["tenant"] = tenant
            context["subscription"] = getattr(tenant, "subscription", None)
            context["database"] = getattr(tenant, "database_config", None)
            context["evolution"] = getattr(tenant, "evolution_config", None)
            context["trello"] = getattr(tenant, "trello_config", None)
        return context


class BaseTenantConfigView(LoginRequiredMixin, UpdateView):
    template_name = "tenants/config_form.html"
    success_url = reverse_lazy("tenants:dashboard")

    def get_object(self, queryset=None):
        # Tenta encontrar tenant via owner OU via TenantUser
        tenant, _tenant_profile = _resolve_tenant_and_profile(self.request)
        if not tenant:
            from django.http import Http404

            raise Http404("Tenant não encontrado para este usuário.")
        return self.get_config_object(tenant)

    def get_config_object(self, tenant):
        raise NotImplementedError

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Verificar permissões de edição
        can_edit = False
        reason = "Acesso restrito"

        try:
            user = self.request.user
            tenant = self.object.tenant

            # 1. Se for owner do tenant, pode editar
            if user == tenant.owner:
                can_edit = True
                reason = ""

            # 2. Se for superuser do Django, sempre pode editar
            elif user.is_superuser:
                can_edit = True
                reason = ""

            # 3. Verificar permissão modular (configuracoes)
            elif _can_edit_tenant_configs(self.request, tenant):
                can_edit = True
                reason = ""

            else:
                reason = "Seu perfil não possui permissão de edição em Configurações"

        except Exception as e:
            # Fallback seguro - bloqueia edição em caso de erro
            can_edit = False
            reason = f"Erro ao verificar permissões: {str(e)}"

        if not can_edit:
            for field in form.fields.values():
                field.disabled = True

            # Adicionar mensagem informativa (apenas GET para não floodar)
            if self.request.method == "GET":
                messages.info(self.request, f"Modo de visualização: {reason}.")

        return form

    def form_valid(self, form):
        tenant = self.object.tenant
        if not _can_edit_tenant_configs(self.request, tenant):
            messages.error(
                self.request,
                _("Você não tem permissão para editar configurações."),
            )
            return self.form_invalid(form)
        messages.success(self.request, _("Configurações salvas com sucesso."))
        return super().form_valid(form)


class EvolutionConfigView(BaseTenantConfigView):
    model = TenantEvolution
    form_class = TenantEvolutionForm
    template_name = "tenants/config_evolution.html"

    def get_config_object(self, tenant):
        # Ensure object exists
        obj, _ = TenantEvolution.objects.get_or_create(tenant=tenant)
        return obj


class TrelloConfigView(BaseTenantConfigView):
    model = TenantTrello
    form_class = TenantTrelloForm
    template_name = "tenants/config_trello.html"

    def get_config_object(self, tenant: Tenant) -> TenantTrello:
        obj, _ = TenantTrello.objects.get_or_create(tenant=tenant)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_object_or_404(Tenant, owner=self.request.user)
        config = self.get_config_object(tenant)
        context["webhook_registered"] = bool(config.webhook_id)

        # Usar URL pública do ngrok (se configurada) ou fallback para local
        base_url = decouple_config(
            "TRELLO_WEBHOOK_CALLBACK_URL",
            default=self.request.build_absolute_uri("/")[:-1],
        )
        # Remove trailing slash se houver
        base_url = base_url.rstrip("/")
        context["callback_url"] = (
            f"{base_url}/api/trello_sync/webhook/{tenant.slug}/"
        )

        return context


class AIConfigView(BaseTenantConfigView):
    """View para configuração de IA e prompts do Tenant."""

    model = TenantConfig
    form_class = TenantConfigForm
    template_name = "tenants/config_ai.html"

    def get_config_object(self, tenant: Tenant) -> TenantConfig:
        obj, _ = TenantConfig.objects.get_or_create(tenant=tenant)
        return obj


class DatabaseConfigView(BaseTenantConfigView):
    """View para configuração do PostgreSQL do Tenant."""

    model = TenantDatabase
    form_class = TenantDatabaseForm
    template_name = "tenants/config_database.html"

    def get_config_object(self, tenant: Tenant) -> TenantDatabase:
        obj, _ = TenantDatabase.objects.get_or_create(
            tenant=tenant,
            defaults={
                "host": "",
                "port": 5432,
                "database_name": "smartcore_db",
                "username": "smartcore",
                "_password": "",
                "ssl_mode": "disable",
            },
        )
        return obj


class TestConnectionView(LoginRequiredMixin, View):
    """View para testar conexões com serviços de integração."""

    def post(self, request, service_type: str) -> JsonResponse:
        tenant, tenant_profile = _resolve_tenant_and_profile(request)
        if not tenant:
            return JsonResponse(
                {"success": False, "message": "Tenant não encontrado"},
                status=404,
            )
        if not _can_edit_tenant_configs(request, tenant, tenant_profile):
            return JsonResponse(
                {"success": False, "message": "Sem permissão para esta ação"},
                status=403,
            )
        success = False
        message = "Serviço desconhecido"

        if service_type == "evolution":
            config = getattr(tenant, "evolution_config", None)
            if config:
                success = ConnectionTester.test_evolution_connection(config)
                if success:
                    config.connection_valid = True
                    config.save()
                message = (
                    "Conexão bem-sucedida" if success else "Falha na conexão"
                )
            else:
                message = "Configuração não encontrada"

        elif service_type == "trello":
            config = getattr(tenant, "trello_config", None)
            if config:
                success = ConnectionTester.test_trello_connection(config)
                if success:
                    config.connection_valid = True
                    config.save()
                message = (
                    "Conexão bem-sucedida" if success else "Falha na conexão"
                )
            else:
                message = "Configuração não encontrada"

        elif service_type == "database":
            config = getattr(tenant, "database_config", None)
            if config:
                success = ConnectionTester.test_postgres_connection(config)
                if success:
                    config.connection_valid = True
                    config.save()
                message = (
                    "Conexão bem-sucedida" if success else "Falha na conexão"
                )
            else:
                message = "Configuração não encontrada"

        return JsonResponse({"success": success, "message": message})


class RunMigrationsView(LoginRequiredMixin, View):
    """View para executar migrations no banco do tenant."""

    def post(self, request) -> JsonResponse:
        tenant, tenant_profile = _resolve_tenant_and_profile(request)
        if not tenant:
            return JsonResponse(
                {"success": False, "message": "Tenant não encontrado"},
                status=404,
            )
        if not _can_edit_tenant_configs(request, tenant, tenant_profile):
            return JsonResponse(
                {"success": False, "message": "Sem permissão para esta ação"},
                status=403,
            )
        config = getattr(tenant, "database_config", None)

        if not config:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Configure o banco de dados primeiro",
                },
                status=400,
            )

        if not config.host or not config.database_name:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Dados de conexão incompletos",
                },
                status=400,
            )

        success, message = TenantMigrationRunner.run_migrations(config)

        return JsonResponse({"success": success, "message": message})


class ConfigDebugView(LoginRequiredMixin, TemplateView):
    """View para debug e conferência das configurações carregadas.

    Exibe todas as configurações do RuntimeConfig de forma estruturada,
    permitindo conferir se as configs Core e Tenant estão sendo mescladas
    corretamente.
    """

    template_name = "tenants/config_debug.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)

        # Buscar o tenant do usuário logado
        tenant = Tenant.objects.filter(owner=self.request.user).first()

        if tenant:
            # Carregar configurações para o contexto atual
            ConfigLoader.load_for_request(tenant)

            # Obter o RuntimeConfig atual
            runtime_config = get_config_or_default()

            # Converter para dicionário para exibição
            config_dict = asdict(runtime_config)

            # Organizar configs por categoria
            context["tenant"] = tenant
            context["config_loaded"] = True

            # ===================================================
            # SEÇÃO 1: CONFIGURAÇÕES DO TENANT (Editáveis)
            # ===================================================

            # Prompts personalizados pelo cliente
            # Mapeamento: dados_empresa (tenant) → prompt_system_dados_empresa
            # Mapeamento: persona_bot (tenant) → prompt_system_analise_mensagem
            context["tenant_prompts"] = {
                "prompt_system_dados_empresa": config_dict.get(
                    "prompt_system_dados_empresa", ""
                ),
                "prompt_system_analise_mensagem": config_dict.get(
                    "prompt_system_analise_mensagem", ""
                ),
            }

            # Mensagens do tenant (editáveis)
            context["tenant_mensagens"] = {
                "msg_fallback_sem_info": config_dict.get(
                    "msg_fallback_sem_info", ""
                ),
                "msg_fallback_geral": config_dict.get(
                    "msg_fallback_geral", ""
                ),
                "msg_transferencia_generica": config_dict.get(
                    "msg_transferencia_generica", ""
                ),
            }

            # Extração de entidades (configurável pelo tenant)
            context["tenant_entidades"] = {
                "valid_entity_types": config_dict.get(
                    "valid_entity_types", ""
                ),
            }

            # Configurações avançadas do tenant (LLM e API Keys personalizadas)
            try:
                tenant_config = tenant.config
                context["tenant_llm_custom"] = {
                    "llm_class": tenant_config.llm_class
                    or "(usa configuração global)",
                    "model": tenant_config.model
                    or "(usa configuração global)",
                }
                # Verificar se tem API keys personalizadas
                has_custom_keys = bool(tenant_config.api_keys)
                context["tenant_has_custom_api_keys"] = has_custom_keys
            except Exception:
                context["tenant_llm_custom"] = {
                    "llm_class": "(usa configuração global)",
                    "model": "(usa configuração global)",
                }
                context["tenant_has_custom_api_keys"] = False

            # ===================================================
            # SEÇÃO 2: CONFIGURAÇÕES DO CORE (Globais/Sistema)
            # ===================================================

            # API Keys (do Core, mascaradas)
            context["core_api_keys"] = {
                "groq_api_key": _mask_key(config_dict.get("groq_api_key", "")),
                "openai_api_key": _mask_key(
                    config_dict.get("openai_api_key", "")
                ),
                "huggingface_api_key": _mask_key(
                    config_dict.get("huggingface_api_key", "")
                ),
            }

            # LLM Settings (do Core)
            context["core_llm"] = {
                "llm_class": config_dict.get("llm_class", ""),
                "model": config_dict.get("model", ""),
                "llm_temperature": config_dict.get("llm_temperature", 0),
            }

            # Embeddings (do Core)
            context["core_embeddings"] = {
                "embeddings_class": config_dict.get("embeddings_class", ""),
                "embeddings_model": config_dict.get("embeddings_model", ""),
                "chunk_size": config_dict.get("chunk_size", 0),
                "chunk_overlap": config_dict.get("chunk_overlap", 0),
            }

            # Thresholds (do Core)
            context["core_thresholds"] = {
                "similarity_threshold": config_dict.get(
                    "similarity_threshold", 0.0
                ),
                "vector_distance_threshold": config_dict.get(
                    "vector_distance_threshold", 0.0
                ),
                "time_cache": config_dict.get("time_cache", 0),
            }

            # Prompts globais do Core (não editáveis pelo tenant)
            # Nota: prompt_system_analise_mensagem agora é do Tenant
            context["core_prompts"] = {
                "prompt_system_analise_previa_mensagem": config_dict.get(
                    "prompt_system_analise_previa_mensagem", ""
                ),
                "prompt_human_analise_previa_mensagem": config_dict.get(
                    "prompt_human_analise_previa_mensagem", ""
                ),
                "prompt_system_melhoria_conteudo": config_dict.get(
                    "prompt_system_melhoria_conteudo", ""
                ),
                "prompt_human_melhoria_conteudo": config_dict.get(
                    "prompt_human_melhoria_conteudo", ""
                ),
                "prompt_system_analise_conteudo": config_dict.get(
                    "prompt_system_analise_conteudo", ""
                ),
                "prompt_human_analise_conteudo": config_dict.get(
                    "prompt_human_analise_conteudo", ""
                ),
                "prompt_intent_system": config_dict.get(
                    "prompt_intent_system", ""
                ),
                "prompt_intent_footer": config_dict.get(
                    "prompt_intent_footer", ""
                ),
                "prompt_template_user_rag": config_dict.get(
                    "prompt_template_user_rag", ""
                ),
                "prompt_regras_resposta": config_dict.get(
                    "prompt_regras_resposta", ""
                ),
                "prompt_regras_transferencia": config_dict.get(
                    "prompt_regras_transferencia", ""
                ),
            }

        else:
            context["config_loaded"] = False
            context["error"] = "Nenhum tenant encontrado para este usuário."

        return context


def _mask_key(key: str) -> str:
    """Mascara uma API key para exibição segura."""
    if not key:
        return "(não configurada)"
    if len(key) <= 8:
        return "****"

    return f"{key[:4]}...{key[-4:]}"


class RegisterTrelloWebhookView(LoginRequiredMixin, View):
    def post(self, request) -> JsonResponse:
        tenant = get_object_or_404(Tenant, owner=request.user)
        config = getattr(tenant, "trello_config", None)

        if not config or not config.api_key:
            return JsonResponse(
                {"error": "Configure as credenciais primeiro"}, status=400
            )

        # Usar URL pública do ngrok (se configurada) ou fallback para local
        # Isso é necessário pois o Trello precisa validar a URL de callback
        base_url = decouple_config(
            "TRELLO_WEBHOOK_CALLBACK_URL",
            default=request.build_absolute_uri("/")[:-1],
        )
        # Remove trailing slash se houver
        base_url = base_url.rstrip("/")
        callback_url = f"{base_url}/api/trello_sync/webhook/{tenant.slug}/"

        # Registrar webhook na API do Trello
        register_url = (
            f"https://api.trello.com/1/tokens/{config.token}/webhooks/"
        )
        payload = {
            "key": config.api_key,
            "callbackURL": callback_url,
            "idModel": config.workspace_id,
            "description": f"Smart Assistant Webhook - {tenant.name}",
        }

        try:
            response = requests.post(register_url, json=payload)

            if response.status_code == 200:
                data = response.json()
                config.webhook_id = data.get("id")
                config.webhook_callback_url = callback_url
                config.save()
                return JsonResponse({"success": True})
            else:
                # Tentar ler erro
                try:
                    error_msg = response.json()
                except Exception:
                    error_msg = response.text
                return JsonResponse(
                    {"error": f"Erro Trello: {error_msg}"}, status=400
                )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class DeleteTrelloWebhookView(LoginRequiredMixin, View):
    """View para deletar o webhook do Trello existente.

    Comentário (PT-BR): Permite que o usuário remova o webhook existente
    para poder re-registrar com a URL correta (incluindo tenant_slug).
    """

    def post(self, request) -> JsonResponse:
        tenant = get_object_or_404(Tenant, owner=request.user)
        config = getattr(tenant, "trello_config", None)

        if not config:
            return JsonResponse(
                {"error": "Configuração do Trello não encontrada"}, status=400
            )

        if not config.webhook_id:
            return JsonResponse(
                {"error": "Nenhum webhook registrado"}, status=400
            )

        # Deletar webhook na API do Trello
        delete_url = (
            f"https://api.trello.com/1/webhooks/{config.webhook_id}"
            f"?key={config.api_key}&token={config.token}"
        )

        try:
            response = requests.delete(delete_url)

            # Trello retorna 200 se o webhook foi deletado com sucesso
            # e 404 se o webhook não existe mais
            if response.status_code in (200, 404):
                # Limpar dados do webhook no banco
                config.webhook_id = ""
                config.webhook_callback_url = ""
                config.save()
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Webhook removido com sucesso",
                    }
                )
            else:
                try:
                    error_msg = response.json()
                except Exception:
                    error_msg = response.text
                return JsonResponse(
                    {"error": f"Erro ao deletar webhook: {error_msg}"},
                    status=400,
                )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
