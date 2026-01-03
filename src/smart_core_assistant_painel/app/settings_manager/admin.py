from django.contrib import admin
from .models import CoreSettings


@admin.register(CoreSettings)
class CoreSettingsAdmin(admin.ModelAdmin):
    list_display = ("key", "encrypted", "description", "updated_at")
    list_filter = ("encrypted", "created_at")
    search_fields = ("key", "description")
    readonly_fields = ("created_at", "updated_at")

    # TODO: Futuramente implementar widget customizado para criptografar no save do Admin
    # Por enquanto, a carga será feita via script, então não é bloqueante.
