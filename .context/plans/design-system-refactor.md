# PRD - Refatoração do Design System

## Título da Feature
Design System Desacoplado — `modules/design_system/` com Jinja2 + Adaptador Django

## Resumo Executivo

O projeto tem 240 ocorrências de `#a98f71` hardcoded, 0/64 templates usando os componentes CSS
definidos, e toda a lógica de layout misturada com Django Template Language (DTL) — o que torna
impossível portar o frontend sem reescrever tudo.

A solução é criar `modules/design_system/` como um módulo independente com:
- **CSS/JS puro** (Tailwind tokens + componentes) — 100% framework-agnostic
- **Templates Jinja2** — compatíveis com Django e FastAPI nativamente
- **Adaptador Django isolado** — toda a cola com Django fica em um único lugar

Os apps Django ficam com zero templates. Apenas Python.

---

## Diagnóstico

### Números
| Problema | Quantidade |
|----------|-----------|
| Ocorrências de `#a98f71` hardcoded | **240** |
| Arquivos com cores hardcoded | **45** |
| Templates usando `.ui-btn` / `.badge` | **0 / 64** |
| Tags Django-específicas (`url`, `csrf`, `load`, `static`) | **~200** |

### Tags Django nos templates (auditoria)
| Tag | Ocorrências | Portável para Jinja2? |
|-----|-------------|----------------------|
| `{% url %}` | 135 | `{{ url('name') }}` — helper |
| `{% block %}`/`{% extends %}` | 106 | Idêntico em Jinja2 |
| `{% csrf_token %}` | 36 | `{{ csrf_input }}` — helper |
| `{% load static %}`/`{% static %}` | 26 | `{{ static('path') }}` — helper |
| `{% for %}`/`{% if %}`/`{% include %}` | 247+ | Idêntico em Jinja2 |
| `{% load permission_tags %}` | 5 | Tag customizada → helper Jinja2 |

### Dois artefatos desconexos atuais
| Artefato | Onde | Problema |
|----------|------|---------|
| `app.css` | `core/static/css/` | Define componentes, ninguém usa |
| `@theme {}` inline | `base.html` | Define tokens, templates ignoram |

---

## Princípio Arquitetural

O mesmo padrão já aplicado no backend — lógica de negócio em `modules/`, cola com Django em `app/` — agora aplicado ao frontend:

```
ANTES (acoplado):
  app/core/templates/base_dashboard.html  ← layout misturado com {% url %} {% load %}
  app/core/static/css/app.css             ← componentes que ninguém usa

DEPOIS (desacoplado):
  modules/design_system/templates/        ← Jinja2 puro, sem cola Django
  modules/design_system/static/css/       ← CSS/JS 100% framework-agnostic
  modules/design_system/adapters/django/  ← TODA a cola Django fica aqui
  app/{qualquer}/                         ← zero templates, só Python
```

---

## Estrutura Final

```
modules/design_system/
│
├── __init__.py
│
├── adapters/
│   └── django/
│       ├── __init__.py
│       ├── apps.py          ← DesignSystemConfig (INSTALLED_APPS)
│       └── jinja2_env.py    ← registra url(), static(), csrf_input, helpers de permissão
│
├── static/
│   └── design_system/
│       └── css/
│           ├── tokens.css      ← variáveis CSS puras (--brand-*, --color-*)
│           ├── components.css  ← .ui-btn, .badge, .modal, .kanban-*, .ui-input
│           └── layout.css      ← .app-container, .app-navbar, .app-footer
│
└── templates/
    └── design_system/
        │
        ├── base.html               ← base global (head, scripts, body wrapper)
        ├── base_dashboard.html     ← layout com sidebar + main
        ├── base_public.html        ← layout landing/login (dark luxury)
        │
        ├── components/             ← partials globais reutilizáveis
        │   ├── _alert.html         ← substitui {% if messages %} repetido
        │   ├── _page_header.html   ← título de página com breadcrumb
        │   └── _card.html          ← card container
        │
        └── apps/                   ← templates de cada app (todos aqui)
            │
            ├── atendimento_unificado/
            │   ├── workspace.html
            │   ├── workspace_disabled.html
            │   └── partials/
            │       ├── chat_message.html
            │       ├── kanban_card.html
            │       ├── kanban_column.html
            │       ├── conversation_item.html
            │       ├── chat_drawer.html
            │       ├── detail_panel.html
            │       └── custom_fields_panel.html
            │
            ├── tenants/
            │   ├── dashboard.html
            │   ├── config_database.html
            │   ├── config_evolution.html
            │   ├── config_ai.html
            │   ├── config_trello.html
            │   ├── config_debug.html
            │   ├── config_form.html
            │   ├── signup.html
            │   ├── subscription_expired.html
            │   ├── tenant_not_found.html
            │   ├── backoffice/
            │   ├── onboarding/
            │   └── users/
            │
            ├── evolution_sync/
            │   ├── instance_list.html
            │   └── instance_detail.html
            │
            ├── settings_manager/
            │   ├── index.html
            │   ├── whitelist.html
            │   ├── whitelist_form.html
            │   └── whitelist_confirm.html
            │
            ├── treinamento/
            │   └── *.html
            │
            └── usuarios/
                ├── login.html
                ├── cadastro.html
                └── password_reset_form.html

app/
  core/            → settings, middleware, context_processors, URLs — SEM templates
  atendimentos/    → models, views, signals — SEM templates
  tenants/         → models, views, forms, templatetags → helpers Jinja2
  evolution_sync/  → models, views, signals — SEM templates
  ...              → todos: zero templates
```

---

## Adaptador Django — `jinja2_env.py`

Toda a "cola" entre Jinja2 e Django fica aqui. É o único arquivo que muda se trocar o framework:

```python
# modules/design_system/adapters/django/jinja2_env.py
from jinja2 import Environment
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        # Equivalentes Django → Jinja2
        "url": reverse,
        "static": static,
        "csrf_input": _csrf_input,

        # Helpers de permissão (substitui permission_tags)
        "can_view_module": _can_view_module,
        "is_owner_user": _is_owner_user,
        "can_access_admin_panel": _can_access_admin_panel,
    })
    return env


def _csrf_input(request):
    token = request.META.get("CSRF_COOKIE", "")
    return mark_safe(f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">')


def _can_view_module(user, module_name: str) -> bool:
    # Lógica extraída de permission_tags
    ...
```

**Configuração no `settings.py`:**

```python
TEMPLATES = [
    # Jinja2 — processa design_system/templates/ e {app}/templates/ via APP_DIRS
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "smart_core_assistant_painel.modules.design_system.adapters.django.jinja2_env.environment",
        },
    },
    # DTL — mantido apenas para Admin Django (Jazzmin usa DTL)
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [...],
        },
    },
]
```

> O Admin (Jazzmin) usa DTL — mantemos o backend DTL **somente** para ele. Todas as views da aplicação usam Jinja2.

---

## Conversão DTL → Jinja2 (mapeamento completo)

### Tags que mudam

| DTL | Jinja2 |
|-----|--------|
| `{% url 'name' %}` | `{{ url('name') }}` |
| `{% url 'name' arg %}` | `{{ url('name', args=[arg]) }}` |
| `{% static 'path' %}` | `{{ static('path') }}` |
| `{% csrf_token %}` | `{{ csrf_input(request) }}` |
| `{% load static %}` | Remove (não existe em Jinja2) |
| `{% load permission_tags %}` | Remove (helpers no env) |
| `{% load i18n %}` | Remove (configurar i18n no env) |
| `{% trans "texto" %}` | `{{ _("texto") }}` |
| `{% now "Y" %}` | `{{ now().year }}` |
| `{% with x=y %}` | `{% set x = y %}` |
| `{% can_view_module "x" as var %}` | `{% set var = can_view_module(user, "x") %}` |

### Tags que ficam iguais

| Tag | Status |
|-----|--------|
| `{% block %}` / `{% endblock %}` | Idêntico |
| `{% extends "..." %}` | Idêntico |
| `{% include "..." %}` | Idêntico |
| `{% for x in y %}` | Idêntico |
| `{% if %}` / `{% elif %}` / `{% else %}` | Idêntico |
| `{{ variavel }}` | Idêntico |
| `{{ variavel\|filter }}` | Idêntico (maioria dos filtros) |

### Filtros que mudam

| DTL | Jinja2 |
|-----|--------|
| `\|truncatechars:N` | `\|truncate(N)` |
| `\|default:"x"` | `\|default("x")` |
| `\|date:"d/m/Y"` | `\|strftime("%d/%m/%Y")` |
| `\|slice:":2"` | `[:2]` (Python nativo) |
| `\|upper` | `\|upper` (idêntico) |
| `\|length` | `\|length` (idêntico) |

---

## Portabilidade no futuro

Se migrar para FastAPI, o trabalho se resume a:

1. **CSS/JS** → zero mudanças
2. **Templates Jinja2** → zero mudanças  
3. **`jinja2_env.py`** → escrever `adapters/fastapi/jinja2_env.py` com:
   - `url` → função de URL do FastAPI
   - `static` → montagem de static do Starlette
   - `csrf_input` → dependência do FastAPI
4. **Views Django** → reescrever como rotas FastAPI (lógica de negócio nos `modules/` reaproveitada)
5. **Models Django ORM** → adaptar para SQLAlchemy ou Tortoise ORM

O frontend (templates + CSS/JS) fica intacto. A lógica de negócio (`modules/`) fica intacta.

---

## Requisitos Funcionais

### RF-001: Criar `modules/design_system/` com adaptador Django
**Prioridade:** Alta — bloqueante
**Critérios de Aceite:**
- [ ] `modules/design_system/adapters/django/apps.py` com `DesignSystemConfig`
- [ ] `modules/design_system/adapters/django/jinja2_env.py` com `url`, `static`, `csrf_input`, helpers de permissão
- [ ] `"smart_core_assistant_painel.modules.design_system.adapters.django"` em `INSTALLED_APPS`
- [ ] `settings.py` com backend Jinja2 configurado apontando para `jinja2_env.environment`
- [ ] Backend DTL mantido para Admin/Jazzmin

### RF-002: CSS Desacoplado em `design_system/static/`
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] `tokens.css` com variáveis CSS puras (`--brand-*`)
- [ ] `components.css` com todos os componentes (`.ui-btn`, `.badge`, `.modal`, `.kanban-*`, `.ui-input`)
- [ ] `layout.css` com layout global (`.app-container`, `.app-navbar`, `.app-footer`)
- [ ] Zero hex hardcoded nesses arquivos
- [ ] `core/static/css/app.css` removido

### RF-003: Templates Base em Jinja2
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] `design_system/templates/design_system/base.html` em Jinja2
- [ ] `design_system/templates/design_system/base_dashboard.html` em Jinja2 com tokens de cor
- [ ] `design_system/templates/design_system/base_public.html` em Jinja2
- [ ] `base.html` carrega os CSS via `{{ static('design_system/css/tokens.css') }}`
- [ ] `@theme` do Tailwind v4 mantido inline (limitação do CDN browser)

### RF-004: Migrar Todos os Templates para `design_system/templates/design_system/apps/`
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] Todos os 64 templates migrados para `design_system/templates/design_system/apps/{app}/`
- [ ] Todos convertidos de DTL para Jinja2
- [ ] Zero cores hardcoded (`#a98f71`, `#8b7355`, `#1c1917`)
- [ ] Apps Django com zero arquivos `.html`

### RF-005: Helpers de Permissão no Ambiente Jinja2
**Prioridade:** Alta (bloqueante para migração de templates com permissões)
**Critérios de Aceite:**
- [ ] `can_view_module(user, module)` disponível nos templates Jinja2
- [ ] `is_owner_user(user)` disponível
- [ ] `can_access_admin_panel(user)` disponível
- [ ] `has_no_module_permissions(user)` disponível
- [ ] `has_any_module_permission(user)` disponível

### RF-006: Componentes Globais (Partials)
**Prioridade:** Média
**Critérios de Aceite:**
- [ ] `components/_alert.html` substitui `{% if messages %}` repetido
- [ ] `components/_page_header.html` reutilizado em ≥ 5 templates
- [ ] `components/_card.html` reutilizado em ≥ 3 templates

---

## Requisitos Não-Funcionais

### RNF-001: Zero Regressão Visual
Substituição 1:1 de cores. Nenhuma mudança perceptível ao usuário.

### RNF-002: Sem Build Step
Tailwind v4 CDN mantido. Sem npm, node_modules ou Vite.

### RNF-003: Admin Django intacto
Jazzmin/Admin continuam funcionando via backend DTL. Nenhuma mudança.

### RNF-004: Portabilidade Futura
Template layer ≥ 90% portável para FastAPI via troca do `jinja2_env.py`.

---

## Plano de Execução por Fases

### Fase 1 — Infraestrutura do Módulo *(bloqueante)*
**Arquivos criados:**
- `modules/design_system/__init__.py`
- `modules/design_system/adapters/__init__.py`
- `modules/design_system/adapters/django/__init__.py`
- `modules/design_system/adapters/django/apps.py`
- `modules/design_system/adapters/django/jinja2_env.py`
- `modules/design_system/static/design_system/css/tokens.css`
- `modules/design_system/static/design_system/css/components.css`
- `modules/design_system/static/design_system/css/layout.css`

**Arquivos modificados:**
- `settings.py` — adicionar `INSTALLED_APPS` + backend Jinja2

**Resultado:** Módulo registrado, CSS criado, Jinja2 configurado. Nenhum template migrado.

---

### Fase 2 — Templates Base em Jinja2 *(bloqueante)*
**Arquivos criados:**
- `design_system/templates/design_system/base.html`
- `design_system/templates/design_system/base_dashboard.html`
- `design_system/templates/design_system/base_public.html`
- `design_system/templates/design_system/components/_alert.html`
- `design_system/templates/design_system/components/_page_header.html`
- `design_system/templates/design_system/components/_card.html`

**Conversões principais em `base_dashboard.html`:**
- `{% load static %}` → remove
- `{% static 'css/app.css' %}` → `{{ static('design_system/css/tokens.css') }}`
- `bg-[#a98f71]` → `bg-gold-primary` (~60 ocorrências)
- `bg-[#1c1917]` → `bg-sidebar`

---

### Fase 3 — `atendimento_unificado` (referência)
**Arquivos criados:**
- `design_system/templates/design_system/apps/atendimento_unificado/workspace.html`
- `design_system/templates/design_system/apps/atendimento_unificado/workspace_disabled.html`
- `design_system/templates/design_system/apps/atendimento_unificado/partials/*.html` (7 partials)

**Arquivos removidos:**
- `app/atendimento_unificado/templates/` (inteiro)

**Conversões:**
- `{% extends "base_dashboard.html" %}` → `{% extends "design_system/base_dashboard.html" %}`
- `{% load static %}` → remove
- `{% static '...' %}` → `{{ static('...') }}`
- Cores hardcoded → tokens Tailwind
- Sintaxe Jinja2 para `{% with %}`, filtros, etc.

**Views devem passar `request` no contexto** (necessário para `csrf_input(request)` no Jinja2).

---

### Fase 4 — `tenants` (maior volume de templates)
**~10 templates** migrados para `design_system/templates/design_system/apps/tenants/`

**Atenção especial:**
- `permission_tags` (`can_view_module`, `is_owner_user`) → helpers Jinja2 do env
- Forms Django → `{{ form.as_p() }}` (Jinja2 chama métodos com `()`)

---

### Fase 5 — `evolution_sync`, `settings_manager`, `treinamento`, `usuarios`
**~20 templates** migrados para `design_system/templates/design_system/apps/{app}/`

---

### Fase 6 — Limpeza
1. Remover todas as pastas `{app}/templates/` (migradas)
2. Remover `core/static/css/app.css`
3. Remover `TEMPLATES DIRS` do DTL backend (manter só para Admin)
4. `core/` vira app Django puro: settings, middleware, URLs, context_processors

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| `@theme` Tailwind v4 não funcionar em arquivo CSS externo | Alta | Alto | Manter `@theme` inline no `base.html`; `tokens.css` exporta apenas `var()` CSS puras |
| Forms Django renderizados diferente no Jinja2 | Média | Médio | Jinja2 chama métodos com `()` — `form.as_p()` em vez de `form.as_p` |
| `permission_tags` com lógica complexa difícil de extrair | Média | Médio | Extrair lógica das tags para funções Python puras antes de migrar |
| Admin (Jazzmin) quebrar com backend Jinja2 | Baixa | Alto | Django suporta múltiplos backends de template. DTL fica exclusivo para Admin |
| Views não passando `request` no contexto (necessário pro csrf_input) | Média | Médio | Django Jinja2 backend injeta `request` automaticamente via context_processors |

---

## Métricas de Sucesso

- [ ] `grep -r "#a98f71" src/ --include="*.html"` → **0**
- [ ] `grep -rn "{% load" src/smart_core_assistant_painel/app --include="*.html"` → **0**
- [ ] `find src/smart_core_assistant_painel/app -name "*.html"` → **0 arquivos**
- [ ] `find src/smart_core_assistant_painel/modules/design_system/templates -name "*.html" | wc -l` → **~64**
- [ ] Admin Django funcionando normalmente
- [ ] `grep -rn "ui-btn\|badge\|ui-input" src/ --include="*.html"` → **≥ 30**

---

## Timeline

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Infraestrutura do módulo (apps.py, jinja2_env.py, CSS) | Pendente |
| 2 | Templates base em Jinja2 (base, dashboard, public, components) | Pendente |
| 3 | `atendimento_unificado` — referência completa | Pendente |
| 4 | `tenants` — maior volume | Pendente |
| 5 | `evolution_sync`, `settings_manager`, `treinamento`, `usuarios` | Pendente |
| 6 | Limpeza geral | Pendente |

---

## Aprovações

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | pwlimaverde | 2026-05-24 | Pendente |
| Tech Lead | — | — | Pendente |
