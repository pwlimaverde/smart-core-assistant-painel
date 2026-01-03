from django.contrib import admin
from django.urls import path

from .views.backoffice import RegisterPaymentView

from .models import (
    PaymentRecord,
    Plan,
    Subscription,
    Tenant,
    TenantConfig,
    TenantDatabase,
    TenantEvolution,
    TenantTrello,
)


class PaymentRecordInline(admin.TabularInline):
    model = PaymentRecord
    extra = 0
    readonly_fields = ("recorded_by", "created_at")
    fields = (
        "payment_date",
        "amount",
        "payment_method",
        "period_start",
        "period_end",
        "notes",
    )


class TenantDatabaseInline(admin.StackedInline):
    model = TenantDatabase
    extra = 0
    fields = (
        "host",
        "port",
        "database_name",
        "username",
        "_password",
        "ssl_mode",
        "connection_valid",
        "last_check",
    )
    readonly_fields = ("connection_valid", "last_check")


class TenantEvolutionInline(admin.StackedInline):
    model = TenantEvolution
    extra = 0
    fields = (
        "server_url",
        "_api_key",
        "instance_name",
        "connection_valid",
        "last_check",
    )
    readonly_fields = ("connection_valid", "last_check")


class TenantTrelloInline(admin.StackedInline):
    model = TenantTrello
    extra = 0
    fields = (
        "workspace_id",
        "_api_key",
        "_api_secret",
        "_token",
        "webhook_id",
        "connection_valid",
        "last_check",
    )
    readonly_fields = ("webhook_id", "connection_valid", "last_check")


class TenantConfigInline(admin.StackedInline):
    model = TenantConfig
    extra = 0
    fieldsets = (
        (
            "Configurações de LLM",
            {
                "fields": ("llm_class", "model"),
                "description": (
                    "Configurações avançadas de LLM. Se preenchidas, "
                    "sobrescrevem as configurações globais (CoreSettings)."
                ),
            },
        ),
        (
            "API Keys do Tenant",
            {
                "fields": ("api_keys",),
                "description": (
                    "API Keys específicas do tenant. Formato JSON: "
                    '{"groq_api_key": "...", "openai_api_key": "..."}. '
                    "Se preenchidas, sobrescrevem as API Keys globais."
                ),
            },
        ),
    )


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    fields = (
        "status",
        "plan",
        "current_period_start",
        "current_period_end",
        "payment_gateway",
        "external_customer_id",
        "external_subscription_id",
    )
    readonly_fields = ("is_active_property",)

    def is_active_property(self, obj):
        return obj.is_active()

    is_active_property.short_description = "Is Active?"
    is_active_property.boolean = True


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "max_instances",
        "max_departments",
        "active",
        "price",
    )
    search_fields = ("name",)
    list_filter = ("active",)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    # ... (restante do código igual)
    list_display = (
        "name",
        "slug",
        "owner",
        "active",
        "setup_completed",
        "subscription_status_badge",
        "days_until_expiration",
        "created_at",
    )
    search_fields = ("name", "slug", "owner__email", "owner__username")
    list_filter = (
        "active",
        "setup_completed",
        "subscription__status",
        "created_at",
    )

    def subscription_status_badge(self, obj):
        if not hasattr(obj, "subscription"):
            return "-"
        status = obj.subscription.status
        color = "gray"
        if status == Subscription.Status.ACTIVE:
            color = "green"
        elif status == Subscription.Status.PAST_DUE:
            color = "orange"
        elif status == Subscription.Status.SUSPENDED:
            color = "red"
        elif status == Subscription.Status.CANCELLED:
            color = "gray"

        from django.utils.html import format_html

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.subscription.get_status_display(),
        )

    subscription_status_badge.short_description = "Status Assinatura"

    def days_until_expiration(self, obj):
        if (
            not hasattr(obj, "subscription")
            or not obj.subscription.current_period_end
        ):
            return "-"
        from django.utils import timezone

        today = timezone.now().date()
        # Converter datetime para date se necessário
        period_end = obj.subscription.current_period_end
        if hasattr(period_end, "date"):
            period_end = period_end.date()
        delta = period_end - today
        days = delta.days

        color = "black"
        if days < 0:
            color = "red"
            text = f"Expirado há {abs(days)} dias"
        elif days <= 7:
            color = "orange"
            text = f"{days} dias"
        else:
            text = f"{days} dias"

        from django.utils.html import format_html

        return format_html('<span style="color: {};">{}</span>', color, text)

    days_until_expiration.short_description = "Expira em"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/register-payment/",
                self.admin_site.admin_view(RegisterPaymentView.as_view()),
                name="tenants_tenant_register_payment",
            ),
        ]
        return custom_urls + urls

    inlines = [
        TenantDatabaseInline,
        TenantEvolutionInline,
        TenantTrelloInline,
        TenantConfigInline,
        SubscriptionInline,
        PaymentRecordInline,
    ]
    readonly_fields = ("api_key", "id")
    fieldsets = (
        (
            "Identificação",
            {"fields": ("name", "slug", "owner", "active", "setup_completed")},
        ),
        ("Credenciais", {"fields": ("api_key", "id")}),
        ("Contato", {"fields": ("email", "phone")}),
    )
    actions = [
        "extend_subscription_30_days",
        "extend_subscription_6_months",
        "extend_subscription_12_months",
        "activate_tenants",
        "suspend_tenants",
    ]

    @admin.action(description="Estender assinatura por 30 dias")
    def extend_subscription_30_days(self, request, queryset):
        count = 0
        for tenant in queryset:
            if hasattr(tenant, "subscription"):
                tenant.subscription.extend_period(months=1)  # aprox 30 dias
                count += 1
        self.message_user(
            request, f"{count} assinaturas estendidas por 30 dias."
        )

    @admin.action(description="Estender assinatura por 6 meses")
    def extend_subscription_6_months(self, request, queryset):
        count = 0
        for tenant in queryset:
            if hasattr(tenant, "subscription"):
                tenant.subscription.extend_period(months=6)
                count += 1
        self.message_user(
            request, f"{count} assinaturas estendidas por 6 meses."
        )

    @admin.action(description="Estender assinatura por 12 meses")
    def extend_subscription_12_months(self, request, queryset):
        count = 0
        for tenant in queryset:
            if hasattr(tenant, "subscription"):
                tenant.subscription.extend_period(months=12)
                count += 1
        self.message_user(
            request, f"{count} assinaturas estendidas por 12 meses."
        )

    @admin.action(description="Ativar Tenants selecionados")
    def activate_tenants(self, request, queryset):
        queryset.update(active=True)
        self.message_user(request, "Tenants ativados com sucesso.")

    @admin.action(description="Suspender Tenants selecionados")
    def suspend_tenants(self, request, queryset):
        queryset.update(active=False)
        self.message_user(request, "Tenants suspensos com sucesso.")

    def save_model(self, request, obj, form, change):
        # Garante que criador seja salvo se necessário, etc.
        super().save_model(request, obj, form, change)


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "payment_date",
        "amount",
        "payment_method",
        "period_covered_display",
    )
    list_filter = ("payment_method", "payment_date")
    search_fields = ("tenant__name", "notes")
    date_hierarchy = "payment_date"

    def period_covered_display(self, obj):
        return f"{obj.period_start} até {obj.period_end}"

    period_covered_display.short_description = "Período Coberto"

    def save_model(self, request, obj, form, change):
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "status_badge",
        "plan",
        "current_period_end",
        "is_active_display",
    )
    list_filter = ("status", "plan", "current_period_end")
    search_fields = ("tenant__name", "external_customer_id")
    date_hierarchy = "current_period_end"

    def status_badge(self, obj):
        color = "gray"
        if obj.status == Subscription.Status.ACTIVE:
            color = "green"
        elif obj.status == Subscription.Status.PAST_DUE:
            color = "orange"
        elif obj.status == Subscription.Status.SUSPENDED:
            color = "red"
        elif obj.status == Subscription.Status.CANCELLED:
            color = "gray"

        from django.utils.html import format_html

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def is_active_display(self, obj):
        return obj.is_active()

    is_active_display.short_description = "Active"
    is_active_display.boolean = True
