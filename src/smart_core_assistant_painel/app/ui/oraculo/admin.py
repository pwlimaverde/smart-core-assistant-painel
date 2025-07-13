from django.contrib import admin

from .models import (
    AtendenteHumano,
    Atendimento,
    Cliente,
    FluxoConversa,
    Mensagem,
    Treinamentos,
)


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


@admin.register(AtendenteHumano)
class AtendenteHumanoAdmin(admin.ModelAdmin):
    # Campos a serem exibidos na lista
    list_display = [
        'id',
        'nome',
        'cargo',
        'departamento',
        'whatsapp',
        'ativo',
        'disponivel',
        'get_atendimentos_ativos',
        'max_atendimentos_simultaneos',
        'ultima_atividade',
    ]

    # Campos que podem ser pesquisados
    search_fields = [
        'nome',
        'cargo',
        'departamento',
        'whatsapp',
        'email',
    ]

    # Filtros laterais
    list_filter = [
        'ativo',
        'disponivel',
        'departamento',
        'cargo',
        'data_cadastro',
    ]

    # Campos somente leitura
    readonly_fields = [
        'data_cadastro',
        'ultima_atividade',
        'get_atendimentos_ativos',
    ]

    # Ordenação padrão
    ordering = ['nome']

    # Organização dos campos no formulário
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'cargo', 'departamento'),
            'classes': ('wide',)
        }),
        ('Contatos', {
            'fields': ('whatsapp', 'telefone_corporativo', 'email'),
            'classes': ('wide',)
        }),
        ('Sistema', {
            'fields': ('usuario_sistema', 'ativo', 'disponivel'),
        }),
        ('Capacidades', {
            'fields': ('max_atendimentos_simultaneos', 'especialidades'),
        }),
        ('Horários', {
            'fields': ('horario_trabalho', 'data_admissao'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        }),
        ('Informações do Sistema', {
            'fields': ('data_cadastro', 'ultima_atividade', 'get_atendimentos_ativos'),
            'classes': ('collapse',)
        }),
    )

    # Função para exibir quantidade de atendimentos ativos
    @admin.display(description="Atendimentos Ativos")
    def get_atendimentos_ativos(self, obj):
        """Retorna a quantidade de atendimentos ativos do atendente"""
        if obj:
            return obj.get_atendimentos_ativos()
        return 0

    # Configurações adicionais
    list_per_page = 25
    save_on_top = True

    # Actions customizadas
    actions = ['marcar_como_disponivel', 'marcar_como_indisponivel']

    @admin.action(description='Marcar atendentes selecionados como disponíveis')
    def marcar_como_disponivel(self, request, queryset):
        queryset.update(disponivel=True)
        self.message_user(
            request, f'{
                queryset.count()} atendentes marcados como disponíveis.')

    @admin.action(description='Marcar atendentes selecionados como indisponíveis')
    def marcar_como_indisponivel(self, request, queryset):
        queryset.update(disponivel=False)
        self.message_user(
            request, f'{
                queryset.count()} atendentes marcados como indisponíveis.')

# =====================================================================
# ADMINS PARA O SISTEMA DE CHATBOT
# =====================================================================


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'telefone',
        'nome',
        'ultima_interacao',
        'data_cadastro',
        'total_atendimentos']
    list_filter = ['data_cadastro', 'ultima_interacao']
    search_fields = ['telefone', 'nome']
    readonly_fields = ['data_cadastro', 'ultima_interacao']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('telefone', 'nome')
        }),
        ('Datas', {
            'fields': ('data_cadastro', 'ultima_interacao')
        }),
        ('Metadados', {
            'fields': ('metadados',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Total de Atendimentos')
    def total_atendimentos(self, obj):
        return obj.atendimentos.count()


class MensagemInline(admin.TabularInline):
    model = Mensagem
    extra = 0
    readonly_fields = ['timestamp', 'message_id_whatsapp']
    fields = ['tipo', 'conteudo', 'is_from_client', 'respondida', 'timestamp']

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('timestamp')


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'cliente_telefone',
        'status',
        'atendente_humano_nome',
        'data_inicio',
        'data_fim',
        'avaliacao',
        'total_mensagens']
    list_filter = [
        'status',
        'prioridade',
        'data_inicio',
        'avaliacao',
        'atendente_humano']
    search_fields = [
        'cliente__telefone',
        'cliente__nome',
        'assunto',
        'atendente_humano__nome']
    readonly_fields = ['data_inicio', 'data_fim']
    inlines = [MensagemInline]

    fieldsets = (
        ('Informações do Atendimento', {
            'fields': ('cliente', 'status', 'assunto', 'prioridade')
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_fim')
        }),
        ('Atendente', {
            'fields': ('atendente_humano',)
        }),
        ('Avaliação', {
            'fields': ('avaliacao', 'feedback')
        }),
        ('Contexto e Histórico', {
            'fields': ('contexto_conversa', 'historico_status', 'tags'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Telefone', ordering='cliente__telefone')
    def cliente_telefone(self, obj):
        return obj.cliente.telefone

    @admin.display(description='Atendente', ordering='atendente_humano__nome')
    def atendente_humano_nome(self, obj):
        return obj.atendente_humano.nome if obj.atendente_humano else '-'

    @admin.display(description='Mensagens')
    def total_mensagens(self, obj):
        return obj.mensagens.count()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'atendente_humano')


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'atendimento_id',
        'cliente_telefone',
        'tipo',
        'conteudo_preview',
        'is_from_client',
        'respondida',
        'timestamp']
    list_filter = ['tipo', 'is_from_client', 'respondida', 'timestamp']
    search_fields = ['conteudo', 'atendimento__cliente__telefone']
    readonly_fields = ['timestamp', 'message_id_whatsapp']

    fieldsets = (
        ('Informações da Mensagem', {
            'fields': ('atendimento', 'tipo', 'conteudo', 'is_from_client', 'respondida')
        }),
        ('Resposta do Bot', {
            'fields': ('resposta_bot', 'confianca_resposta', 'intent_detectado')
        }),
        ('Metadados', {
            'fields': ('message_id_whatsapp', 'metadados', 'entidades_extraidas'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp',)
        }),
    )

    @admin.display(description='Telefone',
                   ordering='atendimento__cliente__telefone')
    def cliente_telefone(self, obj):
        return obj.atendimento.cliente.telefone

    @admin.display(description='Conteúdo')
    def conteudo_preview(self, obj):
        return obj.conteudo[:50] + \
            "..." if len(obj.conteudo) > 50 else obj.conteudo

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('atendimento__cliente')


@admin.register(FluxoConversa)
class FluxoConversaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'data_criacao', 'data_modificacao']
    list_filter = ['ativo', 'data_criacao']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['data_criacao', 'data_modificacao']

    fieldsets = (
        ('Informações do Fluxo', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
        ('Configuração', {
            'fields': ('condicoes_entrada', 'estados'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_modificacao')
        }),
    )


# Customizações adicionais do admin
admin.site.site_header = "Smart Core Assistant - Painel de Administração"
admin.site.site_title = "Smart Core Assistant"
admin.site.index_title = "Painel de Controle do Chatbot"
