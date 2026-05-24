# PRD - Refatoração do Design System

## Título da Feature
Design System como Módulo Dedicado — `modules/design_system/`

## Resumo Executivo

O projeto possui tokens de cor e componentes CSS definidos, mas desconectados: `app.css` (em `core/`) tem `.ui-btn`, `.badge`, `.modal`, enquanto o `base.html` define `@theme` inline — e nenhum dos 64 templates usa o que foi definido. As 240 ocorrências de `#a98f71` hardcoded são o sintoma.

A solução é criar `modules/design_system/` como um **Django app próprio**, responsável por tudo que é compartilhado: tokens CSS, componentes globais e templates base. Cada app existente consome do design system e guarda apenas o que não pode ser reaproveitado.

---

## Diagnóstico do Estado Atual

### Números Críticos
| Problema | Quantidade |
|----------|-----------|
| Ocorrências de `#a98f71` hardcoded em templates | **240** |
| Arquivos com cores hardcoded | **45** |
| Templates usando `.ui-btn` / `.badge` do `app.css` | **0 / 64** |

### Dois Artefatos Desconexos
| Artefato | Onde | Problema |
|----------|------|---------|
| `app.css` | `core/static/css/` | Define componentes mas ninguém usa |
| `@theme {}` inline | `base.html` | Define tokens mas templates ignoram |

### Como o Django resolve templates e static hoje
```python
# settings.py
TEMPLATES = [{"DIRS": [BASE_DIR / "core/templates"], "APP_DIRS": True, ...}]
STATICFILES_DIRS = (BASE_DIR / "core/static",)
```
- `core/templates/` → acesso global (base.html, base_dashboard.html…)
- `{app}/templates/` → descoberto via `APP_DIRS: True` para cada app em INSTALLED_APPS
- `core/static/` → incluído manualmente + `{app}/static/` via AppDirectoriesFinder

---

## Arquitetura Proposta

### Design System como Django App dentro de `modules/`

```
modules/
├── ai_engine/         ← Python puro (sem mudança)
├── initial_loading/   ← Python puro (sem mudança)
├── services/          ← Python puro (sem mudança)
└── design_system/     ← NOVO: Django app de UI compartilhada
    ├── apps.py
    ├── __init__.py
    ├── static/
    │   └── design_system/
    │       └── css/
    │           ├── tokens.css      ← @theme + CSS vars (fonte única)
    │           ├── components.css  ← .ui-btn, .badge, .modal, .kanban-*
    │           └── layout.css      ← .app-container, .app-navbar, .app-footer
    └── templates/
        └── design_system/
            ├── base.html           ← migrado de core/templates/
            ├── base_dashboard.html ← migrado de core/templates/
            ├── base_public.html    ← migrado de core/templates/
            └── components/
                ├── _alert.html     ← substitui bloco {% if messages %}
                ├── _page_header.html
                └── _card.html
```

### Responsabilidade de cada app após a refatoração

```
core/               → Configurações Django, middleware, context_processors, URLs
                      SEM templates (migrados), SEM static CSS (migrados)

{app}/              → Apenas o que não pode ser reaproveitado:
  templates/{app}/  → extends "design_system/base_dashboard.html"
  static/{app}/css/ → overrides e componentes exclusivos do app
                      (criado só se o app realmente precisar)
```

### Fluxo de herança de templates
```
design_system/base.html
  └── design_system/base_dashboard.html   ← dashboard layout (sidebar + main)
  └── design_system/base_public.html      ← public layout (landing, login)
        └── {app}/{page}.html             ← conteúdo específico do app
```

---

## Token CSS — Fonte Única da Verdade

### `design_system/static/design_system/css/tokens.css`

O arquivo usa `<style type="text/tailwindcss">` para registrar tokens no Tailwind v4 CDN e variáveis CSS para uso em `components.css`:

```css
/* Carregado via base.html. Processado pelo @tailwindcss/browser@4 inline. */
@theme {
  /* Marca */
  --color-gold-primary: #a98f71;
  --color-gold-dark:    #8b7355;
  --color-sidebar:      #1c1917;

  /* Semântica */
  --color-brand-primary: #3b82f6;
  --color-brand-success: #22c55e;
  --color-brand-warning: #f59e0b;
  --color-brand-danger:  #ef4444;

  /* Superfícies */
  --color-surface-card:   #ffffff;
  --color-surface-page:   #f8fafc;
  --color-border-default: #e2e8f0;

  /* Tipografia */
  --font-family-sans: 'Outfit', sans-serif;

  /* Raios */
  --radius-lg: 14px;
  --radius-md: 10px;
}
```

> **Nota técnica:** O Tailwind v4 browser CDN processa `<style type="text/tailwindcss">` inline. O `tokens.css` precisa ser injetado via `{% include %}` dentro do `<style type="text/tailwindcss">` do `base.html`, ou mantido inline. Não é possível linkear um `.css` externo com sintaxe `@theme` via `<link>` — o browser build só processa tags inline. A solução: manter o `@theme` em um `<style type="text/tailwindcss">` dentro de `base.html`, e usar `tokens.css` como CSS puro (variáveis CSS) para `components.css`.

### Mapeamento de Substituição nos Templates

| Padrão atual (hardcoded) | Substituto (token Tailwind) |
|--------------------------|----------------------------|
| `bg-[#a98f71]` | `bg-gold-primary` |
| `text-[#a98f71]` | `text-gold-primary` |
| `bg-[#a98f71]/10` | `bg-gold-primary/10` |
| `border-l-[#a98f71]` | `border-l-gold-primary` |
| `ring-[#a98f71]/30` | `ring-gold-primary/30` |
| `hover:bg-[#a98f71]` | `hover:bg-gold-primary` |
| `bg-[#8b7355]`, `bg-[#8c735a]` | `bg-gold-dark` |
| `hover:bg-[#8c735a]` | `hover:bg-gold-dark` |
| `bg-[#1c1917]` | `bg-sidebar` |
| `border-[#1c1917]`, `border-stone-800` | mantém `border-stone-800` (é token Tailwind) |

---

## Requisitos Funcionais

### RF-001: Criar `modules/design_system/` como Django App
**Prioridade:** Alta — bloqueante para tudo
**Critérios de Aceite:**
- [ ] `modules/design_system/apps.py` criado (`DesignSystemConfig`)
- [ ] `"smart_core_assistant_painel.modules.design_system"` em `INSTALLED_APPS` no `settings.py`
- [ ] Django descobre os templates e static do módulo via `APP_DIRS: True` e `AppDirectoriesFinder`

### RF-002: Migrar Tokens e Componentes para `design_system/static/`
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] `design_system/static/design_system/css/tokens.css` criado com variáveis CSS `--brand-*`
- [ ] `design_system/static/design_system/css/components.css` com `.ui-btn`, `.badge`, `.modal`, `.kanban-*`, `.ui-input`, `.ui-select`
- [ ] `design_system/static/design_system/css/layout.css` com `.app-container`, `.app-navbar`, `.app-footer`, `.divider`
- [ ] Zero hex hardcoded nesses arquivos (usam `var(--brand-*)`)
- [ ] `core/static/css/app.css` reduzido a zero linhas funcionais ou removido

### RF-003: Migrar Templates Base para `design_system/templates/`
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] `design_system/templates/design_system/base.html` criado (migrado de `core/`)
- [ ] `design_system/templates/design_system/base_dashboard.html` migrado
- [ ] `design_system/templates/design_system/base_public.html` migrado
- [ ] `base.html` do design_system carrega `design_system/css/tokens.css`, `components.css`, `layout.css`
- [ ] `base_dashboard.html` do design_system usa `bg-sidebar`, `bg-gold-primary`, etc. — zero hex
- [ ] `core/templates/` mantém apenas `404.html`, `500.html`, `403.html` (erros Django, não herdam do design_system)
- [ ] `TEMPLATES DIRS` no `settings.py` removido ou mantido vazio (tudo via `APP_DIRS`)

### RF-004: Substituir Cores Hardcoded em Todos os Templates
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] `grep -r "#a98f71\|#8b7355\|#8c735a\|#1c1917" src/ --include="*.html"` → 0 resultados
- [ ] Todos os `{% extends "base_dashboard.html" %}` → `{% extends "design_system/base_dashboard.html" %}`
- [ ] Todos os `{% extends "base_public.html" %}` → `{% extends "design_system/base_public.html" %}`

### RF-005: Partials de Componentes no Design System
**Prioridade:** Média
**Critérios de Aceite:**
- [ ] `design_system/templates/design_system/components/_alert.html` substitui o bloco `{% if messages %}` repetido
- [ ] `design_system/templates/design_system/components/_page_header.html` para cabeçalhos de página
- [ ] `design_system/templates/design_system/components/_card.html` para cards container
- [ ] Pelo menos 3 apps migrados para usar os partials

### RF-006: CSS Específico por App (onde necessário)
**Prioridade:** Média
**Critérios de Aceite:**
- [ ] `atendimento_unificado/static/atendimento_unificado/css/workspace.css` criado com:
  - `.chat-bubble-inbound`, `.chat-bubble-outbound`
  - `.conv-list-item`, `.conv-list-item--active`
  - `.workspace-avatar`
- [ ] `workspace.html` carrega o CSS via `{% block extra_head %}`
- [ ] Outros apps que precisarem: mesma estrutura `{app}/static/{app}/css/{app}.css`

---

## Requisitos Não-Funcionais

### RNF-001: Zero Regressão Visual
Substituição 1:1. As cores dos tokens têm exatamente o mesmo hex dos valores que substituem.

### RNF-002: Sem Build Step
Manter Tailwind v4 CDN. Sem `npm`, `node_modules`, Vite ou PostCSS.

### RNF-003: Backward Compatibility Durante Migração
`core/templates/base.html` e `base_dashboard.html` podem coexistir com shims de redirecionamento enquanto os apps são migrados.

---

## Escopo

### Incluído
- Criação de `modules/design_system/` como Django app
- Migração de tokens e componentes CSS para `design_system/static/`
- Migração de templates base para `design_system/templates/`
- Substituição de todas as cores hardcoded nos templates
- Pasta `{app}/static/{app}/css/` para cada app que precisar de override
- Partials de componentes reutilizáveis no design_system

### Não Incluído
- Refatoração do Django Admin / Jazzmin
- Introdução de build step (Webpack, Vite, PostCSS)
- Mudança de identidade visual
- Testes visuais automatizados (visual regression)
- Dark mode

---

## Plano de Execução por Fases

### Fase 1 — Criar `modules/design_system/` *(bloqueante)*
**O que fazer:**
1. Criar `modules/design_system/__init__.py`
2. Criar `modules/design_system/apps.py` com `DesignSystemConfig`
3. Criar estrutura de diretórios `static/design_system/css/` e `templates/design_system/components/`
4. Adicionar `"smart_core_assistant_painel.modules.design_system"` ao `INSTALLED_APPS`
5. Criar `tokens.css`, `components.css`, `layout.css` (conteúdo extraído e limpo do `app.css`)
6. Verificar que o Django descobre templates e static via `APP_DIRS`

**Resultado:** Módulo registrado, arquivos CSS criados. Nenhum app migrado ainda.

---

### Fase 2 — Migrar Templates Base *(bloqueante)*
**O que fazer:**
1. Criar `design_system/templates/design_system/base.html`
   - Carrega `design_system/css/tokens.css`, `components.css`, `layout.css`
   - Remove `@theme` inline (mantém só o `@tailwindcss/browser@4` CDN)
   - Mantém Alpine.js, Outfit font
2. Criar `design_system/templates/design_system/base_dashboard.html`
   - Substitui todas as ~60 ocorrências de hex por tokens (`bg-sidebar`, `bg-gold-primary`, etc.)
3. Criar `design_system/templates/design_system/base_public.html`
4. Criar partials `_alert.html`, `_page_header.html`, `_card.html`

**Resultado:** Templates base limpos no módulo design_system.

---

### Fase 3 — `atendimento_unificado` (referência) *(alta prioridade)*
**O que fazer:**
1. Criar `atendimento_unificado/static/atendimento_unificado/css/workspace.css`
2. Atualizar `workspace.html`:
   - `{% extends "design_system/base_dashboard.html" %}`
   - Adicionar `{% block extra_head %}` carregando `workspace.css`
   - Substituir cores hardcoded nos templates e partials
3. Atualizar todos os partials do workspace

**Por que primeiro:** É o template mais complexo. Resolvê-lo valida toda a arquitetura antes de escalar.

---

### Fase 4 — Apps de Configuração
**Apps:** `tenants`, `evolution_sync`, `settings_manager`  
**O que fazer:** Atualizar `{% extends %}` + substituir cores + adotar `.ui-btn`, `.badge`  
**~15 templates**

---

### Fase 5 — Apps de Conteúdo
**Apps:** `treinamento`, `usuarios`  
**O que fazer:** Atualizar `{% extends %}` + substituir cores + adotar componentes  
**~12 templates**

---

### Fase 6 — Limpeza do `core/`
**O que fazer:**
1. Remover `core/static/css/app.css` (conteúdo já migrado)
2. Remover templates migrados de `core/templates/`
3. Atualizar `settings.py`: remover `TEMPLATES DIRS` (não mais necessário com `APP_DIRS`) e remover `STATICFILES_DIRS` se `core/static/` ficar vazio
4. `core/` vira app Django puro de configuração: settings, middleware, URLs, context_processors

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Tailwind v4 CDN não processar CSS externo com `@theme` | Alta | Alto | `@theme` fica inline em `<style type="text/tailwindcss">` no `base.html`; `tokens.css` exporta apenas variáveis CSS puras para `components.css` |
| Django não encontrar templates do `design_system` | Baixa | Alto | `APP_DIRS: True` + app registrado em `INSTALLED_APPS` → descoberta automática |
| Conflito de nomes de template (ex: `base.html` do core × do design_system) | Média | Médio | Migrar gradualmente; apps atualizam `{% extends %}` antes de remover do core |
| App sem `static/{app}/css/` precisar de override | Baixa | Baixo | Criar pasta apenas quando necessário |

---

## Métricas de Sucesso

- [ ] `grep -r "#a98f71" src/ --include="*.html"` → **0 resultados**
- [ ] `grep -r "#8b7355\|#8c735a\|#1c1917" src/ --include="*.html"` → **0 resultados**
- [ ] `grep -rn "ui-btn\|badge\|ui-input" src/ --include="*.html"` → **≥ 30 ocorrências**
- [ ] `grep -r "extends \"base_dashboard" src/ --include="*.html"` → **0** (todos apontam para `design_system/`)
- [ ] `core/static/css/app.css` → removido ou vazio
- [ ] `modules/design_system/` registrado em `INSTALLED_APPS`

---

## Timeline

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Criar `modules/design_system/` como Django app | Pendente |
| 2 | Migrar templates base para `design_system/templates/` | Pendente |
| 3 | `atendimento_unificado` — referência + `workspace.css` | Pendente |
| 4 | Apps de configuração (tenants, evolution_sync, settings_manager) | Pendente |
| 5 | Apps de conteúdo (treinamento, usuarios) | Pendente |
| 6 | Limpeza do `core/` | Pendente |

---

## Aprovações

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | pwlimaverde | 2026-05-24 | Pendente |
| Tech Lead | — | — | Pendente |
