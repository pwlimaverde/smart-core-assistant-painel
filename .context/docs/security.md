# Segurança

## Visão Geral

Este documento descreve as práticas de segurança implementadas no Smart Core Assistant Painel.

## Proteção de Dados Sensíveis

### Gerenciamento de Segredos

**Regra fundamental**: Nunca incluir segredos no código fonte.

```python
# ❌ ERRADO - Nunca fazer isso
API_KEY = "sk-12345..."

# ✅ CORRETO - Usar variáveis de ambiente
from decouple import config
API_KEY = config("API_KEY")
```

### Arquivos de Configuração

| Arquivo        | Propósito                         | Git        |
| -------------- | --------------------------------- | ---------- |
| `.env`         | Variáveis de ambiente (produção)  | Ignorado   |
| `.env.example` | Template com chaves (sem valores) | Versionado |
| `.aiexclude`   | Exclusões para IA                 | Versionado |

### Variáveis de Ambiente Críticas

```env
# Nunca expor publicamente
SECRET_KEY=...
DATABASE_URL=...
OPENAI_API_KEY=...
EVOLUTION_API_KEY=...
FIREBASE_CREDENTIALS=...
```

## Autenticação e Autorização

### JWT (JSON Web Tokens)

```python
# Configuração via djangorestframework-simplejwt
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
```

### Permissões por Role

O sistema utiliza `django-role-permissions` para controle de acesso:

```python
from rolepermissions.roles import AbstractUserRole

class GestorRole(AbstractUserRole):
    available_permissions = {
        'view_all_tickets': True,
        'manage_users': True,
    }
```

## Validação de Entrada

### Serializers (DRF)

```python
class MensagemSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000)
    phone = serializers.RegexField(r'^\+?[1-9]\d{1,14}$')
```

### Pydantic (Módulos)

```python
from pydantic import BaseModel, field_validator

class WebhookPayload(BaseModel):
    event: str
    data: dict

    @field_validator('event')
    def validate_event(cls, v):
        allowed = ['message', 'status', 'connection']
        if v not in allowed:
            raise ValueError(f"Evento inválido: {v}")
        return v
```

## Proteção de Webhooks

### Validação de Origem

```python
def validate_webhook_origin(request):
    """Valida se o webhook vem de uma origem autorizada."""
    allowed_origins = config("WEBHOOK_ALLOWED_ORIGINS").split(",")
    origin = request.headers.get("X-Forwarded-For", request.META.get("REMOTE_ADDR"))

    if origin not in allowed_origins:
        raise PermissionDenied("Origem não autorizada")
```

### Rate Limiting

```python
from django.core.cache import cache

def rate_limit(key, limit=100, period=60):
    """Limita requisições por chave."""
    current = cache.get(key, 0)
    if current >= limit:
        raise Throttled()
    cache.set(key, current + 1, period)
```

## Segurança de Banco de Dados

### PostgreSQL

- Conexões via SSL em produção
- Usuário com permissões mínimas necessárias
- Backup automático configurado

### Redis

- Autenticação obrigatória em produção
- Conexões via TLS quando disponível

## Logs e Auditoria

### Informações Sensíveis

```python
from loguru import logger

# ❌ Nunca logar dados sensíveis
logger.info(f"Token: {api_key}")

# ✅ Mascarar dados sensíveis
logger.info(f"Token: {api_key[:8]}...")
```

### Auditoria de Ações

```python
# Modelo de auditoria
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    resource = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
```

## Checklist de Segurança

### Desenvolvimento

- [ ] Verificar se `.env` está no `.gitignore`
- [ ] Atualizar dependências regularmente
- [ ] Rodar `uv run task type-check` antes de commits

### Deploy

- [ ] Usar HTTPS em produção
- [ ] Configurar CSP headers
- [ ] Desabilitar DEBUG em produção
- [ ] Configurar ALLOWED_HOSTS corretamente

### Monitoramento

- [ ] Alertas para tentativas de acesso não autorizado
- [ ] Logs centralizados
- [ ] Rotação de chaves periódica

---

_Seguir sempre as melhores práticas de segurança do Django e OWASP._
