"""Configuração de URL para o projeto principal.

A lista `urlpatterns` roteia URLs para views. Para mais informações, consulte:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Exemplos:
    Function views
        1. Adicione uma importação:  from my_app import views
        2. Adicione uma URL a urlpatterns:  path('', views.home, name='home')
    Class-based views
        1. Adicione uma importação:  from other_app.views import Home
        2. Adicione uma URL a urlpatterns:  path('', Home.as_view(), name='home')
    Including another URLconf
        1. Importe a função include(): from django.urls import include, path
        2. Adicione uma URL a urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve


from . import views
from smart_core_assistant_painel.app.tenants.admin_client import (
    tenant_admin_site,
)

# Importar registros do Tenant Admin (Auto-discovery manual)
import smart_core_assistant_painel.app.ui.operacional.tenant_admin  # noqa
import smart_core_assistant_painel.app.evolution_sync.tenant_admin  # noqa
import smart_core_assistant_painel.app.ui.treinamento.tenant_admin  # noqa
import smart_core_assistant_painel.app.ui.atendimentos.tenant_admin  # noqa
import smart_core_assistant_painel.app.ui.clientes.tenant_admin  # noqa
import smart_core_assistant_painel.app.trello_sync.tenant_admin  # noqa

urlpatterns = [
    path("", views.LandingPageView.as_view(), name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("health/", views.health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("tenant-admin/", tenant_admin_site.urls),
    path(
        "tenants/",
        include("smart_core_assistant_painel.app.tenants.urls"),
    ),
    # Integrações
    path(
        "integrations/clickup/callback/",
        views.clickup_callback,
        name="clickup_callback",
    ),
    path(
        "usuarios/",
        include("smart_core_assistant_painel.app.ui.usuarios.urls"),
    ),
    path(
        "operacional/",
        include("smart_core_assistant_painel.app.ui.operacional.urls"),
    ),
    path(
        "clientes/",
        include("smart_core_assistant_painel.app.ui.clientes.urls"),
    ),
    path(
        "treinamento/",
        include("smart_core_assistant_painel.app.ui.treinamento.urls"),
    ),
    # Endpoint desativado: appflowy_adapter não está instalado
    # API pública do painel Kanban e entidades
    path(
        "api/operacional/",
        include("smart_core_assistant_painel.app.ui.operacional.api_urls"),
    ),
    # API ClickUp (condicional): só inclui se o app estiver instalado
]

if (
    "smart_core_assistant_painel.app.clickup_sync.apps.ClickupSyncConfig"
    in settings.INSTALLED_APPS
):
    urlpatterns += [
        path(
            "api/clickup_sync/",
            include("smart_core_assistant_painel.app.clickup_sync.api_urls"),
        ),
    ]

if "smart_core_assistant_painel.app.trello_sync" in settings.INSTALLED_APPS:
    urlpatterns += [
        path(
            "api/trello_sync/",
            include("smart_core_assistant_painel.app.trello_sync.api_urls"),
        ),
    ]

urlpatterns += [
    path(
        "",
        include("smart_core_assistant_painel.app.evolution_sync.urls"),
    ),
]

# Em produção via gunicorn sem Nginx dedicado, servir estáticos/mídia pelo Django
# evita admin sem CSS/JS após collectstatic.
if not settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATIC_ROOT},
        ),
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]


handler404 = (
    "smart_core_assistant_painel.app.ui.core.views.custom_page_not_found"
)
handler403 = (
    "smart_core_assistant_painel.app.ui.core.views.custom_permission_denied"
)
handler500 = (
    "smart_core_assistant_painel.app.ui.core.views.custom_server_error"
)
