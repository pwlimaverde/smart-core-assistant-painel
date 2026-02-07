"""Configuração do painel de administração do Django para usuários."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin de usuários sem grupos/permissões globais."""

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Informações pessoais",
            {"fields": ("first_name", "last_name", "email")},
        ),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
        (
            "Informações pessoais",
            {"fields": ("first_name", "last_name", "email")},
        ),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    readonly_fields = ("last_login", "date_joined")
    filter_horizontal: tuple[str, ...] = ()
