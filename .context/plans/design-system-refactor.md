# PRD — Design System Desacoplado

## Objetivo

Centralizar **tudo que é design** em `modules/design_system/` com o mínimo de acoplamento
possível ao Django. Os apps Django ficam com zero templates e zero CSS — apenas Python.

---

## Princípio Central

O mesmo padrão já usado no backend — lógica de negócio em `modules/`, cola com Django em
`app/` — aplicado ao frontend:

```
HOJE                              DEPOIS
──────────────────────────────    ──────────────────────────────────────────
app/core/templates/base.html  →  modules/design_system/templates/ (Jinja2)
app/core/static/css/app.css   →  modules/design_system/static/css/
app/*/templates/**/*.html     →  modules/design_system/templates/apps/*/
app/*/static/**/css/          →  removidas
──────────────────────────────    ──────────────────────────────────────────
Todo acoplamento com Django   →  modules/design_system/adapters/django/
```

---

## As Três Camadas do Design System

A pesquisa de melhores práticas (2026) deixa claro que "design" são três camadas separadas,
cada uma com sua estratégia:

### Camada 1 — Tokens (100% portável)

**Melhor prática da indústria:** W3C Design Tokens — especificação estabilizada em outubro
de 2025, padrão agnóstico de plataforma.

Os tokens são definidos **uma vez** em JSON neutro. O CSS os consome como variáveis puras.
Se o projeto migrar para qualquer outro stack (FastAPI, Node, app mobile), o `tokens.json`
vai junto sem mudança.

**Sem build step:** o `tokens.css` é mantido manualmente em sincronia com `tokens.json`.
Se futuramente precisar gerar iOS/Android, a adição do Style Dictionary não exige alterar
os arquivos existentes — é aditivo.

### Camada 2 — Componentes CSS (100% portável)

Classes utilitárias CSS puras (`.ui-btn`, `.badge`, `.modal`). Usam as variáveis CSS dos
tokens. Funcionam em qualquer framework ou HTML puro — zero acoplamento.

### Camada 3 — Templates (90% portável)

**Melhor prática para SSR:** Jinja2. Suportado nativamente por Django **e** FastAPI.
A sintaxe (`{% block %}`, `{% extends %}`, `{% for %}`, `{% if %}`) é idêntica nos dois.
O único código Django-específico (`url()`, `static()`, `csrf_input`) fica isolado em um
único arquivo adaptador.

---

## Estrutura Final

```
modules/
└── design_system/
    │
    ├── tokens/
    │   └── tokens.json                   ← W3C Design Tokens (fonte única da verdade)
    │
    ├── static/
    │   └── design_system/
    │       └── css/
    │           ├── tokens.css            ← variáveis CSS geradas do tokens.json
    │           ├── components.css        ← .ui-btn, .badge, .modal, .kanban-*
    │           └── layout.css            ← .app-container, .app-navbar, .app-footer
    │
    ├── templates/
    │   └── design_system/
    │       │
    │       ├── base.html                 ← base global (head, CDN scripts, body)
    │       ├── base_dashboard.html       ← layout com sidebar + main
    │       ├── base_public.html          ← layout landing / login (dark)
    │       │
    │       ├── components/               ← partials globais reutilizáveis
    │       │   ├── _alert.html
    │       │   ├── _page_header.html
    │       │   └── _card.html
    │       │
    │       └── apps/                     ← TODOS os templates de todos os apps
    │           ├── atendimento_unificado/
    │           │   ├── workspace.html
    │           │   ├── workspace_disabled.html
    │           │   └── partials/
    │           │       ├── chat_message.html
    │           │       ├── kanban_card.html
    │           │       ├── kanban_column.html
    │           │       ├── conversation_item.html
    │           │       ├── chat_drawer.html
    │           │       ├── detail_panel.html
    │           │       └── custom_fields_panel.html
    │           ├── tenants/
    │           │   ├── dashboard.html
    │           │   ├── config_database.html
    │           │   ├── config_evolution.html
    │           │   ├── config_ai.html
    │           │   ├── config_trello.html
    │           │   ├── config_debug.html
    │           │   ├── config_form.html
    │           │   ├── signup.html
    │           │   ├── subscription_expired.html
    │           │   ├── tenant_not_found.html
    │           │   ├── backoffice/
    │           │   ├── onboarding/
    │           │   └── users/
    │           ├── evolution_sync/
    │           │   ├── instance_list.html
    │           │   └── instance_detail.html
    │           ├── settings_manager/
    │           │   ├── index.html
    │           │   ├── whitelist.html
    │           │   ├── whitelist_form.html
    │           │   └── whitelist_confirm.html
    │           ├── treinamento/
    │           │   └── *.html
    │           └── usuarios/
    │               ├── login.html
    │               ├── cadastro.html
    │               └── password_reset_form.html
    │
    └── adapters/
        └── django/
            ├── __init__.py
            ├── apps.py                   ← DesignSystemConfig (INSTALLED_APPS)
            └── jinja2_env.py             ← ÚNICO arquivo com código Django

app/
  core/            → settings, middleware, context_processors, URLs — zero templates
  atendimentos/    → models, views, signals — zero templates
  tenants/         → models, views, forms — zero templates
  evolution_sync/  → models, views, signals — zero templates
  ...              → todos: zero templates, zero CSS
```

---

## Tokens W3C — Arquivo `tokens.json`

Fonte única de verdade. Formato estável W3C (2025.10):

```json
{
  "$schema": "https://design-tokens.org/schema",
  "brand": {
    "gold": {
      "primary": { "$value": "#a98f71", "$type": "color" },
      "dark":    { "$value": "#8b7355", "$type": "color" }
    },
    "sidebar": { "$value": "#1c1917", "$type": "color" }
  },
  "semantic": {
    "primary": { "$value": "#3b82f6", "$type": "color" },
    "success": { "$value": "#22c55e", "$type": "color" },
    "warning": { "$value": "#f59e0b", "$type": "color" },
    "danger":  { "$value": "#ef4444", "$type": "color" }
  },
  "surface": {
    "card":    { "$value": "#ffffff", "$type": "color" },
    "page":    { "$value": "#f8fafc", "$type": "color" },
    "border":  { "$value": "#e2e8f0", "$type": "color" }
  },
  "typography": {
    "fontFamily": { "$value": "'Outfit', sans-serif", "$type": "fontFamily" }
  },
  "radius": {
    "lg": { "$value": "14px", "$type": "dimension" },
    "md": { "$value": "10px", "$type": "dimension" }
  }
}
```

---

## CSS — Derivado dos Tokens

### `tokens.css` — variáveis CSS (tradução direta do `tokens.json`)

```css
:root {
  /* Marca */
  --color-gold-primary: #a98f71;
  --color-gold-dark:    #8b7355;
  --color-sidebar:      #1c1917;

  /* Semântica */
  --color-primary: #3b82f6;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-danger:  #ef4444;

  /* Superfícies */
  --color-surface-card:   #ffffff;
  --color-surface-page:   #f8fafc;
  --color-border-default: #e2e8f0;

  /* Tipografia */
  --font-sans: 'Outfit', sans-serif;

  /* Raios */
  --radius-lg: 14px;
  --radius-md: 10px;
}
```

### Tailwind v4 `@theme` — registra tokens como classes Tailwind

Inline no `base.html` (limitação do CDN browser — não pode ser arquivo externo):

```html
<style type="text/tailwindcss">
  @theme {
    --color-gold-primary: var(--color-gold-primary);
    --color-gold-dark:    var(--color-gold-dark);
    --color-sidebar:      var(--color-sidebar);
    --font-family-sans:   var(--font-sans);
    --radius-lg:          var(--radius-lg);
    --radius-md:          var(--radius-md);
  }
</style>
```

Isso habilita `bg-gold-primary`, `text-gold-primary`, `bg-sidebar` nos templates.

---

## Adaptador Django — `jinja2_env.py`

**Todo o código Django-específico fica aqui. É o único arquivo que muda se trocar o framework:**

```python
# modules/design_system/adapters/django/jinja2_env.py
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from jinja2 import Environment


def environment(**options) -> Environment:
    env = Environment(**options)
    env.globals.update({
        # Equivalentes Django → portável para FastAPI trocando só este arquivo
        "url":        reverse,
        "static":     static,
        "csrf_input": _csrf_input,

        # Helpers de permissão (substitui permission_tags)
        "can_view_module":         _can_view_module,
        "is_owner_user":           _is_owner_user,
        "can_access_admin_panel":  _can_access_admin_panel,
        "has_no_module_permissions": _has_no_module_permissions,
        "has_any_module_permission": _has_any_module_permission,
    })
    return env
```

---

## Conversão DTL → Jinja2

### Tags que mudam (as únicas que exigem trabalho)

| Django Template Language | Jinja2 |
|--------------------------|--------|
| `{% url 'name' %}` | `{{ url('name') }}` |
| `{% url 'name' arg %}` | `{{ url('name', args=[arg]) }}` |
| `{% static 'path' %}` | `{{ static('path') }}` |
| `{% csrf_token %}` | `{{ csrf_input(request) }}` |
| `{% load static %}` | Remove (não existe em Jinja2) |
| `{% load permission_tags %}` | Remove (helpers no env) |
| `{% load i18n %}` | Remove (i18n configurado no env) |
| `{% trans "texto" %}` | `{{ _("texto") }}` |
| `{% now "Y" %}` | `{{ now().year }}` |
| `{% with x=y %}...{% endwith %}` | `{% set x = y %}` |
| `{% can_view_module "x" as var %}` | `{% set var = can_view_module(user, "x") %}` |
| `form.as_p` | `form.as_p()` (Jinja2 chama métodos com `()`) |

### Tags que ficam idênticas (maioria)

`{% block %}`, `{% extends %}`, `{% include %}`, `{% for %}`, `{% if %}`, `{% elif %}`,
`{% else %}`, `{{ variavel }}`, `{{ variavel|filter }}`, `{% macro %}`.

---

## Configuração Django (`settings.py`)

```python
TEMPLATES = [
    # Jinja2 — processa todos os templates da aplicação
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,  # descobre design_system/templates/ via INSTALLED_APPS
        "OPTIONS": {
            "environment": (
                "smart_core_assistant_painel"
                ".modules.design_system.adapters.django.jinja2_env.environment"
            ),
        },
    },
    # DTL — mantido SOMENTE para o Admin Django (Jazzmin usa DTL)
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [...]},
    },
]

INSTALLED_APPS = [
    ...
    # Design system registrado — Django descobre static/ e templates/ automaticamente
    "smart_core_assistant_painel.modules.design_system.adapters.django",
    ...
]
```

---

## Portabilidade Futura

| O que | Mudança ao trocar Django → FastAPI |
|-------|-------------------------------------|
| `tokens.json` | **Nada** — JSON neutro |
| `tokens.css`, `components.css`, `layout.css` | **Nada** — CSS puro |
| Templates Jinja2 | **Nada** — Jinja2 é o mesmo |
| `jinja2_env.py` (adaptador Django) | **Troca por** `adapters/fastapi/jinja2_env.py` |
| Business logic (`modules/`) | **Nada** — Python puro |
| Views Django | Reescreve como rotas FastAPI |
| Django ORM | Adapta para SQLAlchemy |

O frontend completo (tokens, CSS, templates) sobrevive à migração intacto.

---

## Plano de Execução — 6 Fases

### Fase 1 — Infraestrutura do Módulo *(bloqueante para tudo)*

**Criar a estrutura vazia do módulo:**
- `modules/design_system/__init__.py`
- `modules/design_system/tokens/tokens.json` — todos os tokens da marca
- `modules/design_system/static/design_system/css/tokens.css` — CSS vars do tokens.json
- `modules/design_system/static/design_system/css/components.css` — extraído do app.css
- `modules/design_system/static/design_system/css/layout.css` — layout do app.css
- `modules/design_system/adapters/__init__.py`
- `modules/design_system/adapters/django/__init__.py`
- `modules/design_system/adapters/django/apps.py` — DesignSystemConfig
- `modules/design_system/adapters/django/jinja2_env.py` — todos os helpers

**Modificar:**
- `settings.py` — adicionar `INSTALLED_APPS` + backend Jinja2

**Verificar:** Admin Django continua funcionando (DTL isolado).

---

### Fase 2 — Templates Base em Jinja2 *(bloqueante para as demais fases)*

**Criar:**
- `templates/design_system/base.html` — head, CDN, @theme Tailwind inline
- `templates/design_system/base_dashboard.html` — sidebar + main (zero hex hardcoded)
- `templates/design_system/base_public.html` — layout dark (landing, login)
- `templates/design_system/components/_alert.html`
- `templates/design_system/components/_page_header.html`
- `templates/design_system/components/_card.html`

**Substituições em `base_dashboard.html`:**
- ~60 ocorrências de `bg-[#a98f71]` → `bg-gold-primary`
- `bg-[#1c1917]` → `bg-sidebar`
- Todas as tags DTL → Jinja2

---

### Fase 3 — `atendimento_unificado` (referência)

O workspace é o template mais complexo. Resolvê-lo valida toda a arquitetura.

**Criar** `templates/design_system/apps/atendimento_unificado/`:
- `workspace.html` + `workspace_disabled.html`
- `partials/` — 7 partials (chat_message, kanban_card, kanban_column, conversation_item,
  chat_drawer, detail_panel, custom_fields_panel)

**Remover:** `app/atendimento_unificado/templates/` (inteiro)

**Conversões específicas:**
- Bolhas de chat usarão classes de `components.css` (`.chat-bubble-in`, `.chat-bubble-out`)
  em vez de classes Tailwind compostas repetidas
- `{% load static %}` → remove
- `{% static '...' %}` → `{{ static('...') }}`

---

### Fase 4 — `tenants` (maior volume)

**Criar** `templates/design_system/apps/tenants/` com todos os ~15 templates.

**Atenção especial:**
- `permission_tags` customizadas (`can_view_module`, `is_owner_user`) →
  já disponíveis como helpers no `jinja2_env.py`
- Forms Django: `form.as_p` → `form.as_p()`

**Remover:** `app/tenants/templates/`

---

### Fase 5 — Apps restantes

**Migrar** para `templates/design_system/apps/{app}/`:
- `evolution_sync/` — 2 templates
- `settings_manager/` — 4 templates
- `treinamento/` — 5 templates
- `usuarios/` — 3 templates (login, cadastro, password_reset)

**Remover** as pastas `templates/` de cada app.

---

### Fase 6 — Limpeza

1. Remover `app/core/static/css/app.css` (conteúdo migrado para o design_system)
2. Remover templates migrados de `app/core/templates/`
   - Manter apenas `404.html`, `500.html`, `403.html` (erros Django, DTL, não migram)
3. Atualizar `settings.py`: remover `TEMPLATES DIRS` do DTL (só mantém `core/templates`
   para as páginas de erro)
4. `app/core/` vira app Django puro: settings, middleware, URLs, context_processors

---

## Métricas de Sucesso

```bash
# Zero cores hardcoded nos templates
grep -r "#a98f71\|#8b7355\|#8c735a\|#1c1917" src/ --include="*.html"
# → 0 resultados

# Zero tags DTL nos templates de aplicação
grep -rn "{% load " src/smart_core_assistant_painel/modules/design_system/templates/
# → 0 resultados

# Zero templates nos apps Django
find src/smart_core_assistant_painel/app -name "*.html" | grep -v "core/templates"
# → 0 resultados (apenas 404/500/403 no core ficam)

# Todos os templates vivem no design_system
find src/smart_core_assistant_painel/modules/design_system/templates -name "*.html" | wc -l
# → ~65 arquivos

# Adoção real das classes de componentes
grep -rn "ui-btn\|badge\|ui-input\|chat-bubble" \
  src/smart_core_assistant_painel/modules/design_system/templates/
# → ≥ 50 ocorrências
```

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Tailwind v4 `@theme` não funcionar em CSS externo | Alta | Alto | `@theme` mantido inline no `base.html`; `tokens.css` exporta só variáveis CSS puras |
| Admin Django (Jazzmin) quebrar | Baixa | Alto | Backend DTL mantido exclusivamente para o Admin; Jinja2 só nas views da aplicação |
| Forms Django renderizados diferente em Jinja2 | Média | Médio | Jinja2 chama métodos com `()` — `form.as_p()`, `form.as_table()` |
| `permission_tags` com lógica complexa | Média | Médio | Extrair funções Python puras antes de migrar; testar helpers no `jinja2_env.py` |
| Regressão visual durante migração de cores | Média | Baixo | Mapeamento 1:1 rigoroso (tabela de substituição); revisar visualmente por fase |

---

## Timeline

| Fase | Descrição | Arquivos | Status |
|------|-----------|----------|--------|
| 1 | Infraestrutura do módulo (tokens.json, CSS, jinja2_env.py) | ~8 novos | Pendente |
| 2 | Templates base em Jinja2 (base, dashboard, public, partials globais) | ~6 novos | Pendente |
| 3 | `atendimento_unificado` — 9 templates (referência completa) | ~9 novos | Pendente |
| 4 | `tenants` — ~15 templates | ~15 novos | Pendente |
| 5 | `evolution_sync`, `settings_manager`, `treinamento`, `usuarios` — ~14 templates | ~14 novos | Pendente |
| 6 | Limpeza (`core/`, remoção de templates dos apps) | ~60 removidos | Pendente |

---

## Aprovações

| Papel | Data | Status |
|-------|------|--------|
| Product Owner (pwlimaverde) | 2026-05-24 | Pendente |
