from django.urls import path

from .views import (
    AIConfigView,
    ConfigDebugView,
    DashboardView,
    DatabaseConfigView,
    DeleteTrelloWebhookView,
    EvolutionConfigView,
    RegisterTrelloWebhookView,
    RunMigrationsView,
    TenantSignupView,
    TestConnectionView,
    TrelloConfigView,
)

from .views.invites import activate_account, invite_user, list_users

from .views.backoffice import BackofficeDashboardView, RegisterPaymentView

app_name = "tenants"

urlpatterns = [
    # Backoffice (Super Admin)
    path(
        "bo/", BackofficeDashboardView.as_view(), name="backoffice_dashboard"
    ),
    path(
        "bo/tenant/<uuid:pk>/register-payment/",
        RegisterPaymentView.as_view(),
        name="backoffice_register_payment",
    ),
    # Frontend (Tenant)
    path("signup/", TenantSignupView.as_view(), name="signup"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path(
        "config/database/",
        DatabaseConfigView.as_view(),
        name="config_database",
    ),
    path(
        "config/evolution/",
        EvolutionConfigView.as_view(),
        name="config_evolution",
    ),
    path("config/trello/", TrelloConfigView.as_view(), name="config_trello"),
    path(
        "register-trello-webhook/",
        RegisterTrelloWebhookView.as_view(),
        name="register_trello_webhook",
    ),
    path(
        "delete-trello-webhook/",
        DeleteTrelloWebhookView.as_view(),
        name="delete_trello_webhook",
    ),
    path("config/ai/", AIConfigView.as_view(), name="config_ai"),
    path("config/debug/", ConfigDebugView.as_view(), name="config_debug"),
    path(
        "test-connection/<str:service_type>/",
        TestConnectionView.as_view(),
        name="test_connection",
    ),
    path(
        "run-migrations/",
        RunMigrationsView.as_view(),
        name="run_migrations",
    ),
    # User Management
    path("users/", list_users, name="user_list"),
    path("users/invite/", invite_user, name="user_invite"),
    path("activate/<str:token>/", activate_account, name="activate_account"),
]
