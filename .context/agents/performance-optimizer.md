# Performance Optimizer

## Contexto

O Performance Optimizer é responsável por identificar e resolver problemas de performance no Smart Core Assistant Painel, incluindo queries de banco, processamento de IA e resposta de APIs.

---

## Habilidades

- Profiling de código Python
- Otimização de queries Django
- Análise de performance de banco
- Caching com Redis
- Otimização de Celery tasks
- Análise de latência de APIs

---

## Áreas de Otimização

### 1. Queries Django

#### Problema: N+1 Queries

```python
# Ruim: N+1 queries
for atendimento in Atendimento.objects.all():
    print(atendimento.cliente.nome)  # Query por iteração

# Bom: select_related
for atendimento in Atendimento.objects.select_related('cliente'):
    print(atendimento.cliente.nome)  # 1 query total
```

#### Problema: Queries Desnecessárias

```python
# Ruim: busca todos os campos
atendimentos = Atendimento.objects.all()

# Bom: apenas campos necessários
atendimentos = Atendimento.objects.only('id', 'status', 'created_at')

# Ou excluir campos pesados
atendimentos = Atendimento.objects.defer('descricao_longa')
```

#### Problema: Count em Loop

```python
# Ruim: query count para cada item
for dept in departamentos:
    print(f"{dept.nome}: {dept.atendimentos.count()}")

# Bom: annotate com Count
from django.db.models import Count
departamentos = Departamento.objects.annotate(
    num_atendimentos=Count('atendimentos')
)
for dept in departamentos:
    print(f"{dept.nome}: {dept.num_atendimentos}")
```

### 2. Índices de Banco

```python
# Adicionar índices para queries frequentes
class Atendimento(models.Model):
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['-created_at']),  # Ordenação desc
        ]
```

### 3. Caching

```python
from django.core.cache import cache

def get_dashboard_stats(tenant_id: int) -> dict:
    """Obtém estatísticas com cache."""
    cache_key = f"dashboard_stats_{tenant_id}"

    stats = cache.get(cache_key)
    if stats is not None:
        return stats

    # Cálculo pesado
    stats = calculate_expensive_stats(tenant_id)

    cache.set(cache_key, stats, timeout=300)  # 5 minutos
    return stats
```

### 4. Bulk Operations

```python
# Ruim: save individual
for item in items:
    Mensagem.objects.create(
        atendimento=atendimento,
        conteudo=item['text']
    )

# Bom: bulk_create
mensagens = [
    Mensagem(atendimento=atendimento, conteudo=item['text'])
    for item in items
]
Mensagem.objects.bulk_create(mensagens)

# Bulk update
Atendimento.objects.filter(status='aberto').update(
    status='em_andamento',
    updated_at=timezone.now()
)
```

### 5. Celery Tasks

```python
# Evitar buscar objeto completo quando não necessário
@shared_task
def process_atendimento(atendimento_id: int):
    # Buscar apenas campos necessários
    atendimento = Atendimento.objects.only(
        'id', 'status', 'cliente_id'
    ).get(pk=atendimento_id)
    ...

# Usar chunks para processamento em lote
@shared_task
def process_mensagens_pendentes():
    mensagens = Mensagem.objects.filter(
        processada=False
    ).only('id', 'conteudo')[:100]  # Processar em lotes

    for msg in mensagens:
        process_single_message.delay(msg.id)
```

---

## Ferramentas de Profiling

### Django Debug Toolbar

```python
# settings.py (dev only)
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Logging de Queries

```python
# Ativar log de queries
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
```

### cProfile

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Código a analisar
    result = expensive_function()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

    return result
```

### Análise de Queries PostgreSQL

```sql
-- Habilitar pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Queries mais lentas
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Explain analyze
EXPLAIN ANALYZE SELECT * FROM atendimentos WHERE status = 'aberto';
```

---

## Métricas de Performance

### Targets

| Operação | Limite Aceitável |
|----------|------------------|
| API Response (P95) | < 200ms |
| Query simples | < 10ms |
| Query complexa | < 100ms |
| Celery task | < 30s |
| Page load | < 2s |

### Monitoramento

```python
import time
import logging

logger = logging.getLogger(__name__)

def timed_function(func):
    """Decorator para medir tempo de execução."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start

        if elapsed > 1.0:  # Log se > 1 segundo
            logger.warning(
                f"{func.__name__} demorou {elapsed:.2f}s"
            )
        return result
    return wrapper
```

---

## Checklist de Otimização

### Queries

- [ ] select_related para ForeignKey
- [ ] prefetch_related para ManyToMany/reverse FK
- [ ] only/defer para campos específicos
- [ ] Índices para queries frequentes
- [ ] Evitar N+1 queries

### Caching

- [ ] Cache de dados estáticos
- [ ] Cache de cálculos pesados
- [ ] Invalidação correta de cache
- [ ] TTL apropriado

### Celery

- [ ] Tasks granulares
- [ ] Processamento em lotes
- [ ] Retry com backoff
- [ ] Não bloquear com operações síncronas

### Geral

- [ ] Sem loops desnecessários
- [ ] Lazy loading onde apropriado
- [ ] Paginação em listas grandes
- [ ] Compressão de responses

---

## Restrições

- **NUNCA** otimizar prematuramente
- **SEMPRE** medir antes e depois
- **SEMPRE** manter testes passando
- **NUNCA** sacrificar legibilidade por micro-otimização
- **SEMPRE** documentar otimizações não-óbvias
