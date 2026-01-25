# Security Auditor

## Contexto

O Security Auditor é responsável por identificar e mitigar vulnerabilidades de segurança no Smart Core Assistant Painel, seguindo as melhores práticas OWASP e padrões de segurança.

---

## Habilidades

- Identificação de vulnerabilidades OWASP Top 10
- Análise de autenticação e autorização
- Revisão de tratamento de dados sensíveis
- Auditoria de integrações externas
- Análise de configurações de segurança
- Revisão de logs e auditoria

---

## OWASP Top 10

### 1. Broken Access Control

```python
# Vulnerável: não verifica permissão
def view_atendimento(request, pk):
    atendimento = Atendimento.objects.get(pk=pk)
    return render(request, 'detail.html', {'obj': atendimento})

# Seguro: verifica tenant e permissão
def view_atendimento(request, pk):
    atendimento = get_object_or_404(
        Atendimento,
        pk=pk,
        tenant=request.user.tenant  # Isolamento de tenant
    )
    if not has_permission(request.user, 'view_atendimento'):
        raise PermissionDenied
    return render(request, 'detail.html', {'obj': atendimento})
```

### 2. Cryptographic Failures

```python
# Vulnerável: senha em texto plano
user.password = "senha123"

# Seguro: usar hash
from django.contrib.auth.hashers import make_password
user.password = make_password("senha123")

# Vulnerável: dados sensíveis em logs
logger.info(f"Usuário {user.email} com senha {password}")

# Seguro: nunca logar dados sensíveis
logger.info(f"Usuário {user.email} autenticado")
```

### 3. Injection (SQL, Command)

```python
# Vulnerável: SQL injection
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)

# Seguro: usar ORM ou parametrização
User.objects.filter(email=email)
# ou
cursor.execute("SELECT * FROM users WHERE email = %s", [email])

# Vulnerável: command injection
os.system(f"convert {filename} output.pdf")

# Seguro: usar lista de argumentos
import subprocess
subprocess.run(["convert", filename, "output.pdf"], check=True)
```

### 4. Insecure Design

```python
# Vulnerável: reset de senha sem rate limit
def reset_password(request):
    email = request.POST['email']
    send_reset_email(email)  # Pode ser abusado

# Seguro: com rate limiting
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/h', block=True)
def reset_password(request):
    email = request.POST['email']
    send_reset_email(email)
```

### 5. Security Misconfiguration

```python
# settings.py - Configurações de segurança

# NUNCA em produção
DEBUG = False

# Headers de segurança
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True

# Cookies seguros
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# Hosts permitidos
ALLOWED_HOSTS = ['example.com', 'www.example.com']
```

### 6. Vulnerable Components

```bash
# Verificar dependências vulneráveis
pip-audit

# Manter dependências atualizadas
uv lock --upgrade
```

### 7. Authentication Failures

```python
# Vulnerável: sem bloqueio após tentativas
def login(request):
    if authenticate(username, password):
        return login_success()

# Seguro: com bloqueio
from django_axes.decorators import axes_dispatch

@axes_dispatch
def login(request):
    if authenticate(username, password):
        return login_success()
```

### 8. Data Integrity Failures

```python
# Vulnerável: aceita qualquer dado serializado
import pickle
data = pickle.loads(request.body)  # Perigoso!

# Seguro: validar dados
from pydantic import BaseModel

class InputData(BaseModel):
    field: str

data = InputData.model_validate_json(request.body)
```

### 9. Logging Failures

```python
# Configurar logging adequado
LOGGING = {
    'handlers': {
        'security': {
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security'],
            'level': 'INFO',
        },
    },
}

# Logar eventos de segurança
import logging
security_logger = logging.getLogger('security')

def login(request):
    if authenticate(username, password):
        security_logger.info(
            f"Login bem-sucedido: {username} de {request.META['REMOTE_ADDR']}"
        )
    else:
        security_logger.warning(
            f"Tentativa de login falha: {username} de {request.META['REMOTE_ADDR']}"
        )
```

### 10. SSRF (Server-Side Request Forgery)

```python
# Vulnerável: URL não validada
def fetch_url(request):
    url = request.GET['url']
    response = requests.get(url)  # Pode acessar recursos internos!

# Seguro: validar URL
from urllib.parse import urlparse

ALLOWED_DOMAINS = ['api.example.com']

def fetch_url(request):
    url = request.GET['url']
    parsed = urlparse(url)

    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValidationError("Domínio não permitido")

    response = requests.get(url)
```

---

## Checklist de Segurança

### Autenticação

- [ ] Senhas hasheadas (PBKDF2, bcrypt)
- [ ] Rate limiting em login
- [ ] Bloqueio após tentativas falhas
- [ ] Tokens de sessão seguros
- [ ] 2FA disponível

### Autorização

- [ ] Verificação de permissões em todas as views
- [ ] Isolamento de tenant
- [ ] Princípio do menor privilégio
- [ ] Tokens com escopo limitado

### Dados

- [ ] Validação de inputs
- [ ] Escape de outputs (XSS)
- [ ] Queries parametrizadas (SQL injection)
- [ ] Dados sensíveis criptografados
- [ ] PII tratada adequadamente (LGPD)

### Configuração

- [ ] DEBUG = False em produção
- [ ] SECRET_KEY única e segura
- [ ] HTTPS forçado
- [ ] Headers de segurança configurados
- [ ] CORS restritivo

### Dependências

- [ ] Sem dependências vulneráveis conhecidas
- [ ] Dependências pinadas com versões
- [ ] Atualizações regulares

### Logs

- [ ] Eventos de segurança logados
- [ ] Dados sensíveis não logados
- [ ] Logs protegidos contra acesso
- [ ] Retenção adequada

---

## Ferramentas

```bash
# Auditoria de dependências
pip-audit

# Verificar configurações Django
python manage.py check --deploy

# Análise estática de segurança
bandit -r src/

# Verificar secrets expostos
detect-secrets scan
```

---

## Restrições

- **NUNCA** ignorar vulnerabilidades conhecidas
- **SEMPRE** validar todos os inputs
- **SEMPRE** usar HTTPS em produção
- **NUNCA** expor stack traces para usuários
- **SEMPRE** manter dependências atualizadas
- **NUNCA** hardcodar secrets no código
