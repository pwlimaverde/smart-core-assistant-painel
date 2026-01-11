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

from .views import onboarding

from .views.invites import (
    activate_account,
    edit_permissions,
    invite_user,
    list_users,
    resend_invite,
)

from .views.backoffice import BackofficeDashboardView, RegisterPaymentView

app_name = "tenants"

urlpatterns = [
    # Onboarding Wizard (Public)
    path(
        "onboarding/",
        onboarding.Step1TenantView.as_view(),
        name="onboarding_step_1",
    ),
    path(
        "onboarding/step/2/",
        onboarding.Step2PaymentView.as_view(),
        name="onboarding_step_2",
    ),
    path(
        "onboarding/step/3/",
        onboarding.Step3ConfigView.as_view(),
        name="onboarding_step_3",
    ),
    path(
        "onboarding/step/4/",
        onboarding.Step4ProvisionView.as_view(),
        name="onboarding_step_4",
    ),
    path(
        "api/onboarding/check-slug/",
        onboarding.CheckSlugView.as_view(),
        name="api_check_slug",
    ),
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
    path(
        "users/invite/<uuid:invite_id>/resend/",
        resend_invite,
        name="user_invite_resend",
    ),
    path(
        "users/<int:user_id>/permissions/",
        edit_permissions,
        name="user_permissions",
    ),
    path("activate/<str:token>/", activate_account, name="activate_account"),
]
