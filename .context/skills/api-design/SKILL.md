---
name: api-design
description: Design de APIs RESTful
phases: [P, R]
---

# API Design Skill

## Quando Usar

Use este skill quando:
- Projetando novos endpoints de API
- Revisando design de API existente
- Documentando contratos de API

## Instruções

### 1. Princípios REST

| Método | Uso | Idempotente |
|--------|-----|-------------|
| GET | Ler recurso(s) | Sim |
| POST | Criar recurso | Não |
| PUT | Substituir recurso | Sim |
| PATCH | Atualizar parcial | Não* |
| DELETE | Remover recurso | Sim |

### 2. Estrutura de URL

```
# Coleção
GET    /api/atendimentos/           # Listar
POST   /api/atendimentos/           # Criar

# Recurso individual
GET    /api/atendimentos/{id}/      # Detalhe
PUT    /api/atendimentos/{id}/      # Substituir
PATCH  /api/atendimentos/{id}/      # Atualizar
DELETE /api/atendimentos/{id}/      # Remover

# Ações customizadas
POST   /api/atendimentos/{id}/encerrar/

# Recursos aninhados
GET    /api/atendimentos/{id}/mensagens/
POST   /api/atendimentos/{id}/mensagens/

# Filtragem e paginação
GET    /api/atendimentos/?status=aberto&page=1&limit=20
```

### 3. Design de Response

#### Sucesso
```json
// GET /api/atendimentos/123/
{
    "id": 123,
    "cliente": {
        "id": 456,
        "nome": "Cliente Exemplo"
    },
    "status": "aberto",
    "created_at": "2026-01-25T10:00:00Z",
    "updated_at": "2026-01-25T10:30:00Z"
}

// GET /api/atendimentos/ (lista)
{
    "count": 100,
    "next": "/api/atendimentos/?page=2",
    "previous": null,
    "results": [...]
}
```

#### Erro
```json
// 400 Bad Request
{
    "error": "validation_error",
    "message": "Dados inválidos",
    "details": {
        "cliente": ["Este campo é obrigatório."]
    }
}

// 404 Not Found
{
    "error": "not_found",
    "message": "Atendimento não encontrado"
}

// 500 Internal Server Error
{
    "error": "internal_error",
    "message": "Erro interno do servidor"
}
```

### 4. Status Codes

| Code | Uso |
|------|-----|
| 200 | Sucesso (GET, PUT, PATCH) |
| 201 | Criado (POST) |
| 204 | Sem conteúdo (DELETE) |
| 400 | Erro de validação |
| 401 | Não autenticado |
| 403 | Não autorizado |
| 404 | Não encontrado |
| 409 | Conflito |
| 422 | Entidade não processável |
| 500 | Erro interno |

### 5. Implementação DRF

```python
# serializers.py
class AtendimentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)

    class Meta:
        model = Atendimento
        fields = ["id", "cliente", "cliente_nome", "status", "created_at"]
        read_only_fields = ["created_at"]


# views.py
class AtendimentoViewSet(viewsets.ModelViewSet):
    """API de Atendimentos."""

    serializer_class = AtendimentoSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "cliente"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Atendimento.objects.filter(
            tenant=self.request.user.tenant
        ).select_related("cliente")

    @action(detail=True, methods=["post"])
    def encerrar(self, request, pk=None):
        """Encerra o atendimento."""
        atendimento = self.get_object()
        atendimento.status = "encerrado"
        atendimento.save()
        return Response({"status": "encerrado"})


# urls.py
router = DefaultRouter()
router.register("atendimentos", AtendimentoViewSet, basename="atendimento")
urlpatterns = router.urls
```

### 6. Documentação OpenAPI

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

class AtendimentoViewSet(viewsets.ModelViewSet):
    @extend_schema(
        summary="Listar atendimentos",
        description="Retorna lista paginada de atendimentos do tenant.",
        parameters=[
            OpenApiParameter(
                name="status",
                description="Filtrar por status",
                required=False,
                type=str,
                enum=["aberto", "em_andamento", "encerrado"],
            ),
        ],
        responses={
            200: AtendimentoSerializer(many=True),
            401: {"description": "Não autenticado"},
        },
    )
    def list(self, request):
        ...
```

## Checklist

- [ ] URLs seguem padrão REST
- [ ] Métodos HTTP corretos
- [ ] Status codes apropriados
- [ ] Responses consistentes
- [ ] Erros bem formatados
- [ ] Paginação implementada
- [ ] Filtros disponíveis
- [ ] Documentação OpenAPI
