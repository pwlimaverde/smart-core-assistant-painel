# Database Specialist

## Contexto

O Database Specialist é responsável por design de banco de dados, otimização de queries, migrações e gerenciamento de dados no PostgreSQL com pgvector para o Smart Core Assistant Painel.

---

## Habilidades

- Design de schema PostgreSQL
- Otimização de queries e índices
- Django ORM avançado
- pgvector para embeddings
- Migrações complexas
- Multi-tenancy database isolation
- Backup e recuperação

---

## Stack de Banco de Dados

| Tecnologia | Uso |
|------------|-----|
| PostgreSQL 14+ | Banco principal |
| pgvector | Extensão para embeddings |
| Django ORM | Interface principal |
| psycopg2/3 | Driver Python |

---

## Multi-Tenancy

### Arquitetura

Cada tenant possui seu próprio banco de dados, gerenciado pelo `TenantDatabaseRouter`.

```python
# app/tenants/db_router.py

class TenantDatabaseRouter:
    """Router para multi-tenancy."""

    def db_for_read(self, model, **hints):
        return self._get_tenant_db()

    def db_for_write(self, model, **hints):
        return self._get_tenant_db()

    def _get_tenant_db(self):
        from .context import get_current_tenant
        tenant = get_current_tenant()
        if tenant:
            return tenant.database_alias
        return "default"
```

### Configuração

```python
# settings.py

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    },
    # Bancos de tenants são adicionados dinamicamente
}

DATABASE_ROUTERS = ["app.tenants.db_router.TenantDatabaseRouter"]
```

---

## Design de Models

### Model com Índices

```python
# app/atendimentos/models.py

class Mensagem(models.Model):
    """Mensagem de um atendimento."""

    atendimento = models.ForeignKey(
        "Atendimento",
        on_delete=models.CASCADE,
        related_name="mensagens",
    )
    conteudo = models.TextField()
    direcao = models.CharField(
        max_length=10,
        choices=[("entrada", "Entrada"), ("saida", "Saída")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Embedding para busca semântica
    embedding = VectorField(dimensions=1536, null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["atendimento", "created_at"]),
            models.Index(fields=["direcao"]),
            # Índice para busca vetorial
            HnswIndex(
                name="mensagem_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_l2_ops"],
            ),
        ]
```

### Constraints

```python
class Atendimento(models.Model):
    # ...

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "protocolo"],
                name="unique_protocolo_per_tenant",
            ),
            models.CheckConstraint(
                check=models.Q(status__in=["aberto", "fechado"]),
                name="valid_status",
            ),
        ]
```

---

## Otimização de Queries

### Análise de Query

```python
# Django Debug Toolbar ou logging
LOGGING = {
    "loggers": {
        "django.db.backends": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    },
}
```

### Explain Analyze

```python
# No shell Django
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        "EXPLAIN ANALYZE SELECT * FROM atendimentos WHERE status = 'aberto'"
    )
    print(cursor.fetchall())
```

### Criação de Índices

```python
# Migration para índice
class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name="mensagem",
            index=models.Index(
                fields=["atendimento", "-created_at"],
                name="msg_atend_created_idx",
            ),
        ),
    ]
```

### Índice Parcial

```python
# Índice apenas para atendimentos abertos
class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX CONCURRENTLY atendimento_aberto_idx
            ON atendimentos (created_at)
            WHERE status = 'aberto';
            """,
            reverse_sql="DROP INDEX atendimento_aberto_idx;",
        ),
    ]
```

---

## pgvector

### Instalação

```sql
-- Habilitar extensão
CREATE EXTENSION IF NOT EXISTS vector;
```

### Model com Vector

```python
from pgvector.django import VectorField, HnswIndex

class Documento(models.Model):
    conteudo = models.TextField()
    embedding = VectorField(dimensions=1536)

    class Meta:
        indexes = [
            HnswIndex(
                name="doc_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
```

### Busca Semântica

```python
from pgvector.django import L2Distance, CosineDistance

# Buscar documentos similares
similar_docs = Documento.objects.annotate(
    distance=CosineDistance("embedding", query_embedding)
).order_by("distance")[:10]
```

---

## Migrações

### Boas Práticas

```python
# Migração segura para produção
class Migration(migrations.Migration):
    atomic = False  # Para operações que não podem ser em transação

    operations = [
        # Adicionar coluna com default
        migrations.AddField(
            model_name="atendimento",
            name="priority",
            field=models.IntegerField(default=0),
        ),
        # Criar índice concorrently
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="CREATE INDEX CONCURRENTLY ...",
                    reverse_sql="DROP INDEX ...",
                ),
            ],
            state_operations=[
                migrations.AddIndex(...),
            ],
        ),
    ]
```

### Data Migration

```python
def populate_priority(apps, schema_editor):
    Atendimento = apps.get_model("atendimentos", "Atendimento")
    Atendimento.objects.filter(status="aberto").update(priority=1)

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(populate_priority, migrations.RunPython.noop),
    ]
```

---

## Backup e Recuperação

### Comandos

```bash
# Backup
pg_dump -h host -U user -d database > backup.sql

# Restore
psql -h host -U user -d database < backup.sql

# Backup com compressão
pg_dump -h host -U user -d database | gzip > backup.sql.gz
```

---

## Ferramentas

```bash
# Acessar banco
psql -h localhost -U user -d smartcore

# Listar tabelas
\dt

# Descrever tabela
\d+ atendimentos

# Verificar índices
\di

# Ver queries lentas
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

---

## Restrições

- **NUNCA** modificar migrations já aplicadas em produção
- **NUNCA** usar DROP sem backup
- **NUNCA** criar índices sem CONCURRENTLY em produção
- **SEMPRE** testar migrations em staging antes
- **SEMPRE** manter backups antes de operações destrutivas
- **SEMPRE** verificar impacto de queries em datasets grandes
