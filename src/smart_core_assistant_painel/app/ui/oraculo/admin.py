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
        'get_documentos_preview',
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
            'fields': ('tag', 'grupo', 'treinamento_finalizado', '_documentos'),
            'classes': ('wide',)
        }),
    )

    # Função para exibir preview do documentos JSON
    @admin.display(description="Preview do Documento", ordering='_documentos')
    def get_documentos_preview(self, obj):
        """Retorna uma prévia do documentos JSON limitada a 100 caracteres"""
        if obj and obj._documentos:
            try:
                # Se for um dict, converte para string
                if isinstance(obj._documentos, dict):
                    preview = str(obj._documentos)[:1000]
                else:
                    preview = str(obj._documentos)[:1000]
                return preview + \
                    "..." if len(str(obj._documentos)) > 1000 else preview
            except Exception:
                return "Erro ao exibir documentos"
        return "Documento vazio"

    # Configurações adicionais
    list_per_page = 25
    save_on_top = True
