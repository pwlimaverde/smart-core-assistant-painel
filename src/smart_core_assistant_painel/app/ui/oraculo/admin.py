from django.contrib import admin

from .models import Treinamentos


@admin.register(Treinamentos)
class TreinamentosAdmin(admin.ModelAdmin):
    # Campos a serem exibidos na lista
    list_display = [
        'id',
        'tag',
        'grupo',
        'treinamento_finalizado',
        'get_documento_preview',
    ]

    # Campos que podem ser pesquisados
    search_fields = [
        'tag',
    ]

    # Ordenação padrão
    ordering = ['id']

    # Organização dos campos no formulário
    fieldsets = (
        ('Informações do Treinamento', {
            'fields': ('tag', 'grupo', 'treinamento_finalizado', 'documento'),
            'classes': ('wide',)
        }),
    )

    # Função para exibir preview do documento JSON
    @admin.display(description="Preview do Documento", ordering='documento')
    def get_documento_preview(self, obj):
        """Retorna uma prévia do documento JSON limitada a 100 caracteres"""
        if obj and obj.documento:
            try:
                # Se for um dict, converte para string
                if isinstance(obj.documento, dict):
                    preview = str(obj.documento)[:1000]
                else:
                    preview = str(obj.documento)[:1000]
                return preview + \
                    "..." if len(str(obj.documento)) > 1000 else preview
            except Exception:
                return "Erro ao exibir documento"
        return "Documento vazio"

    # Configurações adicionais
    list_per_page = 25
    save_on_top = True
