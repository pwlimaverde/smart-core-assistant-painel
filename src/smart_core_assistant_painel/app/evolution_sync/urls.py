from django.urls import path

from .views import webhook

urlpatterns = [
    # Rota nova com tenant_slug (preferida)
    path(
        "sync/evolution/webhook/<slug:tenant_slug>/",
        webhook,
        name="evolution_webhook_tenant",
    ),
    path("sync/evolution/webhook/<slug:tenant_slug>", webhook),
    # Manter rotas antigas para compatibilidade (emite warning)
    path("sync/evolution/webhook/", webhook, name="evolution_webhook"),
    path("sync/evolution/webhook", webhook),
]
