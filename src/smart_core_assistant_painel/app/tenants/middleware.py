import re
import threading
from typing import Callable, Optional

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .models import Subscription, Tenant
from .services.config_loader import ConfigLoader

# Contexto thread-local para armazenar o tenant atual
_tenant_context = threading.local()


def get_current_tenant() -> Optional["Tenant"]:
    """Retorna o tenant do contexto atual da thread."""
    return getattr(_tenant_context, "tenant", None)


def set_current_tenant(tenant: Optional["Tenant"]) -> None:
    """Define o tenant no contexto da thread atual."""
    _tenant_context.tenant = tenant


def clear_current_tenant() -> None:
    """Limpa o tenant do contexto (para cleanup após request)."""
    if hasattr(_tenant_context, "tenant"):
        del _tenant_context.tenant


class TenantMiddleware:
    """Middleware para identificação e validação de tenant por requisição."""

    EXEMPT_PATTERNS = [
        r"^/$",
        r"^/admin/",
        r"^/backoffice/",
        r"^/cadastro/",
        r"^/login/",
        r"^/logout/",
        r"^/static/",
        r"^/media/",
        r"^/health/",
        r"^/tenants/",
        r"^/api/payments/",
    ]

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse]
    ) -> None:
        self.get_response = get_response
        self._exempt_patterns = [re.compile(p) for p in self.EXEMPT_PATTERNS]

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Limpar contexto anterior
        clear_current_tenant()
        request.tenant = None  # type: ignore[attr-defined]

        # Verificar se path é exempto
        if self._is_exempt(request.path):
            return self.get_response(request)

        if hasattr(request, "user") and request.user.is_authenticated:
            if request.user.is_superuser:
                return self.get_response(request)

        # Tentar resolver tenant
        tenant, source = self._resolve_tenant(request)

        # Se identificou origem por subdomínio mas não achou tenant:
        if source == "subdomain" and not tenant:
            subdomain = self._extract_subdomain(request)
            return self._tenant_not_found_response(
                request, subdomain or "unknown"
            )

        if tenant:
            # Validar tenant ativo
            if not tenant.active:
                return self._subscription_error_response(
                    request, "Seu tenant está inativo. Entre em contato."
                )

            # Validar subscription (se existir)
            try:
                if hasattr(tenant, "subscription"):
                    if not tenant.subscription.is_active():
                        return self._subscription_error_response(
                            request,
                            "Sua assinatura expirou ou está inativa. "
                            "Renove seu plano para continuar.",
                        )
            except Subscription.DoesNotExist:
                pass  # Tenant sem subscription ainda (trial)

            # Definir no contexto
            request.tenant = tenant  # type: ignore[attr-defined]
            set_current_tenant(tenant)

        try:
            response = self.get_response(request)
        finally:
            # Limpar contexto após response (garantido pelo finally)
            clear_current_tenant()

        return response

    def _subscription_error_response(
        self, request: HttpRequest, message: str
    ) -> HttpResponse:
        """Retorna resposta de erro de subscription."""
        # Verifica se é requisição de API (JSON) ou browser (HTML)
        accept = request.headers.get("Accept", "")
        is_api_request = (
            "application/json" in accept
            or request.path.startswith("/api/")
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        )

        if is_api_request:
            return JsonResponse({"detail": message}, status=402)
        else:
            # Para requisições de browser, redirecionar para página de erro
            from django.shortcuts import render

            return render(
                request,
                "tenants/subscription_expired.html",
                {"message": message},
                status=402,
            )

    def _tenant_not_found_response(
        self, request: HttpRequest, slug: str
    ) -> HttpResponse:
        """Resposta para tenant não encontrado via subdomínio."""
        from django.shortcuts import render

        # API retorna JSON 404
        if request.path.startswith("/api/"):
            return JsonResponse(
                {"detail": f"Tenant '{slug}' não encontrado."}, status=404
            )

        # Browser: renderiza template
        return render(
            request,
            "tenants/tenant_not_found.html",
            {"slug": slug},
            status=404,
        )

    def _is_exempt(self, path: str) -> bool:
        """Verifica se o path está na lista de exceções."""
        return any(p.match(path) for p in self._exempt_patterns)

    def _extract_subdomain(self, request: HttpRequest) -> Optional[str]:
        """Extrai o slug do tenant a partir do subdomínio do host."""
        from django.conf import settings

        host = request.get_host().split(":")[0]  # Remove porta
        base_domain = getattr(settings, "TENANT_BASE_DOMAIN", "")
        reserved = getattr(settings, "TENANT_RESERVED_SUBDOMAINS", [])

        if not base_domain:
            return None

        # Verifica se é IP direto/localhost (desenvolvimento)
        if host.replace(".", "").isdigit() or host in (
            "localhost",
            "127.0.0.1",
            "django-app",
        ):
            return None

        # Verifica se termina com domínio base
        if not host.endswith(base_domain):
            return None

        # Extrai subdomínio
        # ex: cliente.dominio.com -> cliente
        # len(base_domain) + 1 conta o ponto anterior
        subdomain_part = (
            host[: -(len(base_domain) + 1)]
            if len(host) > len(base_domain)
            else ""
        )

        if not subdomain_part:
            return None

        subdomain = subdomain_part.split(".")[
            -1
        ]  # Pega o último nível apenas? Ou todo?
        # Assumindo apenas 1 nível de subdomínio por enquanto: cliente.dominio.com

        # Valida
        if not subdomain or subdomain.lower() in [r.lower() for r in reserved]:
            return None

        return subdomain.lower()

    def _resolve_tenant(
        self, request: HttpRequest
    ) -> tuple[Optional["Tenant"], str]:
        """
        Tenta identificar o tenant via:
        1. Subdomínio
        2. URL Webhook
        3. Header
        4. Sessão

        Retorna (Tenant ou None, fonte_da_identificacao)
        fonte: 'subdomain', 'url', 'header', 'session', 'none'
        """

        # 0. Subdomínio (Maior Prioridade)
        subdomain_slug = self._extract_subdomain(request)
        if subdomain_slug:
            tenant = Tenant.objects.filter(slug=subdomain_slug).first()
            # Retorna mesmo se for None, para indicar que a tentativa foi via subdomínio
            return tenant, "subdomain"

        # 1. Extrair de URL (webhook pattern)
        match = re.search(r"/webhook/([^/]+)/", request.path)
        if match:
            slug = match.group(1)
            return Tenant.objects.filter(slug=slug).first(), "url"

        # 2. Header X-Tenant-Slug
        slug = request.headers.get("X-Tenant-Slug")
        if slug:
            return Tenant.objects.filter(slug=slug).first(), "header"

        # 3. Sessão do usuário logado
        if hasattr(request, "user") and request.user.is_authenticated:
            # Primeiro tenta como owner
            tenant = Tenant.objects.filter(owner=request.user).first()
            if tenant:
                return tenant, "session"

            # Se não for owner, tenta como funcionário (TenantUser)
            # Import local para evitar circular import se houver
            from .models import TenantUser

            tenant_user = (
                TenantUser.objects.filter(user=request.user, is_active=True)
                .select_related("tenant")
                .first()
            )
            if tenant_user:
                request.tenant_user = tenant_user  # type: ignore[attr-defined]
                return tenant_user.tenant, "session"

        return None, "none"


class TenantConfigMiddleware(MiddlewareMixin):
    """
    Middleware responsável por carregar e injetar as configurações
    (RuntimeConfig) no contexto da requisição (ContextVar).

    Deve ser executado APÓS o middleware que define o tenant (se houver).
    Se não houver tenant (ex: admin, login), carrega apenas configs globais.
    """

    def process_request(self, request: HttpRequest) -> None:
        # Tenta obter o tenant da requisição (definido por middleware anterior)
        tenant: Tenant | None = getattr(request, "tenant", None)

        # Carrega as configurações (Core + Tenant) e define no ContextVar
        ConfigLoader.load_for_request(tenant)
