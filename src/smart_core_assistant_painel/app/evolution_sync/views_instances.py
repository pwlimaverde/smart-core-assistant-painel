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
from .services import EvolutionGoAdapter

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


def _parse_state(state_data: dict[str, Any]) -> str:
    """Extrai o estado de conexão da resposta do Evolution Go.

    O ``GET /instance/status`` do Go retorna o formato aninhado
    ``{"data": {"Connected": bool, "LoggedIn": bool, "Name": str}}``:
    - ``LoggedIn=True``  → sessão WhatsApp autenticada → ``"open"``.
    - caso contrário     → ainda não pareada → ``"close"``.

    Mantém fallback para os formatos ``{"state": "open"}`` e
    ``{"instance": {"state": ...}}`` por robustez.
    """
    data = state_data.get("data") if isinstance(state_data, dict) else None
    if isinstance(data, dict) and ("LoggedIn" in data or "Connected" in data):
        return "open" if data.get("LoggedIn") else "close"

    state = state_data.get("state")
    if not state:
        state = state_data.get("instance", {}).get("state", "unknown")
    return str(state or "unknown")


class InstanceListView(LoginRequiredMixin, TemplateView):
    """Lista instâncias Evolution do tenant."""

    template_name = "apps/evolution_sync/instance_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        tenant, evo_config, can_edit = _get_tenant_and_config(self.request)

        context["tenant"] = tenant
        context["evo_config"] = evo_config
        context["can_edit"] = can_edit
        context["instances"] = []

        if tenant and evo_config:
            from smart_core_assistant_painel.app.operacional.models import (
                AppInstance,
                Departamento,
            )

            instances = list(EvolutionInstance.objects.filter(active=True))

            # Busca resposta_bot e departamento do AppInstance
            api_keys = [i.api_key for i in instances]
            app_instances = AppInstance.objects.filter(
                api_key__in=api_keys, active=True
            ).select_related("departamento", "owner")
            app_map: dict[str, AppInstance] = {
                ai.api_key: ai for ai in app_instances
            }
            for inst in instances:
                app_inst = app_map.get(inst.api_key)
                inst.bot_active = (  # type: ignore # atributo dinâmico
                    app_inst.resposta_bot if app_inst else True
                )
                if app_inst and app_inst.departamento:
                    inst.departamento_nome = app_inst.departamento.nome  # type: ignore # dinâmico
                    inst.departamento_id = app_inst.departamento.id  # type: ignore # dinâmico
                else:
                    inst.departamento_nome = None  # type: ignore
                    inst.departamento_id = None  # type: ignore

                if app_inst and app_inst.owner:
                    inst.owner_id = app_inst.owner.id  # type: ignore
                else:
                    inst.owner_id = None  # type: ignore

            context["instances"] = instances
            context["webhook_url"] = _build_webhook_url(self.request, tenant)

            # Dados para o modal de criação
            context["departamentos"] = list(
                Departamento.objects.filter(ativo=True).values("id", "nome")
            )
        return context


class InstanceCreateView(LoginRequiredMixin, View):
    """Cria instância na Evolution API e salva no banco do tenant.

    Recebe no body JSON:
        - instance_name: Nome da instância (obrigatório)
        - resposta_bot: Se o bot deve responder (default: True)
        - departamento_id: ID do departamento para vincular (opcional)
        - owner_id: ID do atendente responsável (opcional)
    """

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
        resposta_bot = bool(data.get("resposta_bot", True))
        departamento_id = data.get("departamento_id")
        owner_id = data.get("owner_id")

        if not INSTANCE_NAME_RE.match(instance_name):
            return _json_error(
                "Nome inválido. Use 3-50 caracteres alfanuméricos "
                "ou hífen (não pode iniciar/terminar com hífen)."
            )

        # Log de diagnóstico para rastreamento de problemas de API
        api_key_preview = (
            evo_config.api_key[:6] if evo_config.api_key else "VAZIO"
        )
        logger.info(
            "Criando instância '%s' no servidor '%s' (api_key: %s..., len=%d)",
            instance_name,
            evo_config.server_url,
            api_key_preview,
            len(evo_config.api_key),
        )

        service = EvolutionGoAdapter()

        # O Evolution Go exige um ``token`` no POST /instance/create
        # (retorna 400 "token is required" se ausente). Geramos o token
        # aqui — ele se torna o ``api_key`` da instância e é usado como
        # header ``apikey`` nas operações de instância (qr/status/send).
        import uuid

        instance_token = uuid.uuid4().hex

        try:
            result = service.create_instance(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                name=instance_name,
                token=instance_token,
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Falha ao criar instância '%s': %s",
                instance_name,
                error_msg,
            )
            # Mensagem amigável para erro 401
            if "401" in error_msg or "Unauthorized" in error_msg:
                return _json_error(
                    "API Key inválida ou expirada. Verifique a "
                    "configuração da Evolution API em "
                    "Configurações > Evolution.",
                    502,
                )
            return _json_error(f"Erro na API Evolution: {error_msg}", 502)

        # O Evolution Go pode retornar o token da instância no topo
        # (``token``), dentro de ``hash`` (string ou dict ``{apikey}``) ou
        # dentro de ``instance``. Extrai de forma tolerante ao formato.
        instance_data = result.get("instance", {}) or {}
        hash_data = result.get("hash", {})

        token = (
            result.get("token")
            or instance_data.get("token")
            or (
                hash_data.get("apikey")
                if isinstance(hash_data, dict)
                else hash_data
            )
            or instance_token
        )
        instance_id = (
            instance_data.get("instanceId")
            or instance_data.get("id")
            or result.get("instanceId")
            or result.get("id")
            or ""
        )

        instance = EvolutionInstance.objects.create(
            tenant_id=tenant.id,
            name=instance_name,
            instance_id=str(instance_id) or None,
            api_key=str(token),
            connection_state="close",
        )

        # Mantém a sessão sempre online (mecanismo documentado do Evolution GO),
        # evitando que o websocket caia por ociosidade e pare os webhooks.
        if instance_id:
            try:
                service.set_advanced_settings(
                    base_url=evo_config.server_url,
                    api_key=str(token),
                    instance_id=str(instance_id),
                    always_online=True,
                    read_messages=False,
                )
            except Exception as e:
                logger.warning(
                    "Não foi possível ativar alwaysOnline para '%s': %s",
                    instance_name,
                    e,
                )

        from smart_core_assistant_painel.app.operacional.models import (
            AppInstance,
            Atendente,
            Departamento,
        )

        # Monta defaults para o AppInstance
        app_defaults: dict[str, Any] = {
            "channel": "evolution_api",
            "display_name": instance.name,
            "resposta_bot": resposta_bot,
            "active": True,
        }

        # Vincula departamento se fornecido
        if departamento_id:
            dept = Departamento.objects.filter(
                id=departamento_id, ativo=True
            ).first()
            if dept:
                app_defaults["departamento"] = dept

        # Vincula owner se fornecido
        if owner_id:
            owner = Atendente.objects.filter(id=owner_id, ativo=True).first()
            if owner:
                app_defaults["owner"] = owner

        app_inst, _ = AppInstance.objects.update_or_create(
            api_key=instance.api_key,
            defaults=app_defaults,
        )

        logger.info(
            "Instância '%s' criada com sucesso (dept=%s, owner=%s)",
            instance.name,
            getattr(app_inst.departamento, "nome", None),
            getattr(app_inst.owner, "nome", None),
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

    template_name = "apps/evolution_sync/instance_detail.html"

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
            service = EvolutionGoAdapter()
            try:
                state_data = service.get_status(
                    base_url=evo_config.server_url,
                    api_key=instance.api_key,
                    name=instance.name,
                )
                state = _parse_state(state_data)
                instance.connection_state = state
                instance.last_state_check = timezone.now()
                instance.save(
                    update_fields=["connection_state", "last_state_check"]
                )
            except Exception as e:
                logger.warning(f"Erro ao verificar estado: {e}")

        # Busca resposta_bot do AppInstance vinculado
        from smart_core_assistant_painel.app.operacional.models import (
            AppInstance,
        )

        app_inst = AppInstance.objects.filter(
            api_key=instance.api_key, active=True
        ).first()
        instance.bot_active = (  # type: ignore[attr-defined]
            app_inst.resposta_bot if app_inst else True
        )

        context["instance"] = instance
        if tenant:
            context["webhook_url"] = _build_webhook_url(self.request, tenant)
        return context


class InstanceQRCodeView(LoginRequiredMixin, View):
    """Retorna QR Code (base64) para conexão via AJAX."""

    def get(self, request: HttpRequest, pk: int) -> JsonResponse:
        tenant, evo_config, _ = _get_tenant_and_config(request)
        if not tenant or not evo_config or not evo_config.server_url:
            return _json_error("Config Evolution não encontrada.", 404)

        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        webhook_url = _build_webhook_url(request, tenant)
        service = EvolutionGoAdapter()
        try:
            # 1. /instance/connect (token da instância) configura webhook +
            #    eventos e inicia o pareamento. Não retorna o QR.
            service.connect_instance(
                base_url=evo_config.server_url,
                api_key=instance.api_key,
                name=instance.name,
                webhook_url=webhook_url,
                subscribe=[],
            )
            # 2. /instance/qr retorna o QR em data.Qrcode (data URI completa).
            qr_result = service.get_qr_code(
                base_url=evo_config.server_url,
                api_key=instance.api_key,
                name=instance.name,
            )
        except Exception as e:
            logger.error(f"Erro ao gerar QR code: {e}")
            return _json_error(f"Erro na API: {e}", 502)

        # O Go aninha o QR em ``data`` com chaves capitalizadas
        # (``Qrcode``/``PairingCode``). Mantém fallback para formato plano.
        qr_data = (
            qr_result.get("data") if isinstance(qr_result, dict) else None
        )
        if not isinstance(qr_data, dict):
            qr_data = qr_result if isinstance(qr_result, dict) else {}

        qr_base64 = (
            qr_data.get("Qrcode")
            or qr_data.get("qrcode")
            or qr_data.get("base64")
            or qr_result.get("base64", "")
        )
        pairing_code = (
            qr_data.get("PairingCode")
            or qr_data.get("pairingCode")
            or qr_result.get("pairingCode", "")
        )

        return JsonResponse(
            {
                "base64": qr_base64,
                "pairingCode": pairing_code,
                "count": qr_data.get("count", 0),
            }
        )


class InstanceConnectionStateView(LoginRequiredMixin, View):
    """Retorna estado de conexão da instância via AJAX."""

    def get(self, request: HttpRequest, pk: int) -> JsonResponse:
        _, evo_config, _ = _get_tenant_and_config(request)
        if not evo_config or not evo_config.server_url:
            return _json_error("Config Evolution não encontrada.", 404)

        try:
            instance = EvolutionInstance.objects.get(pk=pk, active=True)
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        service = EvolutionGoAdapter()
        try:
            state_data = service.get_status(
                base_url=evo_config.server_url,
                api_key=instance.api_key,
                name=instance.name,
            )
            state = _parse_state(state_data)

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
        service = EvolutionGoAdapter()

        # No Evolution Go o webhook é configurado no /instance/connect
        # (não há endpoint /webhook/set). Reconectar reconfigura o webhook
        # e a lista de eventos assinados.
        try:
            # /instance/connect autentica com o token da instância
            # (não a Global API Key — esta retorna 401 "not authorized").
            service.connect_instance(
                base_url=evo_config.server_url,
                api_key=instance.api_key,
                name=instance.name,
                webhook_url=webhook_url,
                subscribe=[],
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

        service = EvolutionGoAdapter()

        try:
            service.delete_instance(
                base_url=evo_config.server_url,
                api_key=evo_config.api_key,
                name=instance.name,
            )
        except Exception as e:
            logger.warning(f"Erro ao deletar na API (continuando): {e}")

        instance.active = False
        instance.save(update_fields=["active"])

        from smart_core_assistant_painel.app.operacional.models import (
            AppInstance,
        )

        AppInstance.objects.filter(api_key=instance.api_key).update(
            active=False
        )

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

        service = EvolutionGoAdapter()

        try:
            # Logout no Go usa o token da instância (não a Global API Key).
            service.logout_instance(
                base_url=evo_config.server_url,
                api_key=instance.api_key,
                name=instance.name,
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


class InstanceToggleBotView(LoginRequiredMixin, View):
    """Ativa ou desativa a resposta automática do bot na instância."""

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

        import json

        try:
            data = json.loads(request.body)
            resposta_bot = bool(data.get("resposta_bot", True))
        except (json.JSONDecodeError, ValueError):
            return _json_error("Body inválido.")

        # Atualiza somente o AppInstance (fonte da verdade)
        from smart_core_assistant_painel.app.operacional.models import (
            AppInstance,
        )

        updated = AppInstance.objects.filter(api_key=instance.api_key).update(
            resposta_bot=resposta_bot
        )

        if not updated:
            return _json_error(
                "AppInstance não encontrado para esta instância.",
                404,
            )

        status_text = "ativado" if resposta_bot else "desativado"
        return JsonResponse(
            {
                "success": True,
                "message": f"Bot {status_text} para a instância.",
                "resposta_bot": resposta_bot,
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

        service = EvolutionGoAdapter()
        instances = list(EvolutionInstance.objects.filter(active=True))
        updated: list[dict[str, Any]] = []

        from smart_core_assistant_painel.app.operacional.models import (
            AppInstance,
        )

        for instance in instances:
            # Garante que o AppInstance existe, mas não sobrescreve
            # vínculos de departamento/owner já definidos
            AppInstance.objects.update_or_create(
                api_key=instance.api_key,
                defaults={
                    "channel": "evolution_api",
                    "display_name": instance.name,
                    "active": True,
                },
            )
            try:
                state_data = service.get_status(
                    base_url=evo_config.server_url,
                    api_key=instance.api_key,
                    name=instance.name,
                )
                state = _parse_state(state_data)
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


class DepartmentListView(LoginRequiredMixin, View):
    """Retorna departamentos ativos em JSON para uso no modal."""

    def get(self, request: HttpRequest) -> JsonResponse:
        tenant, _, _ = _get_tenant_and_config(request)
        if not tenant:
            return _json_error("Tenant não encontrado.", 404)

        from smart_core_assistant_painel.app.operacional.models import (
            Departamento,
        )

        departments = list(
            Departamento.objects.filter(ativo=True)
            .order_by("nome")
            .values("id", "nome", "descricao")
        )
        return JsonResponse({"departments": departments})


class DepartmentCreateView(LoginRequiredMixin, View):
    """Cria um novo departamento via AJAX para uso inline no modal."""

    def post(self, request: HttpRequest) -> JsonResponse:
        tenant, _, can_edit = _get_tenant_and_config(request)
        if not tenant:
            return _json_error("Tenant não encontrado.", 404)
        if not can_edit:
            return _json_error("Sem permissão para esta ação.", 403)

        import json

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return _json_error("Body inválido.")

        nome = str(data.get("nome", "")).strip()
        descricao = str(data.get("descricao", "")).strip()

        if not nome or len(nome) < 2:
            return _json_error(
                "Nome do departamento deve ter pelo menos 2 caracteres."
            )

        from smart_core_assistant_painel.app.operacional.models import (
            Departamento,
        )

        # Verifica duplicidade
        if Departamento.objects.filter(nome__iexact=nome).exists():
            return _json_error(f"Departamento '{nome}' já existe.")

        dept = Departamento.objects.create(
            nome=nome,
            descricao=descricao or None,
            ativo=True,
        )

        logger.info(
            "Departamento '%s' criado via modal de instância",
            dept.nome,
        )

        return JsonResponse(
            {
                "success": True,
                "department": {
                    "id": dept.pk,
                    "nome": dept.nome,
                    "descricao": dept.descricao or "",
                },
            },
            status=201,
        )


class AttendantListView(LoginRequiredMixin, View):
    """Retorna atendentes ativos filtrados por departamento."""

    def get(self, request: HttpRequest) -> JsonResponse:
        tenant, _, _ = _get_tenant_and_config(request)
        if not tenant:
            return _json_error("Tenant não encontrado.", 404)

        from smart_core_assistant_painel.app.operacional.models import (
            Atendente,
        )

        dept_id = request.GET.get("department_id")
        qs = Atendente.objects.filter(ativo=True).order_by("nome")

        if dept_id:
            qs = qs.filter(departamento_id=dept_id)

        attendants = list(qs.values("id", "nome", "cargo"))
        return JsonResponse({"attendants": attendants})


class InstanceUpdateView(LoginRequiredMixin, View):
    """Atualiza as configurações de uma instância (departamento, owner e bot)."""

    def post(self, request: HttpRequest, pk: int) -> JsonResponse:
        tenant, _, can_edit = _get_tenant_and_config(request)

        if not tenant:
            return _json_error("Configuração não encontrada.", 404)
        if not can_edit:
            return _json_error("Sem permissão para esta ação.", 403)

        try:
            instance = EvolutionInstance.objects.get(
                pk=pk, tenant_id=tenant.id, active=True
            )
        except EvolutionInstance.DoesNotExist:
            return _json_error("Instância não encontrada.", 404)

        import json

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return _json_error("Body inválido.")

        resposta_bot = bool(data.get("resposta_bot", True))
        departamento_id = data.get("departamento_id")
        owner_id = data.get("owner_id")

        from smart_core_assistant_painel.app.operacional.models import (
            AppInstance,
            Atendente,
            Departamento,
        )

        app_inst = AppInstance.objects.filter(api_key=instance.api_key).first()
        if not app_inst:
            return _json_error(
                "Configuração operacional da instância não encontrada.", 404
            )

        app_inst.resposta_bot = resposta_bot

        # Atualiza departamento
        if departamento_id:
            dept = Departamento.objects.filter(
                id=departamento_id, ativo=True
            ).first()
            app_inst.departamento = dept if dept else None
        else:
            app_inst.departamento = None

        # Atualiza owner
        if owner_id:
            owner = Atendente.objects.filter(id=owner_id, ativo=True).first()
            app_inst.owner = owner if owner else None
        else:
            app_inst.owner = None

        app_inst.save(update_fields=["resposta_bot", "departamento", "owner"])

        logger.info(
            "Instância '%s' atualizada com sucesso (dept=%s, owner=%s)",
            instance.name,
            getattr(app_inst.departamento, "nome", None),
            getattr(app_inst.owner, "nome", None),
        )

        return JsonResponse({"success": True})
