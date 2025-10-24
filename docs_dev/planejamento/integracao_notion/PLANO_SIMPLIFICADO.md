# Plano Simplificado de Integração Django ↔ Notion

**Versão:** 4.0  
**Status:** ✅ Aprovado para Implementação  
**Data:** Janeiro 2025

---

## 🎯 Visão Geral

Este documento apresenta a abordagem **simplificada e robusta** para integração entre o sistema Smart Core Assistant e o Notion, baseada em shadow models e mapeamento direto por IDs.

### 🔄 Conceito Central

Em vez de uma arquitetura complexa com múltiplas camadas, adotamos uma abordagem direta:

1. **Shadow Models** locais espelham os dados do Notion
2. **NotionDatabaseConfig** centraliza configurações
3. **Mappers** transformam dados entre sistemas
4. **Signals Django** disparam sincronização automática

---

## 🏗️ Arquitetura Simplificada

```
┌─────────────────┐    Signals    ┌─────────────────┐    Tasks    ┌─────────────────┐
│   Django Core   │ ────────────► │   notion_sync   │ ──────────► │   Celery Tasks  │
│                 │               │                 │            │                 │
│ • Contato       │               │ • Shadow Models │            │ • Notion API    │
│ • Cliente       │               │ • Mappers       │            │ • Transformação │
│ • Atendimento   │               │ • Configs       │            │ • Retry/Log     │
└─────────────────┘               └─────────────────┘            └─────────────────┘
                                                                 │
                                                                 ▼
                                                       ┌─────────────────┐
                                                       │     Notion      │
                                                       │                 │
                                                       │ • Databases     │
                                                       │ • Pages         │
                                                       │ • Properties    │
                                                       └─────────────────┘
```

---

## 📋 Models Essenciais

### 1. NotionDatabaseConfig (O Coração)

```python
class NotionDatabaseConfig(models.Model):
    """
    Centralizador de configurações dos artefatos Notion.
    Cada instância representa uma database/página no Notion.
    """
    # Identificação
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    
    # IDs Notion (API 2025-09-03)
    notion_database_id = models.UUIDField(help_text="ID da database no Notion")
    data_source_id = models.UUIDField(help_text="ID do data source (API v2025-09-03)")
    
    # Mapeamento
    django_model = models.CharField(max_length=100, help_text="Modelo Django")
    
    # Schema e configurações
    notion_schema = models.JSONField(default=dict, help_text="Schema das propriedades")
    sync_enabled = models.BooleanField(default=True)
    sync_direction = models.CharField(max_length=20, choices=[
        ('bidirectional', 'Bidirecional'),
        ('django_to_notion', 'Django → Notion'),
        ('notion_to_django', 'Notion → Django'),
    ], default='bidirectional')
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração Notion"
        ordering = ['slug']
```

### 2. Shadow Models (Espelhos)

Para cada modelo principal, um shadow correspondente:

```python
class ContatoSync(models.Model):
    """
    Espelho do Contato para integração Notion.
    Contém dados pré-processados e ID externo.
    """
    # Relação 1:1 com original
    contato = models.OneToOneField(
        'clientes.Contato',
        on_delete=models.CASCADE,
        related_name='notion_sync'
    )
    
    # ID externo para localização exata
    external_id = models.CharField(
        max_length=36,
        unique=True,
        db_index=True,
        help_text="ID da página no Notion"
    )
    
    # Dados pré-processados
    nome_formatado = models.CharField(max_length=200)
    email_normalizado = models.EmailField(null=True, blank=True)
    telefone_formatado = models.CharField(max_length=20, null=True, blank=True)
    
    # Propriedades formatadas para Notion
    notion_properties = models.JSONField(default=dict)
    
    # Controle de sincronização
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendente'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro'),
    ], default='pending')
    sync_error = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['sync_status']),
        ]
```

### 3. Models de Apoio

```python
class NotionObjectMapping(models.Model):
    """
    Mapeamento genérico Django ↔ Notion.
    Funciona como index reverso rápido.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    external_id = models.CharField(max_length=36, db_index=True)
    config = models.ForeignKey(NotionDatabaseConfig, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['content_type', 'object_id']

class SyncLog(models.Model):
    """
    Log essencial de sincronização.
    Focado no necessário para debugging.
    """
    model_name = models.CharField(max_length=100)
    instance_id = models.PositiveIntegerField()
    external_id = models.CharField(max_length=36, null=True, blank=True)
    
    direction = models.CharField(max_length=20, choices=[
        ('to_notion', 'Django → Notion'),
        ('from_notion', 'Notion → Django'),
    ])
    operation = models.CharField(max_length=20)  # create, update, delete
    
    success = models.BooleanField()
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'instance_id']),
            models.Index(fields=['-created_at']),
        ]
```

---

## 🔄 Fluxo de Sincronização

### Django → Notion (Principal)

```python
# 1. Signal dispara no model original
@receiver(post_save, sender=Contato)
def contato_saved(sender, instance, created, **kwargs):
    """
    Quando um Contato é salvo, dispara sincronização.
    """
    # Busca ou cria shadow model
    shadow, created = ContatoSync.objects.get_or_create(
        contato=instance,
        defaults={'external_id': '', 'sync_status': 'pending'}
    )
    
    # Prepara dados para Notion
    shadow.prepare_notion_data()
    shadow.save()
    
    # Dispara task assíncrona
    sync_to_notion.delay('ContatoSync', shadow.pk)

# 2. Task Celery processa
@shared_task(bind=True, max_retries=3)
def sync_to_notion(self, model_name: str, instance_id: int):
    """
    Task assíncrona para sincronização com Notion.
    """
    try:
        # Busca shadow model
        Model = apps.get_model('notion_sync', model_name)
        shadow = Model.objects.get(pk=instance_id)
        
        # Busca configuração
        config = NotionDatabaseConfig.objects.get(django_model='Contato')
        
        # Prepara propriedades
        properties = ContatoMapper.to_notion_properties(shadow)
        
        # Sincroniza com Notion
        notion_service = NotionSyncService()
        if shadow.external_id:
            # Update existente
            notion_service.update_page(
                page_id=shadow.external_id,
                properties=properties
            )
        else:
            # Create novo
            page = notion_service.create_page(
                data_source_id=config.data_source_id,
                properties=properties
            )
            shadow.external_id = page['id']
        
        # Atualiza status
        shadow.sync_status = 'synced'
        shadow.last_sync_at = timezone.now()
        shadow.sync_error = None
        shadow.save()
        
        # Log sucesso
        SyncLog.objects.create(
            model_name=model_name,
            instance_id=instance_id,
            external_id=shadow.external_id,
            direction='to_notion',
            operation='update' if not created else 'create',
            success=True
        )
        
    except Exception as exc:
        # Retry com backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # Log erro
        SyncLog.objects.create(
            model_name=model_name,
            instance_id=instance_id,
            direction='to_notion',
            operation='sync',
            success=False,
            error_message=str(exc)
        )
        
        # Atualiza status erro
        shadow.sync_status = 'error'
        shadow.sync_error = str(exc)
        shadow.save()
```

### Notion → Django (Webhook)

```python
# views.py
@csrf_exempt
def notion_webhook(request):
    """
    Endpoint para receber webhooks do Notion.
    """
    if request.method == 'POST':
        payload = json.loads(request.body)
        
        # Processa diferentes tipos de eventos
        if payload['type'] == 'page.updated':
            handle_page_updated(payload)
        elif payload['type'] == 'page.created':
            handle_page_created(payload)
        
        return JsonResponse({'status': 'ok'})

def handle_page_updated(payload):
    """
    Processa atualização de página no Notion.
    """
    page_id = payload['data']['page']['id']
    
    # Busca mapeamento
    try:
        mapping = NotionObjectMapping.objects.get(external_id=page_id)
        shadow = mapping.content_object
        
        # Atualiza dados do shadow
        notion_service = NotionSyncService()
        page_data = notion_service.get_page(page_id)
        
        # Transforma dados Notion → Django
        updated_data = ContatoMapper.from_notion_properties(
            page_data['properties']
        )
        
        # Atualiza model original
        contato = shadow.contato
        contato.nome = updated_data['nome']
        contato.email = updated_data['email']
        contato.telefone = updated_data['telefone']
        contato.save()
        
        # Atualiza shadow
        shadow.last_sync_at = timezone.now()
        shadow.sync_status = 'synced'
        shadow.save()
        
        # Log
        SyncLog.objects.create(
            model_name='ContatoSync',
            instance_id=shadow.pk,
            external_id=page_id,
            direction='from_notion',
            operation='update',
            success=True
        )
        
    except NotionObjectMapping.DoesNotExist:
        # Página não mapeada, ignora
        pass
```

---

## 🎯 Mappers de Transformação

Cada modelo tem seu mapper específico:

### ContatoMapper

```python
class ContatoMapper:
    """
    Transforma dados entre Contato Django e Notion properties.
    """
    
    @staticmethod
    def to_notion_properties(shadow: ContatoSync) -> dict:
        """
        Converte shadow model para propriedades Notion.
        """
        contato = shadow.contato
        
        properties = {
            'Nome': {
                'title': [{'text': {'content': contato.nome}}]
            },
            'Email': {
                'email': contato.email or ''
            },
            'Telefone': {
                'phone': contato.telefone or ''
            },
            'Django ID': {
                'number': contato.id
            },
            'Data Criação': {
                'date': {
                    'start': contato.created_at.isoformat(),
                    'time_zone': 'America/Sao_Paulo'
                }
            },
            'Ativo': {
                'checkbox': contato.ativo
            }
        }
        
        # Trata campo observações (rich_text)
        if contato.observacoes:
            if len(contato.observacoes) > 1990:
                # Limita tamanho
                content = contato.observacoes[:1987] + '...'
            else:
                content = contato.observacoes
                
            properties['Observações'] = {
                'rich_text': [{'text': {'content': content}}]
            }
        
        return properties
    
    @staticmethod
    def from_notion_properties(properties: dict) -> dict:
        """
        Converte propriedades Notion para Django.
        """
        # Extrai nome (title)
        nome = ''
        if 'Nome' in properties:
            title_items = properties['Nome'].get('title', [])
            if title_items:
                nome = title_items[0].get('text', {}).get('content', '')
        
        # Extrai email
        email = properties.get('Email', {}).get('email', '')
        
        # Extrai telefone
        telefone = properties.get('Telefone', {}).get('phone', '')
        
        # Extrai observações
        observacoes = ''
        if 'Observações' in properties:
            rich_text_items = properties['Observações'].get('rich_text', [])
            if rich_text_items:
                observacoes = rich_text_items[0].get('text', {}).get('content', '')
        
        return {
            'nome': nome,
            'email': email,
            'telefone': telefone,
            'observacoes': observacoes
        }
```

---

## 📊 Models Sincronizados

| Modelo Django | Shadow Model | Direção | Prioridade |
|---------------|--------------|---------|------------|
| Contato | ContatoSync | Bidirecional | Alta |
| Cliente | ClienteSync | Bidirecional | Alta |
| Departamento | DepartamentoSync | Django → Notion | Média |
| AtendenteHumano | AtendenteSync | Bidirecional | Média |
| Atendimento | AtendimentoSync | Bidirecional | **Crítica** |
| Mensagem | MensagemSync | Django → Notion | Baixa |
| ❌ WhatsAppInstance | - | **Excluído** | - |

---

## 🔧 Configuração Inicial

### 1. Configurações no settings.py

```python
# Configurações Notion
NOTION_INTEGRATION_TOKEN = env('NOTION_TOKEN', default='')
NOTION_API_VERSION = '2025-09-03'

# Configurações de sincronização
NOTION_SYNC_ENABLED = env.bool('NOTION_SYNC_ENABLED', default=True)
NOTION_RETRY_MAX_ATTEMPTS = env.int('NOTION_RETRY_MAX_ATTEMPTS', default=3)
NOTION_RETRY_BACKOFF_FACTOR = env.int('NOTION_RETRY_BACKOFF_FACTOR', default=2)

# Rate limiting
NOTION_RATE_LIMIT_REQUESTS_PER_SECOND = env.int(
    'NOTION_RATE_LIMIT_RPS', 
    default=3
)
```

### 2. Configuração do Celery

```python
# Celery config
CELERY_BEAT_SCHEDULE = {
    'sync-pending-notion': {
        'task': 'notion_sync.tasks.sync_pending_items',
        'schedule': crontab(minute='*/5'),  # A cada 5 minutos
    },
    'cleanup-old-sync-logs': {
        'task': 'notion_sync.tasks.cleanup_sync_logs',
        'schedule': crontab(hour=2, minute=0),  # Diário às 2h
    },
}
```

### 3. Variáveis de Ambiente (.env.example)

```bash
# Notion Integration
NOTION_TOKEN=secret_nAbCdEfGhIjKlMnOpQrStUvWxYz
NOTION_SYNC_ENABLED=true

# Database IDs (obter do Notion)
NOTION_DATABASE_CONTATOS=12345678-1234-1234-1234-123456789012
NOTION_DATABASE_CLIENTES=87654321-4321-4321-4321-210987654321
NOTION_DATABASE_ATENDIMENTOS=11111111-1111-1111-1111-111111111111

# Rate Limiting
NOTION_RATE_LIMIT_RPS=3
```

---

## 🚀 Plano de Implementação

### Fase 1: Estrutura Base (2-3 dias)
- [ ] Criar app `notion_sync`
- [ ] Implementar `NotionDatabaseConfig`
- [ ] Criar `NotionObjectMapping` e `SyncLog`
- [ ] Configurar migrations

### Fase 2: Shadow Models (3-4 dias)
- [ ] Implementar `ContatoSync`
- [ ] Implementar `ClienteSync`
- [ ] Implementar `AtendimentoSync`
- [ ] Implementar outros shadow models
- [ ] Criar indices e otimizações

### Fase 3: Mappers (2-3 dias)
- [ ] Implementar `ContatoMapper`
- [ ] Implementar `ClienteMapper`
- [ ] Implementar `AtendimentoMapper`
- [ ] Implementar outros mappers
- [ ] Testes unitários dos mappers

### Fase 4: Serviços e Tasks (3-4 dias)
- [ ] Implementar `NotionSyncService`
- [ ] Criar tasks Celery
- [ ] Implementar retry e error handling
- [ ] Configurar rate limiting

### Fase 5: Signals e Webhook (2-3 dias)
- [ ] Implementar signals Django
- [ ] Criar endpoint webhook
- [ ] Implementar processamento Notion → Django
- [ ] Prevenção de loops infinitos

### Fase 6: Configuração e Deploy (2-3 dias)
- [ ] Configurar variáveis ambiente
- [ ] Setup databases no Notion
- [ ] Configurar webhook no Notion
- [ ] Testes de integração

### Fase 7: Documentação e Treinamento (1-2 dias)
- [ ] Documentar procedimentos
- [ ] Criar guia de troubleshooting
- [ ] Treinar equipe

**Total Estimado:** 15-22 dias úteis

---

## 🧪 Testes

### Testes Unitários

```python
class TestContatoMapper(TestCase):
    def test_to_notion_properties(self):
        """Testa transformação Django → Notion"""
        contato = Contato.objects.create(
            nome="João Silva",
            email="joao@email.com",
            telefone="11999999999"
        )
        shadow = ContatoSync.objects.create(contato=contato)
        
        properties = ContatoMapper.to_notion_properties(shadow)
        
        self.assertEqual(
            properties['Nome']['title'][0]['text']['content'],
            "João Silva"
        )
        self.assertEqual(
            properties['Email']['email'],
            "joao@email.com"
        )
    
    def test_from_notion_properties(self):
        """Testa transformação Notion → Django"""
        properties = {
            'Nome': {'title': [{'text': {'content': 'João Silva'}}]},
            'Email': {'email': 'joao@email.com'},
            'Telefone': {'phone': '11999999999'}
        }
        
        data = ContatoMapper.from_notion_properties(properties)
        
        self.assertEqual(data['nome'], 'João Silva')
        self.assertEqual(data['email'], 'joao@email.com')
```

### Testes de Integração

```python
class TestNotionIntegration(TestCase):
    @mock.patch('notion_sync.services.NotionSyncService')
    def test_sync_to_notion_success(self, mock_service):
        """Testa sincronização bem-sucedida"""
        # Setup
        mock_service.return_value.create_page.return_value = {
            'id': 'test-page-id'
        }
        
        contato = Contato.objects.create(nome="Test")
        shadow = ContatoSync.objects.create(contato=contato)
        
        # Execute
        sync_to_notion('ContatoSync', shadow.pk)
        
        # Assert
        shadow.refresh_from_db()
        self.assertEqual(shadow.external_id, 'test-page-id')
        self.assertEqual(shadow.sync_status, 'synced')
        
        # Verifica se SyncLog foi criado
        log = SyncLog.objects.latest('created_at')
        self.assertTrue(log.success)
```

---

## 📈 Monitoramento e Logging

### Estrutura de Logs

```python
# Log estruturado para sincronização
logger.info(
    "notion_sync_started",
    extra={
        'model': 'ContatoSync',
        'instance_id': shadow.pk,
        'operation': 'create',
        'direction': 'to_notion'
    }
)

# Log de erro
logger.error(
    "notion_sync_failed",
    extra={
        'model': 'ContatoSync',
        'instance_id': shadow.pk,
        'error': str(exc),
        'attempts': attempt_count
    }
)
```

### Métricas Importantes

- Taxa de sucesso de sincronização
- Tempo médio de sincronização
- Quantidade de erros por tipo
- Tamanho da fila de pendentes
- Performance dos mappers

---

## 🎓 Lições Aprendidas

### ✅ O que funciona bem
1. **Shadow Models**: Dados pré-processados melhoram performance
2. **Mappers específicos**: Fáceis de testar e manter
3. **Sincronização por ID**: Sem ambiguidades, performance otimizada
4. **Config centralizado**: Fácil manutenção

### ⚠️ Pontos de atenção
1. **API Notion rate limiting**: Respeitar limites rigorosamente
2. **Dados sensíveis**: Nunca sincronizar credenciais
3. **Loop prevention**: Implementar flags para evitar sincronização infinita
4. **Error handling**: Retry com backoff exponencial

---

## ✅ Conclusão

Esta abordagem simplificada oferece:

✅ **Simplicidade**: Menos complexidade, mais foco  
✅ **Performance**: Shadow models com dados pré-processados  
✅ **Manutenibilidade**: Mappers isolados e testáveis  
✅ **Flexibilidade**: Fácil adicionar novos modelos  
✅ **Robustez**: Tratamento de erros e retry automático  

**Pronto para implementação!** 🚀

---

**Status:** ✅ Aprovado  
**Próximo passo:** Iniciar Fase 1 - Estrutura Base