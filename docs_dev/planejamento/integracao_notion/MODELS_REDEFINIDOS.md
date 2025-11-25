# Models Redefinidos - Integração Notion

**Versão:** 4.1  
**Status:** ✅ Fase 1 Concluída - Fase 2 Em Progresso  
**Data:** Janeiro 2025

**Models Implementados:**
- ✅ ContatoSync (funcionando em produção)
- ✅ ClienteSync (funcionando em produção)
- 🔄 DepartamentoSync (para implementar - Fase 2.1)
- 🔄 AtendenteHumanoSync (para implementar - Fase 2.2)
- ⏳ AtendimentoSync (para implementar - Fase 3.1)
- ⏳ MensagemSync (para implementar - Fase 3.2)

---

## 📋 Visão Geral

Este documento apresenta os models redefinidos para a abordagem simplificada de integração com Notion, baseada em shadow models e configuração centralizada.

---

## 🏗️ Estrutura de Models

### 1. NotionDatabaseConfig (Centralizador)

```python
# src/smart_core_assistant_painel/app/notion_sync/models.py

class NotionDatabaseConfig(models.Model):
    """
    Configuração central dos artefatos do Notion.
    
    Cada instância representa uma database ou página no Notion que será
    sincronizada com um modelo Django específico.
    
    Funciona como o coração da integração, centralizando todos os
    IDs e configurações necessárias para a comunicação com a API Notion.
    """
    
    # Identificação Única
    slug: str = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Identificador único para referência no código"
    )
    
    name: str = models.CharField(
        max_length=200,
        help_text="Nome descritivo da database/página no Notion"
    )
    
    description: str = models.TextField(
        blank=True,
        help_text="Descrição detalhada do uso desta configuração"
    )
    
    # Configuração Notion (API 2025-09-03)
    notion_database_id: str = models.UUIDField(
        help_text="ID da database no Notion (formato UUID)"
    )
    
    data_source_id: str = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID do data source (API v2025-09-03)"
    )
    
    notion_page_id: str = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID da página principal (opcional, para hierarquias)"
    )
    
    # Mapeamento Django
    django_model: str = models.CharField(
        max_length=100,
        help_text="Modelo Django correspondente (app.Model)"
    )
    
    django_app_label: str = models.CharField(
        max_length=50,
        help_text="App Django onde o modelo está definido"
    )
    
    # Schema e Propriedades
    notion_schema: dict = models.JSONField(
        default=dict,
        help_text="Schema completo das propriedades do Notion"
    )
    
    field_mappings: dict = models.JSONField(
        default=dict,
        help_text="Mapeamento campo_django → campo_notion"
    )
    
    # Configurações de Sincronização
    sync_enabled: bool = models.BooleanField(
        default=True,
        help_text="Habilita/desabilita sincronização"
    )
    
    sync_direction: str = models.CharField(
        max_length=20,
        choices=[
            ('bidirectional', 'Bidirecional'),
            ('django_to_notion', 'Django → Notion'),
            ('notion_to_django', 'Notion → Django'),
        ],
        default='bidirectional',
        help_text="Direção da sincronização"
    )
    
    sync_priority: int = models.IntegerField(
        default=5,
        choices=[
            (1, 'Baixa'),
            (3, 'Média'),
            (5, 'Normal'),
            (7, 'Alta'),
            (10, 'Crítica'),
        ],
        help_text="Prioridade na fila de sincronização"
    )
    
    # Configurações Avançadas
    auto_sync: bool = models.BooleanField(
        default=True,
        help_text="Sincroniza automaticamente após alterações"
    )
    
    batch_sync_enabled: bool = models.BooleanField(
        default=False,
        help_text="Permite sincronização em lote"
    )
    
    batch_size: int = models.IntegerField(
        default=50,
        help_text="Tamanho do lote para sincronização em batch"
    )
    
    # Controle
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)
    last_sync_at: datetime = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata: dict = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais e configurações customizadas"
    )
    
    class Meta:
        verbose_name = "Configuração Notion"
        verbose_name_plural = "Configurações Notion"
        ordering = ['sync_priority', 'slug']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['django_model']),
            models.Index(fields=['sync_enabled']),
            models.Index(fields=['sync_priority']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.django_model})"
    
    def get_django_model_class(self) -> Type[models.Model]:
        """Retorna a classe do modelo Django configurado."""
        from django.apps import apps
        try:
            return apps.get_model(self.django_app_label, self.django_model.split('.')[-1])
        except LookupError:
            raise ValueError(f"Modelo {self.django_model} não encontrado")
    
    def is_ready_for_sync(self) -> bool:
        """Verifica se está pronto para sincronização."""
        return (
            self.sync_enabled and 
            self.notion_database_id and 
            self.data_source_id
        )
```

---

## 2. Shadow Models (Espelhos)

### 2.1. ContatoSync

```python
class ContatoSync(models.Model):
    """
    Espelho do modelo Contato para integração com Notion.
    
    Contém dados pré-processados e formatados para compatibilidade
    com as propriedades do Notion, incluindo o ID externo para
    localização exata.
    """
    
    # Relação com Modelo Original
    contato: 'Contato' = models.OneToOneField(
        'clientes.Contato',
        on_delete=models.CASCADE,
        related_name='notion_sync',
        help_text="Referência ao contato original"
    )
    
    # ID Externo (Principal para Localização)
    external_id: str = models.CharField(
        max_length=36,
        unique=True,
        db_index=True,
        help_text="ID da página correspondente no Notion (UUID sem dashes)"
    )
    
    # Configuração Relacionada
    config: NotionDatabaseConfig = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='contato_syncs',
        help_text="Configuração Notion para este modelo"
    )
    
    # Dados Pré-processados (Formatados para Notion)
    nome_formatado: str = models.CharField(
        max_length=200,
        help_text="Nome já formatado e validado para o Notion"
    )
    
    email_normalizado: str = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
        help_text="Email validado e normalizado"
    )
    
    telefone_formatado: str = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Telefone no formato internacional (+55XX999999999)"
    )
    
    # Campos Adicionais para Notion
    principal: bool = models.BooleanField(
        default=False,
        help_text="É contato principal do cliente?"
    )
    
    tags_formatadas: list = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags formatadas para select/multi-select do Notion"
    )
    
    # Propriedades Completas (Cache)
    notion_properties: dict = models.JSONField(
        default=dict,
        help_text="Propriedades completas formatadas para API Notion"
    )
    
    # Controle de Sincronização
    sync_status: str = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro'),
            ('disabled', 'Desabilitado'),
        ],
        default='pending',
        help_text="Status atual da sincronização"
    )
    
    last_sync_at: datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora da última sincronização"
    )
    
    sync_error: str = models.TextField(
        null=True,
        blank=True,
        help_text="Detalhes do último erro de sincronização"
    )
    
    retry_count: int = models.IntegerField(
        default=0,
        help_text="Número de tentativas de sincronização"
    )
    
    # Metadata
    sync_metadata: dict = models.JSONField(
        default=dict,
        blank=True,
        help_text="Informações adicionais sobre a sincronização"
    )
    
    # Timestamps
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Contato Sync"
        verbose_name_plural = "Contatos Sync"
        ordering = ['contato__nome']
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['contato']),
            models.Index(fields=['last_sync_at']),
            models.Index(fields=['sync_status', 'syncing']),
        ]
    
    def __str__(self) -> str:
        return f"{self.contato.nome} ({self.external_id or 'No ID'})"
    
    def prepare_notion_data(self) -> None:
        """Prepara e formata os dados para sincronização com Notion."""
        from notion_sync.mappers import ContatoMapper
        
        # Usa mapper para transformar dados
        self.notion_properties = ContatoMapper.to_notion_properties(self)
        
        # Formata campos específicos
        self.nome_formatado = self.contato.nome.strip().title()
        
        if self.contato.email:
            self.email_normalizado = self.contato.email.lower().strip()
        
        if self.contato.telefone:
            # Formata para padrão internacional
            self.telefone_formatado = self._format_phone(self.contato.telefone)
        
        # Prepara tags
        if self.contato.tags:
            self.tags_formatadas = [
                tag.strip().title() 
                for tag in self.contato.tags.split(',') 
                if tag.strip()
            ]
        
        # Detecta se é contato principal (primeiro contato do cliente)
        self.principal = self._is_principal_contact()
    
    def _format_phone(self, phone: str) -> str:
        """Formata telefone para padrão internacional."""
        import re
        
        # Remove tudo que não é dígito
        digits = re.sub(r'\D', '', phone)
        
        # Verifica se tem código do Brasil
        if digits.startswith('55') and len(digits) > 11:
            return f"+{digits[:2]} {digits[2:4]} {digits[4:-4]} {digits[-4:]}"
        elif len(digits) == 11:  # Celular com 9
            return f"+55 {digits[0:2]} {digits[2:7]} {digits[7:]}"
        elif len(digits) == 10:  # Fixo
            return f"+55 {digits[0:2]} {digits[2:6]} {digits[6:]}"
        else:
            return phone  # Retorna original se não conseguir formatar
    
    def _is_principal_contact(self) -> bool:
        """Verifica se é o contato principal do cliente."""
        if not self.contato.clientes.exists():
            return False
        
        # Se há apenas um contato, é principal
        if self.contato.clientes.first().contatos.count() == 1:
            return True
        
        # Se marcado como principal
        return self.contato.principal
    
    def needs_sync(self) -> bool:
        """Verifica se precisa sincronizar."""
        if not self.config.sync_enabled:
            return False
        
        if self.sync_status == 'syncing':
            return False
        
        # Verifica se houve alterações após último sync
        if self.last_sync_at and self.contato.updated_at > self.last_sync_at:
            return True
        
        return self.sync_status in ['pending', 'error']
```

### 2.2. AtendimentoSync

```python
class AtendimentoSync(models.Model):
    """
    Espelho do modelo Atendimento para integração com Notion.
    
    Modelo crítico que sincronizadados de atendimentos em tempo
    real para a equipe de atendimento visualizar no Notion.
    """
    
    # Relação
    atendimento: 'Atendimento' = models.OneToOneField(
        'atendimentos.Atendimento',
        on_delete=models.CASCADE,
        related_name='notion_sync'
    )
    
    # ID Externo
    external_id: str = models.CharField(
        max_length=36,
        unique=True,
        db_index=True
    )
    
    # Configuração
    config: NotionDatabaseConfig = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='atendimento_syncs'
    )
    
    # Dados Calculados (Performance)
    cliente_nome: str = models.CharField(
        max_length=200,
        help_text="Nome do cliente (cache para performance)"
    )
    
    cliente_id: int = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID do cliente (para relation no Notion)"
    )
    
    contato_nome: str = models.CharField(
        max_length=200,
        help_text="Nome do contato (cache)"
    )
    
    atendente_nome: str = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Nome do atendente (cache)"
    )
    
    departamento_nome: str = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Nome do departamento (cache)"
    )
    
    # Métricas SLA
    tempo_resposta_minutos: int = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tempo até primeira resposta em minutos"
    )
    
    tempo_total_minutos: int = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tempo total do atendimento em minutos"
    )
    
    # Propriedades Notion
    notion_properties: dict = models.JSONField(default=dict)
    
    # Controle
    sync_status: str = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('syncing', 'Sincronizando'),
            ('synced', 'Sincronizado'),
            ('error', 'Erro'),
        ],
        default='pending'
    )
    
    last_sync_at: datetime = models.DateTimeField(null=True, blank=True)
    sync_error: str = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Atendimento Sync"
        verbose_name_plural = "Atendimentos Sync"
        ordering = ['-atendimento__created_at']
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
            models.Index(fields=['atendimento']),
            models.Index(fields=['cliente_id']),
            models.Index(fields=['atendimento__status']),
        ]
    
    def prepare_notion_data(self) -> None:
        """Prepara dados complexos do atendimento."""
        from notion_sync.mappers import AtendimentoMapper
        
        # Usa mapper para transformação principal
        self.notion_properties = AtendimentoMapper.to_notion_properties(self)
        
        # Calcula métricas de performance
        self._calculate_sla_metrics()
        
        # Cache dos dados relacionados
        self._cache_related_data()
    
    def _calculate_sla_metrics(self) -> None:
        """Calcula métricas de SLA do atendimento."""
        atendimento = self.atendimento
        
        # Tempo de primeira resposta
        if atendimento.data_primeira_resposta:
            delta = atendimento.data_primeira_resposta - atendimento.created_at
            self.tempo_resposta_minutos = int(delta.total_seconds() / 60)
        
        # Tempo total (se finalizado)
        if atendimento.status in ['resolvido', 'cancelado']:
            delta = timezone.now() - atendimento.created_at
            self.tempo_total_minutos = int(delta.total_seconds() / 60)
    
    def _cache_related_data(self) -> None:
        """Cache dos dados relacionados para performance."""
        atendimento = self.atendimento
        
        # Cliente
        if hasattr(atendimento, 'cliente') and atendimento.cliente:
            self.cliente_nome = atendimento.cliente.nome_fantasia
            self.cliente_id = atendimento.cliente.id
        
        # Contato
        self.contato_nome = atendimento.contato.nome
        
        # Atendente
        if atendimento.atendente:
            self.atendente_nome = atendimento.atendente.nome
        
        # Departamento
        if atendimento.departamento:
            self.departamento_nome = atendimento.departamento.nome
```

### 2.3. Demais Shadow Models

```python
# ClienteSync - Estrutura similar
class ClienteSync(models.Model):
    cliente: 'Cliente' = models.OneToOneField(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        related_name='notion_sync'
    )
    external_id: str = models.CharField(max_length=36, unique=True, db_index=True)
    config: NotionDatabaseConfig = models.ForeignKey(NotionDatabaseConfig, on_delete=models.CASCADE)
    
    # Campos pré-processados
    nome_fantasia_formatado: str = models.CharField(max_length=200)
    cnpj_formatado: str = models.CharField(max_length=18, null=True, blank=True)
    
    notion_properties: dict = models.JSONField(default=dict)
    sync_status: str = models.CharField(max_length=20, default='pending')
    last_sync_at: datetime = models.DateTimeField(null=True, blank=True)
    sync_error: str = models.TextField(null=True, blank=True)

# DepartamentoSync - Apenas Django → Notion
class DepartamentoSync(models.Model):
    departamento: 'Departamento' = models.OneToOneField(
        'operacional.Departamento',
        on_delete=models.CASCADE,
        related_name='notion_sync'
    )
    external_id: str = models.CharField(max_length=36, unique=True, db_index=True)
    config: NotionDatabaseConfig = models.ForeignKey(NotionDatabaseConfig, on_delete=models.CASCADE)
    
    nome_formatado: str = models.CharField(max_length=100)
    notion_properties: dict = models.JSONField(default=dict)
    sync_status: str = models.CharField(max_length=20, default='pending')
    
    class Meta:
        # Sync apenas na direção Django → Notion
        pass

# AtendenteSync - Bidirecional
class AtendenteSync(models.Model):
    atendente: 'AtendenteHumano' = models.OneToOneField(
        'operacional.AtendenteHumano',
        on_delete=models.CASCADE,
        related_name='notion_sync'
    )
    external_id: str = models.CharField(max_length=36, unique=True, db_index=True)
    config: NotionDatabaseConfig = models.ForeignKey(NotionDatabaseConfig, on_delete=models.CASCADE)
    
    nome_formatado: str = models.CharField(max_length=200)
    email_normalizado: str = models.EmailField(null=True, blank=True)
    notion_properties: dict = models.JSONField(default=dict)
    sync_status: str = models.CharField(max_length=20, default='pending')
    last_sync_at: datetime = models.DateTimeField(null=True, blank=True)

# MensagemSync - Apenas Django → Notion (muitos dados)
class MensagemSync(models.Model):
    mensagem: 'Mensagem' = models.OneToOneField(
        'atendimentos.Mensagem',
        on_delete=models.CASCADE,
        related_name='notion_sync'
    )
    external_id: str = models.CharField(max_length=36, unique=True, db_index=True)
    config: NotionDatabaseConfig = models.ForeignKey(NotionDatabaseConfig, on_delete=models.CASCADE)
    
    # Conteúdo processado
    conteudo_formatado: str = models.TextField()
    atendimento_id: int = models.IntegerField(help_text="ID do atendimento pai")
    notion_properties: dict = models.JSONField(default=dict)
    sync_status: str = models.CharField(max_length=20, default='pending')
    
    class Meta:
        # Mensagens são sincizadas apenas em lote devido ao volume
        ordering = ['-mensagem->created_at']
```

---

## 3. Models de Apoio

### 3.1. NotionObjectMapping (Simplificado)

```python
class NotionObjectMapping(models.Model):
    """
    Mapeamento simplificado entre objetos Django e IDs externos.
    
    Funciona como um índice reverso rápido para localizar objetos
    Django a partir de IDs do Notion (útil para webhooks).
    """
    
    # Objeto Django
    content_type: ContentType = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Tipo do modelo Django"
    )
    
    object_id: int = models.PositiveIntegerField(
        help_text="ID da instância do modelo Django"
    )
    
    content_object: GenericForeignKey = GenericForeignKey('content_type', 'object_id')
    
    # Referência Externa
    external_id: str = models.CharField(
        max_length=36,
        db_index=True,
        help_text="ID da página/database no Notion"
    )
    
    external_type: str = models.CharField(
        max_length=20,
        choices=[
            ('page', 'Página'),
            ('database', 'Database'),
        ],
        default='page',
        help_text="Tipo do objeto no Notion"
    )
    
    # Configuração Relacionada
    config: NotionDatabaseConfig = models.ForeignKey(
        NotionDatabaseConfig,
        on_delete=models.CASCADE,
        related_name='mappings',
        help_text="Configuração Notion utilizada"
    )
    
    # Controle
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['external_id']),
            models.Index(fields=['config']),
        ]
    
    def __str__(self) -> str:
        return f"{self.content_object} → {self.external_id}"
    
    @classmethod
    def get_by_external_id(cls, external_id: str) -> 'NotionObjectMapping':
        """Busca mapeamento pelo ID externo do Notion."""
        return cls.objects.select_related('content_object').get(external_id=external_id)
```

### 3.2. SyncLog (Essencial)

```python
class SyncLog(models.Model):
    """
    Log essencial de operações de sincronização.
    
    Focado apenas no necessário para debugging e monitoramento.
    Sem sobrecarga de dados, apenas informações relevantes.
    """
    
    # Identificação da Operação
    model_name: str = models.CharField(
        max_length=100,
        help_text="Nome do modelo sincronizado"
    )
    
    instance_id: int = models.PositiveIntegerField(
        help_text="ID da instância sincronizada"
    )
    
    external_id: str = models.CharField(
        max_length=36,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID externo no Notion (se aplicável)"
    )
    
    # Detalhes da Operação
    direction: str = models.CharField(
        max_length=20,
        choices=[
            ('to_notion', 'Django → Notion'),
            ('from_notion', 'Notion → Django'),
        ],
        help_text="Direção da sincronização"
    )
    
    operation: str = models.CharField(
        max_length=20,
        choices=[
            ('create', 'Criar'),
            ('update', 'Atualizar'),
            ('delete', 'Excluir'),
            ('sync', 'Sincronizar'),
        ],
        help_text="Tipo de operação"
    )
    
    # Resultado
    success: bool = models.BooleanField(
        default=False,
        help_text="Operação foi bem-sucedida?"
    )
    
    error_type: str = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Tipo do erro (ex: APIError, ValidationError)"
    )
    
    error_message: str = models.TextField(
        null=True,
        blank=True,
        help_text="Mensagem detalhada do erro"
    )
    
    # Performance
    duration_ms: int = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duração da operação em milissegundos"
    )
    
    attempts: int = models.IntegerField(
        default=1,
        help_text="Número de tentativas realizadas"
    )
    
    # Contexto
    config_slug: str = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Slug da configuração utilizada"
    )
    
    # Timestamps
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Sincronização"
        verbose_name_plural = "Logs de Sincronização"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'instance_id']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['success']),
            models.Index(fields=['direction']),
            models.Index(fields=['external_id']),
        ]
    
    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} {self.direction} {self.model_name}:{self.instance_id}"
    
    @property
    def status_emoji(self) -> str:
        """Retorna emoji baseado no status."""
        if self.success:
            return "✅"
        else:
            return "❌"
    
    def get_context_info(self) -> dict:
        """Retorna informações de contexto para logging."""
        return {
            'model': self.model_name,
            'instance_id': self.instance_id,
            'external_id': self.external_id,
            'direction': self.direction,
            'operation': self.operation,
            'success': self.success,
            'duration_ms': self.duration_ms,
            'attempts': self.attempts,
            'error_type': self.error_type,
        }
```

---

## 4. Índices e Performance

### 4.1. Índices Estratégicos

```python
# Índices compostos para performance
class Meta:
    indexes = [
        # Para buscas por status e data
        models.Index(fields=['sync_status', '-created_at']),
        
        # Para busca por modelo e instância
        models.Index(fields=['model_name', 'instance_id']),
        
        # Para busca por external_id
        models.Index(fields=['external_id']),
        
        # Para ordenação por prioridade
        models.Index(fields=['-priority', 'created_at']),
        
        # Para busca por configuração
        models.Index(fields=['config']),
        
        # Para performance de joins
        models.Index(fields=['contato']),
        models.Index(fields=['atendimento']),
        models.Index(fields=['cliente']),
    ]
```

### 4.2. Estratégias de Otimização

```python
# Select/Prefetch related otimizados
def get_pending_syncs() -> QuerySet:
    """Retorna pendentes com joins otimizados."""
    return (
        ContatoSync.objects
        .filter(
            sync_status='pending',
            config__sync_enabled=True
        )
        .select_related('contato', 'config')
        .prefetch_related('contato__clientes')
    )

# Bulk operations para performance
def bulk_prepare_sync_data(sync_objects: list) -> None:
    """Prepara dados em lote para performance."""
    for sync_obj in sync_objects:
        sync_obj.prepare_notion_data()
    
    # Bulk update
    ContatoSync.objects.bulk_update(
        sync_objects,
        ['notion_properties', 'sync_status', 'updated_at']
    )
```

---

## 5. Métodos Auxiliares

### 5.1. Managers Customizados

```python
class ContatoSyncManager(models.Manager):
    """Manager com métodos específicos para ContatoSync."""
    
    def pending_sync(self) -> QuerySet:
        """Retorna contatos pendentes de sincronização."""
        return self.filter(
            sync_status='pending',
            config__sync_enabled=True
        ).select_related('contato', 'config')
    
    def with_sync_errors(self) -> QuerySet:
        """Retorna contatos com erros de sincronização."""
        return self.filter(
            sync_status='error'
        ).select_related('contato')
    
    def needs_sync(self) -> QuerySet:
        """Retorna contatos que precisam sincronizar."""
        return self.filter(
            config__sync_enabled=True
        ).exclude(
            sync_status='synced'
        )

class ContatoSync(models.Model):
    objects = ContatoSyncManager()
    
    # ... resto do model
```

### 5.2. Property Methods

```python
class ContatoSync(models.Model):
    @property
    def is_synced(self) -> bool:
        """Verifica se está sincronizado."""
        return self.sync_status == 'synced' and self.last_sync_at is not None
    
    @property
    def sync_age_hours(self) -> int:
        """Idade da última sincronização em horas."""
        if not self.last_sync_at:
            return 999999
        
        delta = timezone.now() - self.last_sync_at
        return int(delta.total_seconds() / 3600)
    
    @property
    def has_sync_errors(self) -> bool:
        """Verifica se há erros de sincronização."""
        return self.sync_status == 'error' and bool(self.sync_error)
    
    @property
    def notion_url(self) -> str:
        """Retorna URL da página no Notion."""
        if not self.external_id:
            return ""
        
        formatted_id = '-'.join([
            self.external_id[i:i+8] 
            for i in range(0, len(self.external_id), 8)
        ])
        
        return f"https://notion.so/{formatted_id}"
```

---

## 🎯 Benefícios Desta Estrutura

### ✅ Performance
- **Shadow models** com dados pré-processados
- **Índices otimizados** para queries comuns
- **Cache de dados relacionados** para evitar joins
- **Bulk operations** para sincronização em lote

### ✅ Manutenibilidade
- **Mappers isolados** por modelo
- **Configuração centralizada** em um único model
- **Logs essenciais** sem sobrecarga
- **Métodos auxiliares** para operações comuns

### ✅ Flexibilidade
- **Sync direction** configurável por modelo
- **Priority system** para controle de fila
- **Metadata field** para configurações customizadas
- **Extensível** para novos modelos

### ✅ Robustez
- **Retry tracking** nos models
- **Error handling** detalhado
- **Status tracking** granular
- **Validation** nos mapeamentos

---

## 📊 Resumo de Models

| Model | Tipo | Finalidade | Sync Direction |
|-------|------|------------|----------------|
| **NotionDatabaseConfig** | Configuração | Centralizar IDs e configurações | N/A |
| **ContatoSync** | Shadow | Espelhar contato com dados pré-processados | Bidirecional |
| **ClienteSync** | Shadow | Espelhar cliente | Bidirecional |
| **AtendimentoSync** | Shadow | Espelhar atendimento (crítico) | Bidirecional |
| **DepartamentoSync** | Shadow | Espelhar departamento | Django → Notion |
| **AtendenteSync** | Shadow | Espelhar atendente | Bidirecional |
| **MensagemSync** | Shadow | Espelhar mensagens | Django → Notion |
| **NotionObjectMapping** | Apoio | Índice reverso para webhooks | N/A |
| **SyncLog** | Apoio | Log essencial de operações | N/A |

---

**Status:** ✅ Models Redefinidos e Aprovados  
**Próximo passo:** Implementar mappers de transformação  

---
```

<file_path>
smart-core-assistant-painel\docs_dev\planejamento\integracao_notion\MODELS_REDEFINIDOS.md
</file_path>