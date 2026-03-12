"""Views para gerenciamento de instâncias Evolution API.

Permite listar, criar, conectar (QR Code), configurar webhook,
desconectar e excluir instâncias diretamente pelo painel.
"""

import logging
import re
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from smart_core_assistant_painel.app.tenants.models import (
    Tenant,
    TenantEvolution,
)
from smart_core_assistant_painel.app.tenants.views.legacy_views import (
    _can_edit_tenant_configs,
    _resolve_tenant_and_profile,
)

from .models import EvolutionInstance
from .services.evolution_api import EvolutionWhatsAppService

logger = logging.getLogger(__name__)

# Validação de nome de instância: alfanumérico + hífen, 3-50 chars
INSTANCE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-]{1,48}[a-zA-Z0-9]$")


def _get_tenant_and_config(
    request: HttpRequest,
) -> tuple[Tenant | None, TenantEvolution | None, bool]:
    """Resolve tenant, config Evolution e permissão de edição."""
    tenant, profile = _resolve_tenant_and_profile(request)
    if not tenant:
        return None, None, False

    evo_config = getattr(tenant, "evolution_config", None)
    can_edit = _can_edit_tenant_configs(request, tenant, profile)
    return tenant, evo_config, can_edit


def _build_webhook_url(request: HttpRequest, tenant: Tenant) -> str:
    """Gera URL do webhook para o tenant."""
    base_domain: str = getattr(settings, "TENANT_BASE_DOMAIN", "")
    if base_domain:
        base_url = f"https://{base_domain}"
    else:
        base_url = request.build_absolute_uri("/").rstrip("/")
    return f"{base_url}/sync/evolution/webhook/{tenant.slug}/"


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"success": False, "message": message}, status=status)


class InstanceListView(LoginRequiredMixin, TemplateView):
    """Lista instâncias Evolution do tenant."""

    template_name = "evolution_sync/instance_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        tenant, evo_config, can_edit = _get_tenant_and_config(self.request)

        context["tenant"] = tenant
        context["evo_config"] = evo_config
        context["can_edit"] = can_edit
        context["instances"] = []

        if tenant and evo_config:
            context["instances"] = list(
                EvolutionInstance.objects.filter(active=True)
            )
            context["webhook_url"] = _build_webhook_url(self.request, tenant)
        return context


class InstanceCreateView(LoginRequiredMixin, View):
    """Cria instância na Evolution API e salva no banco do tenant."""

    def post(self, request: HttpRequest) -> JsonResponse:
        tenant, evo_config, can_edit = _get_tenant_and_config(request)

        if not tenant or not evo_config:
            return _json_error("Configuração Evolution não encontrada.", 404)
        if not can_edit:
            return _json_error("Sem permissão para esta ação.", 403)
        if not evo_config.server_url or not evo_config.api_key:
            return _json_error(
                "Configure servidor e API key da Evolution primeiro."
            )

        import json

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return _json_error("Body inválido.")

        instance_name = str(data.get("instance_name", "")).strip()
        if not INSTANCE_NAME_RE.match(instance_name):
            return _json_error(
                "Nome inválido. Use 3-50 caracteres alfanuméricos "
                "ou hífen (não pode iniciar/terminar com hífen)."
            )

        webhook_url = _build_webhook_url(request, tenant)
        service = EvolutionWhatsAppService()

        try:
            result = service.create_instance(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                instance_name=instance_name,
                webhook_url=webhook_url,
            )
        except Exception as e:
            logger.error(f"Erro ao criar instância: {e}")
            return _json_error(f"Erro na API Evolution: {e}", 502)

        instance_data = result.get("instance", {})
        hash_data = result.get("hash", {})

        instance = EvolutionInstance.objects.create(
            tenant_id=tenant.id,
            name=instance_name,
            instance_id=instance_data.get("instanceId", ""),
            api_key=hash_data.get("apikey", ""),
            connection_state="close",
        )

        return JsonResponse(
            {
                "success": True,
                "instance": {
                    "id": instance.pk,
                    "name": instance.name,
                    "instance_id": instance.instance_id,
                },
            },
            status=201,
        )


class InstanceDetailView(LoginRequiredMixin, TemplateView):
    """Detalhe de instância com QR Code e configuração de webhook."""

    template_name = "evolution_sync/instance_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        tenant, evo_config, can_edit = _get_tenant_and_config(self.request)

        context["tenant"] = tenant
        context["evo_config"] = evo_config
        context["can_edit"] = can_edit

        pk = self.kwargs.get("pk")
        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            context["instance"] = None
            return context

        # Buscar estado atual na API
        if evo_config and evo_config.server_url and evo_config.api_key:
            service = EvolutionWhatsAppService()
            try:
                state_data = service.get_connection_state(
                    base_url=evo_config.server_url,
                    api_key=evo_config.api_key,
                    instance_name=instance.name,
                )
                state = state_data.get("instance", {}).get("state", "unknown")
                instance.connection_state = state
                instance.last_state_check = timezone.now()
                instance.save(
                    update_fields=["connection_state", "last_state_check"]
                )
            except Exception as e:
                logger.warning(f"Erro ao verificar estado: {e}")

        context["instance"] = instance
        if tenant:
            context["webhook_url"] = _build_webhook_url(self.request, tenant)
        return context


class InstanceQRCodeView(LoginRequiredMixin, View):
    """Retorna QR Code (base64) para conexão via AJAX."""

    def get(self, request: HttpRequest, pk: int) -> JsonResponse:
        tenant, evo_config, _ = _get_tenant_and_config(request)
        if not evo_config or not evo_config.server_url:
            return _json_error("Config Evolution não encontrada.", 404)

        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        service = EvolutionWhatsAppService()
        try:
            result = service.connect_instance(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                instance_name=instance.name,
            )
        except Exception as e:
            logger.error(f"Erro ao gerar QR code: {e}")
            return _json_error(f"Erro na API: {e}", 502)

        return JsonResponse(
            {
                "base64": result.get("base64", ""),
                "pairingCode": result.get("pairingCode", ""),
                "count": result.get("count", 0),
            }
        )


class InstanceConnectionStateView(LoginRequiredMixin, View):
    """Retorna estado de conexão da instância via AJAX."""

    def get(self, request: HttpRequest, pk: int) -> JsonResponse:
        tenant, evo_config, _ = _get_tenant_and_config(request)
        if not evo_config or not evo_config.server_url:
            return _json_error("Config Evolution não encontrada.", 404)

        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        service = EvolutionWhatsAppService()
        try:
            state_data = service.get_connection_state(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                instance_name=instance.name,
            )
            state = state_data.get("instance", {}).get("state", "unknown")

            instance.connection_state = state
            instance.last_state_check = timezone.now()
            instance.save(
                update_fields=["connection_state", "last_state_check"]
            )
        except Exception as e:
            logger.warning(f"Erro ao verificar estado: {e}")
            state = "unknown"

        return JsonResponse(
            {
                "state": state,
                "instanceName": instance.name,
            }
        )


class InstanceWebhookView(LoginRequiredMixin, View):
    """Configura/reconfigura webhook de uma instância."""

    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        tenant, evo_config, can_edit = _get_tenant_and_config(request)

        if not tenant or not evo_config:
            return _json_error("Config Evolution não encontrada.", 404)
        if not can_edit:
            return _json_error("Sem permissão para esta ação.", 403)

        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        webhook_url = _build_webhook_url(request, tenant)
        service = EvolutionWhatsAppService()

        try:
            service.set_webhook(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                instance_name=instance.name,
                webhook_url=webhook_url,
            )
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")
            return _json_error(f"Erro na API: {e}", 502)

        return JsonResponse(
            {
                "success": True,
                "message": "Webhook configurado com sucesso.",
                "webhook_url": webhook_url,
            }
        )


class InstanceDeleteView(LoginRequiredMixin, View):
    """Deleta instância da API Evolution e remove do banco."""

    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        tenant, evo_config, can_edit = _get_tenant_and_config(request)

        if not tenant or not evo_config:
            return _json_error("Config Evolution não encontrada.", 404)
        if not can_edit:
            return _json_error("Sem permissão para esta ação.", 403)

        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        service = EvolutionWhatsAppService()

        try:
            service.delete_instance(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                instance_name=instance.name,
            )
        except Exception as e:
            logger.warning(f"Erro ao deletar na API (continuando): {e}")

        instance.active = False
        instance.save(update_fields=["active"])

        return JsonResponse(
            {
                "success": True,
                "message": f"Instância '{instance.name}' removida.",
            }
        )


class InstanceLogoutView(LoginRequiredMixin, View):
    """Desconecta instância do WhatsApp sem deletar."""

    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        tenant, evo_config, can_edit = _get_tenant_and_config(request)

        if not tenant or not evo_config:
            return _json_error("Config Evolution não encontrada.", 404)
        if not can_edit:
            return _json_error("Sem permissão para esta ação.", 403)

        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        service = EvolutionWhatsAppService()

        try:
            service.logout_instance(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                instance_name=instance.name,
            )
        except Exception as e:
            logger.error(f"Erro ao desconectar: {e}")
            return _json_error(f"Erro na API: {e}", 502)

        instance.connection_state = "close"
        instance.last_state_check = timezone.now()
        instance.save(update_fields=["connection_state", "last_state_check"])

        return JsonResponse(
            {
                "success": True,
                "message": f"Instância '{instance.name}' desconectada.",
            }
        )


class RefreshAllStatusView(LoginRequiredMixin, View):
    """Atualiza status de todas as instâncias do tenant em batch."""

    def post(self, request: HttpRequest) -> JsonResponse:
        tenant, evo_config, _ = _get_tenant_and_config(request)
        if not tenant or not evo_config:
            return _json_error("Config Evolution não encontrada.", 404)
        if not evo_config.server_url or not evo_config.api_key:
            return _json_error("Servidor Evolution não configurado.")

        service = EvolutionWhatsAppService()
        instances = list(EvolutionInstance.objects.filter(active=True))
        updated: list[dict[str, Any]] = []

        for instance in instances:
            try:
                state_data = service.get_connection_state(
                    base_url=evo_config.server_url,
                    api_key=evo_config.api_key,
                    instance_name=instance.name,
                )
                state = state_data.get("instance", {}).get("state", "unknown")
            except Exception:
                state = "unknown"

            instance.connection_state = state
            instance.last_state_check = timezone.now()
            instance.save(
                update_fields=["connection_state", "last_state_check"]
            )
            updated.append(
                {
                    "id": instance.pk,
                    "name": instance.name,
                    "state": state,
                }
            )

        return JsonResponse(
            {
                "success": True,
                "instances": updated,
            }
        )
