# Segurança

Este documento descreve as práticas de segurança e gestão de credenciais do projeto.

---

## Modelo de Autenticação

### Autenticação de Usuários

O sistema utiliza autenticação baseada em sessões Django com as seguintes características:

- **Backend**: Django Authentication
- **Password Hashing**: PBKDF2 com SHA256
- **Session Storage**: Database-backed sessions
- **Session Timeout**: Configurável por tenant

### Fluxo de Login

```
1. Usuário submete credenciais
2. Django valida contra banco do tenant
3. Sessão criada com CSRF token
4. Usuário redirecionado ao dashboard
```

### Recuperação de Senha

- Email de recuperação com token temporário
- Token expira em 24 horas
- Link único por solicitação

---

## Autorização e Permissões

### Sistema de Roles

O projeto utiliza **django-role-permissions** para controle de acesso:

```python
# Definição de roles em app/core/roles.py

from rolepermissions.roles import AbstractUserRole

class Admin(AbstractUserRole):
    available_permissions = {
        "manage_users": True,
        "manage_departments": True,
        "view_reports": True,
        "manage_integrations": True,
    }

class Supervisor(AbstractUserRole):
    available_permissions = {
        "manage_atendimentos": True,
        "view_reports": True,
        "assign_atendentes": True,
    }

class Atendente(AbstractUserRole):
    available_permissions = {
        "process_atendimentos": True,
        "send_messages": True,
    }
```

### Verificação de Permissões

```python
from rolepermissions.checkers import has_permission

if has_permission(user, "manage_users"):
    # Permite acesso
    pass
```

---

## Multi-Tenancy e Isolamento

### Isolamento de Dados

Cada tenant possui banco de dados separado, garantindo:

- **Isolamento completo**: Dados nunca se misturam
- **Backup independente**: Possível fazer backup/restore por tenant
- **Migração individual**: Migrações podem ser aplicadas por tenant

### Middleware de Tenant

```python
# TenantMiddleware identifica tenant a cada request
class TenantMiddleware:
    def __call__(self, request):
        tenant = self.get_tenant_from_request(request)
        if tenant:
            set_current_tenant(tenant)
        return self.get_response(request)
```

---

## Gestão de Secrets

### Variáveis de Ambiente

Todos os secrets são armazenados em variáveis de ambiente (`.env`):

```bash
# Exemplo de .env (NÃO commitado)
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=postgres://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0

# APIs Externas
EVOLUTION_API_KEY=xxx
OPENAI_API_KEY=xxx
GROQ_API_KEY=xxx

# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/credentials.json
```

### Boas Práticas

| Prática | Descrição |
|---------|-----------|
| **Nunca hardcode** | Secrets nunca no código fonte |
| **Rotação regular** | Trocar secrets periodicamente |
| **Princípio do menor privilégio** | Apenas permissões necessárias |
| **Logs seguros** | Nunca logar valores de secrets |
| **Ambientes separados** | Secrets diferentes por ambiente |

### Arquivos Sensíveis

Arquivos que **nunca** devem ser commitados:

```gitignore
# .gitignore
.env
.env.local
.env.*.local
*.pem
*.key
firebase_key.json
credentials.json
```

---

## Segurança de API

### CSRF Protection

Todas as views Django incluem proteção CSRF por padrão.

```python
# Requisições AJAX devem incluir token
headers: {
    'X-CSRFToken': getCookie('csrftoken')
}
```

### Rate Limiting

Webhooks e APIs públicas possuem rate limiting:

```python
# Configuração de throttling DRF
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### Validação de Webhooks

Webhooks da Evolution API são validados:

```python
def validate_webhook(request):
    # Verificar signature
    signature = request.headers.get("X-Hub-Signature")
    if not verify_signature(request.body, signature):
        raise PermissionDenied("Invalid signature")
```

---

## Proteção de Dados

### Dados Pessoais

O sistema processa dados pessoais de clientes (LGPD):

| Dado | Tratamento |
|------|------------|
| Nome | Armazenado criptografado em repouso |
| Telefone | Utilizado para identificação WhatsApp |
| Mensagens | Armazenadas com isolamento por tenant |

### Retenção de Dados

- Mensagens: Configurável por tenant (padrão 90 dias)
- Logs de webhook: 30 dias
- Sessões expiradas: Limpeza automática

### Direitos do Titular

- **Acesso**: Exportação de dados disponível
- **Exclusão**: Soft-delete com opção de hard-delete
- **Portabilidade**: Formato JSON/CSV

---

## Logs e Auditoria

### O que é Logado

| Evento | Dados |
|--------|-------|
| Login/Logout | Usuário, IP, timestamp |
| Alteração de dados | Usuário, objeto, antes/depois |
| Erros de API | Endpoint, payload (sem secrets), erro |
| Webhooks | Origem, tipo, status |

### O que NÃO é Logado

- Senhas (nem hashes)
- Tokens de API completos
- Dados de cartão de crédito
- Conteúdo de mensagens em logs de erro

### Armazenamento de Logs

```python
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/app.log',
        },
    },
}
```

---

## Checklist de Segurança

### Antes de Deploy

- [ ] SECRET_KEY única gerada
- [ ] DEBUG = False em produção
- [ ] ALLOWED_HOSTS configurado
- [ ] HTTPS forçado
- [ ] Cookies seguros
- [ ] CSRF habilitado
- [ ] Headers de segurança configurados

### Headers de Segurança

```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```
