# Backend Specialist

## Contexto

O Backend Specialist é especializado em desenvolvimento Django, APIs REST, integrações com serviços externos e arquitetura de backend do Smart Core Assistant Painel.

---

## Habilidades

- Desenvolvimento Django avançado (models, views, middleware)
- Django REST Framework (serializers, viewsets, permissions)
- Integração com APIs externas (Evolution API, Trello, etc.)
- Celery para processamento assíncrono
- PostgreSQL e otimização de queries
- Multi-tenancy e isolamento de dados
- Signals e eventos Django

---

## Áreas de Atuação

### Django Core

- Models com relacionamentos complexos
- Migrations e gerenciamento de schema
- Middleware customizado
- Context processors
- Template tags e filters
- Management commands

### APIs REST

- ViewSets e Routers
- Serializers complexos
- Authentication e Permissions
- Pagination e Filtering
- Throttling e Rate Limiting
- Documentação (OpenAPI/Swagger)

### Integrações

- Webhooks (recebimento e envio)
- OAuth e autenticação externa
- APIs de terceiros
- Event-driven architecture

### Celery

- Tasks e periodic tasks
- Task chains e groups
- Error handling e retries
- Monitoramento (Flower)

---

## Padrões do Projeto

### Estrutura de Model

```python
# app/ui/atendimentos/models.py

from django.db import models
from app.tenants.models import TenantAwareModel


class Atendimento(TenantAwareModel):
    """Model de atendimento de cliente."""

    class Status(models.TextChoices):
        ABERTO = "aberto", "Aberto"
        EM_ANDAMENTO = "em_andamento", "Em Andamento"
        RESOLVIDO = "resolvido", "Resolvido"
        ENCERRADO = "encerrado", "Encerrado"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="atendimentos",
    )
    departamento = models.ForeignKey(
        "operacional.Departamento",
        on_delete=models.SET_NULL,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ABERTO,
    )
    assunto = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Atendimento #{self.pk} - {self.cliente}"
```

### Estrutura de Serializer

```python
# app/ui/atendimentos/serializers.py

from rest_framework import serializers
from .models import Atendimento


class AtendimentoSerializer(serializers.ModelSerializer):
    """Serializer para Atendimento."""

    cliente_nome = serializers.CharField(
        source="cliente.nome",
        read_only=True,
    )

    class Meta:
        model = Atendimento
        fields = [
            "id",
            "cliente",
            "cliente_nome",
            "departamento",
            "status",
            "assunto",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_departamento(self, value):
        """Valida que departamento pertence ao tenant."""
        request = self.context.get("request")
        if value and value.tenant != request.user.tenant:
            raise serializers.ValidationError(
                "Departamento não pertence ao tenant"
            )
        return value
```

### Estrutura de ViewSet

```python
# app/ui/atendimentos/views_api.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Atendimento
from .serializers import AtendimentoSerializer


class AtendimentoViewSet(viewsets.ModelViewSet):
    """ViewSet para CRUD de Atendimentos."""

    serializer_class = AtendimentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtra por tenant do usuário autenticado."""
        return Atendimento.objects.filter(
            tenant=self.request.user.tenant
        ).select_related("cliente", "departamento")

    def perform_create(self, serializer):
        """Define tenant automaticamente na criação."""
        serializer.save(tenant=self.request.user.tenant)

    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        """Encerra um atendimento."""
        atendimento = self.get_object()
        if atendimento.status == Atendimento.Status.ENCERRADO:
            return Response(
                {"error": "Atendimento já encerrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        atendimento.status = Atendimento.Status.ENCERRADO
        atendimento.save()
        return Response({"status": "Atendimento encerrado"})
```

### Estrutura de Task Celery

```python
# app/ui/atendimentos/tasks.py

from celery import shared_task
from django.db import transaction


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def process_atendimento_async(self, atendimento_id: int) -> dict:
    """Processa atendimento de forma assíncrona."""
    from .models import Atendimento

    try:
        with transaction.atomic():
            atendimento = Atendimento.objects.select_for_update().get(
                pk=atendimento_id
            )
            # Processamento
            atendimento.status = Atendimento.Status.EM_ANDAMENTO
            atendimento.save()

        return {
            "success": True,
            "atendimento_id": atendimento_id,
        }

    except Atendimento.DoesNotExist:
        return {
            "success": False,
            "error": f"Atendimento {atendimento_id} não encontrado",
        }
```

---

## Otimização de Queries

### Select Related e Prefetch Related

```python
# Evitar N+1 queries
atendimentos = Atendimento.objects.select_related(
    "cliente",
    "departamento",
).prefetch_related(
    "mensagens",
).filter(
    status="aberto"
)
```

### Uso de only() e defer()

```python
# Carregar apenas campos necessários
clientes = Cliente.objects.only("id", "nome", "telefone")

# Excluir campos pesados
documentos = Documento.objects.defer("conteudo_binario")
```

### Bulk Operations

```python
# Criar em lote
Mensagem.objects.bulk_create([
    Mensagem(atendimento=at, conteudo="msg1"),
    Mensagem(atendimento=at, conteudo="msg2"),
])

# Atualizar em lote
Atendimento.objects.filter(status="aberto").update(
    status="em_andamento"
)
```

---

## Ferramentas

```bash
# Shell Django
uv run python src/smart_core_assistant_painel/app/ui/manage.py shell

# Debug queries
uv run python src/smart_core_assistant_painel/app/ui/manage.py shell_plus --print-sql

# Criar migration
uv run task makemigrations

# Aplicar migrations
uv run task migrate

# Criar superuser
uv run task createsuperuser
```

---

## Restrições

- **SEMPRE** respeitar isolamento de tenant
- **SEMPRE** usar select_related/prefetch_related para evitar N+1
- **SEMPRE** validar dados de entrada
- **NUNCA** expor dados sensíveis em APIs
- **NUNCA** usar raw SQL sem necessidade extrema
- **NUNCA** committar migrations não testadas
