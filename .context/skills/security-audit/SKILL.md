---
name: security-audit
description: Auditoria de segurança e vulnerabilidades
phases: [R, V]
---

# Security Audit Skill

## Quando Usar

Use este skill quando:
- Revisando segurança de código
- Verificando vulnerabilidades OWASP
- Auditando configurações

## Instruções

### 1. OWASP Top 10 Checklist

#### A01 - Broken Access Control
```python
# ❌ Vulnerável
def view_atendimento(request, pk):
    atendimento = Atendimento.objects.get(pk=pk)
    return render(request, "detail.html", {"obj": atendimento})

# ✅ Seguro
def view_atendimento(request, pk):
    atendimento = get_object_or_404(
        Atendimento,
        pk=pk,
        tenant=request.user.tenant  # Isolamento
    )
    if not has_permission(request.user, "view_atendimento"):
        raise PermissionDenied
    return render(request, "detail.html", {"obj": atendimento})
```

#### A02 - Cryptographic Failures
```python
# ❌ Vulnerável
user.password = "senha123"  # Texto plano

# ✅ Seguro
from django.contrib.auth.hashers import make_password
user.password = make_password("senha123")
```

#### A03 - Injection
```python
# ❌ Vulnerável (SQL Injection)
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ Seguro
User.objects.filter(email=email)

# ❌ Vulnerável (Command Injection)
os.system(f"convert {filename} output.pdf")

# ✅ Seguro
subprocess.run(["convert", filename, "output.pdf"], check=True)
```

#### A04 - Insecure Design
```python
# ❌ Sem rate limiting
def reset_password(request):
    send_reset_email(request.POST["email"])

# ✅ Com rate limiting
from django_ratelimit.decorators import ratelimit

@ratelimit(key="ip", rate="5/h", block=True)
def reset_password(request):
    send_reset_email(request.POST["email"])
```

#### A05 - Security Misconfiguration
```python
# settings.py - Produção
DEBUG = False
ALLOWED_HOSTS = ["example.com"]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

#### A06 - Vulnerable Components
```bash
# Verificar dependências
pip-audit
```

#### A07 - Authentication Failures
```python
# Usar django-axes para bloqueio
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
```

#### A08 - Data Integrity Failures
```python
# ❌ Vulnerável
import pickle
data = pickle.loads(request.body)

# ✅ Seguro
from pydantic import BaseModel
data = InputModel.model_validate_json(request.body)
```

#### A09 - Logging Failures
```python
# Logar eventos de segurança
security_logger.info(f"Login: {username} de {ip}")
security_logger.warning(f"Login falho: {username} de {ip}")

# NUNCA logar dados sensíveis
# ❌ logger.info(f"User {email} password {password}")
```

#### A10 - SSRF
```python
# ❌ Vulnerável
def fetch(request):
    url = request.GET["url"]
    return requests.get(url)  # Pode acessar rede interna

# ✅ Seguro
ALLOWED_DOMAINS = ["api.example.com"]

def fetch(request):
    url = request.GET["url"]
    if urlparse(url).hostname not in ALLOWED_DOMAINS:
        raise ValidationError("Domínio não permitido")
    return requests.get(url)
```

### 2. Verificações Automatizadas

```bash
# Auditoria de dependências
pip-audit

# Análise estática de segurança
bandit -r src/

# Verificar configurações Django
python manage.py check --deploy

# Detectar secrets expostos
detect-secrets scan
```

### 3. Checklist de Configuração

```python
# settings.py

# ✅ Secrets em variáveis de ambiente
SECRET_KEY = os.environ["SECRET_KEY"]

# ✅ Debug desabilitado
DEBUG = False

# ✅ Hosts permitidos
ALLOWED_HOSTS = ["example.com"]

# ✅ HTTPS forçado
SECURE_SSL_REDIRECT = True

# ✅ Cookies seguros
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# ✅ Headers de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
```

### 4. Relatório de Auditoria

```markdown
# Relatório de Segurança

## Resumo
- **Data:** 2026-01-25
- **Escopo:** [módulos auditados]
- **Severidade geral:** [Alta/Média/Baixa]

## Vulnerabilidades Encontradas

### 1. [Título] - Severidade: Alta
**Arquivo:** `path/to/file.py:42`
**Categoria:** OWASP A03 - Injection
**Descrição:** [detalhes]
**Remediação:** [como corrigir]

## Configurações Verificadas
- [x] DEBUG = False
- [x] HTTPS habilitado
- [ ] Rate limiting configurado

## Recomendações
1. ...
2. ...
```

## Checklist

- [ ] OWASP Top 10 verificado
- [ ] Dependências auditadas
- [ ] Configurações revisadas
- [ ] Secrets não expostos
- [ ] Logging de segurança ok
- [ ] Multi-tenancy isolado
