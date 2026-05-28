# Documentação Auxiliar — Design System Desacoplado

> Gerado em: 2026-05-26
> Plano canônico: `.context/plans/design-system-refactor.md`
> Plano completo: `.context/plans/design-system-refactor/plano_completo_design-system-refactor.md`

## Libs Python

### Django (5.2.7)

#### Backend Jinja2 — Configuração TEMPLATES

**Sintaxe ATUAL (Django 5.2):**

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": ["/caminho/para/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "meuapp.jinja2.environment",
            "context_processors": [ ... ],
        },
    },
]
```

**Comportamento `APP_DIRS` com Jinja2:**
- Com `APP_DIRS=True`, o backend Jinja2 procura templates em `<app>/jinja2/` (NÃO em `<app>/templates/`).
- Isso é diferente do backend DTL que procura em `<app>/templates/`.
- **Importante para o plano:** Como o projeto usa `DIRS` explícito apontando para `modules/design_system/templates/`, e NÃO depende de `APP_DIRS` para os templates do design system, o `APP_DIRS=True` no Jinja2 pode causar conflito se houver pastas `jinja2/` inesperadas em apps instalados.

**Coexistência DTL + Jinja2:**
- Django suporta múltiplos backends simultâneos.
- O Django tenta cada backend na ORDEM listada em `TEMPLATES`.
- Para o Admin (Jazzmin), o backend DTL DEVE permanecer ativo.
- O backend Jinja2 deve ficar PRIMEIRO na lista para ter prioridade.

**Context Processors no Jinja2:**
- Django 5.2 suporta `context_processors` no backend Jinja2 via `OPTIONS`.
- Porém, context processors do Django (como `django.template.context_processors.request`) funcionam apenas quando o template é renderizado com `RequestContext` ou via `render()`.

**Estado atual no projeto:** ✅ Já configurado corretamente em `settings.py` (linhas 218-258).

#### Funções do Jinja2 Environment

**Assinaturas atuais dos helpers registrados em `jinja2_env.py`:**

```python
from jinja2 import Environment, pass_context

# Reverso de URLs do Django
from django.urls import reverse
# Uso: {{ url('nome_da_view') }} ou {{ url('nome', args=[arg1]) }}

# Arquivos estáticos
from django.templatetags.static import static
# Uso: {{ static('css/core.build.css') }}

# CSRF Token
from django.middleware.csrf import get_token
# Uso: {{ csrf_input(request) }}  → <input type="hidden" ...>

# Timezone
from django.utils import timezone
# Uso: {{ now() }} → datetime atual
```

**Nota:** O `pass_context` do Jinja2 é usado para decorar funções que precisam acessar o contexto do template (ex: `can_view_module`, `is_owner_user`).

### Jinja2 (via django.template.backends.jinja2)

**Versão:** Empacotada como dependência transitiva do Django.

**Sintaxe vs DTL — Referência de Migração:**

| Django Template Language | Jinja2 |
|--------------------------|--------|
| `{% url 'name' %}` | `{{ url('name') }}` |
| `{% url 'name' arg %}` | `{{ url('name', args=[arg]) }}` |
| `{% static 'path' %}` | `{{ static('path') }}` |
| `{% csrf_token %}` | `{{ csrf_input(request) }}` |
| `{% load static %}` | Remover (desnecessário) |
| `{% load permission_tags %}` | Remover (helpers no env global) |
| `{% load i18n %}` | Remover (helpers no env global) |
| `{% trans "texto" %}` | `{{ _("texto") }}` |
| `{% now "Y" %}` | `{{ now().year }}` |
| `{% with x=y %}...{% endwith %}` | `{% set x = y %}` |
| `form.as_p` | `form.as_p()` (chamar como função) |
| `{{ var\|default:"val" }}` | `{{ var\|default("val") }}` |
| `{% include "template.html" %}` | `{% include "template.html" %}` (igual) |
| `{% extends "base.html" %}` | `{% extends "base.html" %}` (igual) |
| `{% block content %}...{% endblock %}` | `{% block content %}...{% endblock %}` (igual) |
| `{% if var %}` | `{% if var %}` (igual) |
| `{% for item in list %}` | `{% for item in list %}` (igual) |
| `{{ var\|date:"d/m/Y" }}` | `{{ var.strftime("%d/%m/%Y") }}` |
| `{{ var\|truncatechars:50 }}` | `{{ var[:50] }}` ou filtro custom |
| `{{ var\|floatformat:2 }}` | `{{ "%.2f"\|format(var) }}` |
| `{% empty %}` (dentro de for) | `{% else %}` (dentro de for) |

**Diferenças críticas:**
1. Jinja2 **não suporta** `{% load %}` — filtros e tags são registrados no `Environment`.
2. Jinja2 usa **parênteses** para chamadas: `{{ func() }}` vs DTL `{{ func }}`.
3. Jinja2 permite **expressões Python** mais complexas inline.
4. `{% set %}` substitui `{% with %}`.
5. Acesso a dicionário: `dict['key']` ou `dict.key` (ambos funcionam no Jinja2).

### Tailwind CSS v4 (via pytailwindcss)

**Versão no projeto:** `pytailwindcss>=0.3.0` (dependência dev)

**Mudanças críticas do v4:**

1. **Configuração CSS-first:** Não usa mais `tailwind.config.js`. Toda configuração fica no CSS.
2. **Import simplificado:** `@import "tailwindcss"` substitui `@tailwind base/components/utilities`.
3. **`@theme` directive:** Define variáveis de design como CSS custom properties:

```css
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --font-display: "Satoshi", sans-serif;
  --breakpoint-3xl: 120rem;
}
```

4. **`@source` directive:** Define caminhos para scan de classes:

```css
@source "../../../../app";
@source "../../../../modules";
```

5. **Geração automática de utilitárias:** O Tailwind v4 gera classes como `text-primary`, `bg-primary` automaticamente a partir de variáveis `--color-*` definidas em `@theme`.

**Estado atual no projeto:** ✅ Já configurado em `core.css` com `@import "tailwindcss"`, `@theme`, e `@source`.

**Build command:**
```bash
uv run task build-css   # Gera core.build.css purgado
uv run task watch-css   # Watch mode para desenvolvimento
```

**Nota sobre pytailwindcss:** O wrapper `pytailwindcss` pode não estar otimizado para v4. Se necessário, usar diretamente o binário standalone do Tailwind CLI como alternativa.

### W3C Design Tokens (2025.10)

**Versão da especificação:** 2025.10 (primeira versão estável)

**Formato:** JSON puro com tipos definidos via `$type` e valores via `$value`.

**Schema do projeto (`tokens.json`):**
```json
{
  "$schema": "https://design-tokens.org/schema",
  "grupo": {
    "token": { "$value": "#hexcolor", "$type": "color" }
  }
}
```

**Tipos suportados:**
- `color` — cores em qualquer formato CSS (hex, rgba, oklch)
- `dimension` — tamanhos (px, rem, em)
- `fontFamily`, `fontWeight`, `duration`, `cubicBezier`

**Referências entre tokens:**
```json
"accent": { "$value": "{brand.gold.primary}", "$type": "color" }
```

**Estado atual no projeto:** ✅ Implementado em `tokens.json` com 4 grupos (brand, semantic, chat, radius, layout) e consumido por `tokens.css`.

## Notas Gerais

### Compatibilidade pytailwindcss + Tailwind v4
- O `pytailwindcss>=0.3.0` atua como wrapper para o binário standalone do Tailwind.
- A task `build-css` no `pyproject.toml` já está configurada corretamente.
- Caso `pytailwindcss` apresente incompatibilidade, baixar o binário diretamente de https://github.com/tailwindlabs/tailwindcss/releases.

### Ordem de resolução de templates Django
1. Django tenta o PRIMEIRO backend em TEMPLATES.
2. Para cada backend, verifica `DIRS` primeiro, depois `APP_DIRS`.
3. O Jinja2 está primeiro → templates no design_system são encontrados por ele.
4. O DTL está segundo → captura o Admin e templates antigos dos apps.
5. **Risco na migração:** Se um template migrado para Jinja2 e um antigo DTL coexistirem com o mesmo nome, o Jinja2 tem prioridade. Isso pode causar erros se o template Jinja2 não estiver pronto.

### Components DTL já migrados para Jinja2 (no design_system)
Os seguintes componentes JÁ estão em Jinja2 (sem `{% load %}`):
- `avatar.html`, `badge.html`, `button.html`, `drawer_base.html`
- `empty_state.html`, `input_text.html`, `modal_base.html`
- `spinner.html`, `toast.html`

### Templates base já migrados para Jinja2
- `base.html` ✅ (usa `{{ static_versioned(...) }}`, `{% block %}`)
- `base_dashboard.html` ✅
- `base_public.html` ✅

### Templates ainda em DTL nos apps (74 arquivos)
Distribuição por app:
- `core/`: 9 arquivos (base*.html, dashboard, home, landing, erros, admin overrides)
- `tenants/`: 21 arquivos (dashboard, configs, onboarding, backoffice, users)
- `atendimento_unificado/`: 4 arquivos (workspace, base_workspace, partials)
- `chat_evolution/`: 7 arquivos (partials do chat)
- `gestao_kanban/`: 7 arquivos (partials do kanban)
- `evolution_sync/`: 2 arquivos (instance_list, instance_detail)
- `settings_manager/`: 4 arquivos (configurações, whitelist)
- `treinamento/`: 6 arquivos (treinamento de IA)
- `usuarios/`: 7 arquivos (login, cadastro, password_reset)
- `admin/`: 2 arquivos (overrides DTL — NÃO migrar)
