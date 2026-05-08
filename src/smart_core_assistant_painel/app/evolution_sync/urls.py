from django.urls import path

from .views import contact_data_api, webhook
from .views_instances import (
    AttendantListView,
    DepartmentCreateView,
    DepartmentListView,
    InstanceConnectionStateView,
    InstanceCreateView,
    InstanceDeleteView,
    InstanceDetailView,
    InstanceListView,
    InstanceLogoutView,
    InstanceQRCodeView,
    InstanceToggleBotView,
    InstanceUpdateView,
    InstanceWebhookView,
    RefreshAllStatusView,
)

urlpatterns = [
    # === Gerenciamento de Instâncias ===
    path(
        "evolution/instances/",
        InstanceListView.as_view(),
        name="evolution_instance_list",
    ),
    path(
        "evolution/instances/create/",
        InstanceCreateView.as_view(),
        name="evolution_instance_create",
    ),
    path(
        "evolution/instances/refresh-status/",
        RefreshAllStatusView.as_view(),
        name="evolution_instance_refresh_all",
    ),
    path(
        "evolution/instances/<int:pk>/",
        InstanceDetailView.as_view(),
        name="evolution_instance_detail",
    ),
    path(
        "evolution/instances/<int:pk>/update/",
        InstanceUpdateView.as_view(),
        name="evolution_instance_update",
    ),
    path(
        "evolution/instances/<int:pk>/qrcode/",
        InstanceQRCodeView.as_view(),
        name="evolution_instance_qrcode",
    ),
    path(
        "evolution/instances/<int:pk>/status/",
        InstanceConnectionStateView.as_view(),
        name="evolution_instance_status",
    ),
    path(
        "evolution/instances/<int:pk>/webhook/",
        InstanceWebhookView.as_view(),
        name="evolution_instance_webhook",
    ),
    path(
        "evolution/instances/<int:pk>/delete/",
        InstanceDeleteView.as_view(),
        name="evolution_instance_delete",
    ),
    path(
        "evolution/instances/<int:pk>/toggle-bot/",
        InstanceToggleBotView.as_view(),
        name="evolution_instance_toggle_bot",
    ),
    path(
        "evolution/instances/<int:pk>/logout/",
        InstanceLogoutView.as_view(),
        name="evolution_instance_logout",
    ),
    # === Endpoints AJAX para modal de criação ===
    path(
        "evolution/instances/departments/",
        DepartmentListView.as_view(),
        name="evolution_department_list",
    ),
    path(
        "evolution/instances/departments/create/",
        DepartmentCreateView.as_view(),
        name="evolution_department_create",
    ),
    path(
        "evolution/instances/attendants/",
        AttendantListView.as_view(),
        name="evolution_attendant_list",
    ),
    # === API Interna ===
    path(
        "api/evolution/contact-data/<int:contact_id>/",
        contact_data_api,
        name="evolution_contact_data_api",
    ),
    # === Webhooks (recebimento de mensagens) ===
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
