# PRD - Refatoração do Design System

## Título da Feature
Padronização Global do Design System com Tailwind v4 e Arquitetura de Tokens Centralizados

## Resumo Executivo

O projeto possui dois artefatos de design system que coexistem sem se comunicar: o `app.css` (com componentes CSS como `.ui-btn`, `.badge`, `.kanban-card`) e o bloco `@theme` no `base.html` (tokens Tailwind v4). Nenhum dos 64 templates usa as classes do `app.css`, e as cores de identidade da marca (`#a98f71`, `#8b7355`, `#1c1917`) aparecem hardcoded em **240 lugares** dentro de 45 arquivos.

O objetivo desta refatoração é consolidar os tokens no `core`, fazer os templates consumirem as classes do design system via Tailwind custom tokens, e criar uma pasta `static/{app}/css/` em cada app para sobreposições específicas — deixando toda a aplicação padronizada e mantível.

## Problema

| Sintoma | Evidência |
|---------|-----------|
| Cor primária hardcoded | 240× `#a98f71` em 45 arquivos `.html` |
| Design system inutilizado | 0/64 templates usam `.ui-btn`, `.badge`, `.kanban-card` |
| Duplicação de padrões | Cards, badges, botões recriados inline em cada template |
| Tokens desconexos | `app.css` usa `var(--brand-primary)`, templates ignoram isso |
| Sem hierarquia clara | Não há distinção entre estilos globais e específicos por app |

## Solução Proposta

Estrutura em três camadas:

```
core/static/css/
├── tokens.css          ← NOVO: fonte única da verdade (@layer theme + CSS vars)
├── components.css      ← NOVO: todas as classes utilitárias (.ui-btn, .badge, etc.)
└── app.css             ← MANTIDO: layout global (navbar, kanban-column, modal)

{app}/static/{app}/css/
└── {app}.css           ← NOVO (por app): overrides e componentes específicos
```

O `base.html` carrega `tokens.css` e `components.css` (globais). Cada template de app que precisar de estilos específicos herda via `{% block extra_head %}`.

---

## Diagnóstico do Estado Atual

### Tailwind no Projeto
O projeto usa **Tailwind CSS v4 via browser CDN** (`@tailwindcss/browser@4`) com o `<style type="text/tailwindcss">` processado em runtime. **Não há build step** — os tokens customizados definidos no `@theme {}` já são aplicados como classes Tailwind (`bg-gold-primary`, `text-gold-dark`). O gap é que os templates nunca usam essas classes; usam `bg-[#a98f71]` diretamente.

### Mapa de Templates por App

| App | Templates | Estilo Dominante | Complexidade |
|-----|-----------|-----------------|--------------|
| `core` | `base.html`, `base_dashboard.html`, `base_public.html`, error pages | Layout global | Alta — âncora do sistema |
| `atendimento_unificado` | `workspace.html` + 7 partials | Chat + Kanban em Tailwind | Alta — caso mais complexo |
| `tenants` | 10+ templates (dashboard, configs, onboarding) | Cards + formulários | Média |
| `evolution_sync` | 2 templates (instance_list, detail) | Cards + tabelas | Baixa |
| `settings_manager` | 4 templates (whitelist) | Formulários + tabelas | Baixa |
| `treinamento` | 5 templates | Formulários + listagens | Baixa |
| `usuarios` | 3 templates (login, cadastro, reset) | Dark luxury (landing) | Média |

### Análise do `atendimento_unificado` (Referência)
O Workspace é o template mais bem estruturado: usa Tailwind de forma consistente, tem partials bem isolados (`chat_message.html`, `kanban_card.html`, `conversation_item.html`), mas sofre do mesmo problema de cores hardcoded. É o **modelo a seguir** para os demais apps.

---

## Requisitos Funcionais

### RF-001: Token CSS Centralizados no Core
**Descrição:** Criar `core/static/css/tokens.css` como fonte única da verdade para todas as cores, tipografia e espaçamentos da marca.
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] Arquivo `tokens.css` define `@theme {}` com todos os tokens Tailwind v4
- [ ] Arquivo `tokens.css` define variáveis CSS (`--brand-*`) para uso em `components.css`
- [ ] `base.html` carrega `tokens.css` antes de qualquer outro CSS
- [ ] Não existe mais `@theme {}` inline no `base.html`

### RF-002: Classes de Componentes Globais em `components.css`
**Descrição:** Extrair todos os componentes do `app.css` para um arquivo `components.css` dedicado, usando tokens do `tokens.css`.
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] `components.css` contém `.ui-btn`, `.ui-input`, `.ui-select`, `.badge`, `.modal`, `.card-actions`
- [ ] Todas as classes usam `var(--brand-*)` ou classes Tailwind com tokens customizados
- [ ] Zero valores hex hardcoded no `components.css`

### RF-003: Substituição de Cores Hardcoded nos Templates
**Descrição:** Substituir todas as 240 ocorrências de `#a98f71`, `#8b7355`, `#8c735a`, `#1c1917` por classes Tailwind com tokens.
**Prioridade:** Alta
**Critérios de Aceite:**
- [ ] `grep -r "#a98f71" src/` retorna 0 resultados em templates
- [ ] Cores substituídas por: `bg-gold-primary`, `text-gold-primary`, `bg-sidebar` (para `#1c1917`)
- [ ] `base_dashboard.html` usa tokens em todos os elementos do sidebar

### RF-004: Pasta de Estilos por App
**Descrição:** Criar estrutura `{app}/static/{app}/css/{app}.css` para cada app com templates, contendo apenas overrides específicos.
**Prioridade:** Média
**Critérios de Aceite:**
- [ ] `atendimento_unificado/static/atendimento_unificado/css/workspace.css` criado com estilos do chat
- [ ] Templates herdam via `{% block extra_head %}{% load static %}<link rel="stylesheet" href="{% static '{app}/css/{app}.css' %}">{% endblock %}`
- [ ] Apps sem necessidade de override específico não têm pasta `css/`

### RF-005: Adoção de Classes de Componentes nos Templates
**Descrição:** Refatorar templates para usar `.ui-btn`, `.badge`, `.ui-input` onde aplicável, em vez de classes Tailwind compostas repetidas.
**Prioridade:** Média
**Critérios de Aceite:**
- [ ] Templates de `tenants` usam `.ui-btn` e `.badge` do design system
- [ ] Templates de `evolution_sync` usam `.ui-btn` e `.ui-input`
- [ ] Templates de `treinamento` usam classes padrão

### RF-006: Partials de Componentes Django (Core)
**Descrição:** Criar partials reutilizáveis em `core/templates/components/` para os padrões mais repetidos.
**Prioridade:** Baixa
**Critérios de Aceite:**
- [ ] `_page_header.html` (título de página com breadcrumb opcional)
- [ ] `_card.html` (card container com header/body opcional)
- [ ] `_alert.html` (substituir o bloco `{% if messages %}` repetido)
- [ ] Pelo menos 3 templates migrados para usar os novos partials

---

## Requisitos Não-Funcionais

### RNF-001: Zero Regressão Visual
- Nenhuma mudança visível para o usuário final. Toda cor substituída deve ter exatamente o mesmo valor HEX mapeado no token.

### RNF-002: Sem Build Step Adicional
- A abordagem CDN do Tailwind v4 deve ser mantida. Nenhum `npm install`, `node_modules` ou processo de build introduzido.

### RNF-003: Backward Compatibility
- `app.css` continua funcionando durante a transição. Os novos arquivos são aditivos até a migração completa.

### RNF-004: Legibilidade do Template
- Após a refatoração, classes como `bg-gold-primary` devem ser auto-documentáveis. O leitor do template entende a intenção sem consultar o CSS.

---

## Escopo

### Incluído
- Arquivo `tokens.css` com todos os tokens da marca
- Arquivo `components.css` consolidado
- Substituição de todas as cores hardcoded nos templates HTML
- Pasta `css/` por app para overrides específicos
- Partials de componentes básicos no `core`
- Migração dos templates mais usados para classes do design system

### Não Incluído (Fora de Escopo)
- Introdução de build step (Webpack, Vite, PostCSS)
- Mudança na identidade visual (cores, fontes, espaçamentos)
- Refatoração do Django Admin / Jazzmin
- Testes automatizados de CSS (visual regression)
- Dark mode (fora do roadmap atual)

---

## Arquitetura de Tokens (Detalhamento)

### `tokens.css` — Fonte Única da Verdade

```css
/* core/static/css/tokens.css */
<style type="text/tailwindcss">
@theme {
  /* Marca — Smart Core */
  --color-gold-primary: #a98f71;   /* Substituí todos bg-[#a98f71] */
  --color-gold-dark:    #8b7355;   /* Substituí todos bg-[#8b7355], bg-[#8c735a] */
  --color-sidebar:      #1c1917;   /* bg do sidebar escuro */

  /* Semântica */
  --color-brand-primary:   #3b82f6;  /* azul */
  --color-brand-success:   #22c55e;  /* verde */
  --color-brand-warning:   #f59e0b;  /* amarelo */
  --color-brand-danger:    #ef4444;  /* vermelho */

  /* Superfícies */
  --color-surface-card:    #ffffff;
  --color-surface-page:    #f8fafc;  /* stone-50 */
  --color-border-default:  #e2e8f0;

  /* Tipografia */
  --font-family-sans: 'Outfit', sans-serif;

  /* Raios */
  --radius-lg: 14px;
  --radius-md: 10px;
}
</style>
```

### Mapeamento de Substituição nos Templates

| Padrão Atual | Substituição |
|--------------|-------------|
| `bg-[#a98f71]` | `bg-gold-primary` |
| `text-[#a98f71]` | `text-gold-primary` |
| `bg-[#a98f71]/10` | `bg-gold-primary/10` |
| `border-l-[#a98f71]` | `border-l-gold-primary` |
| `bg-[#8b7355]`, `bg-[#8c735a]` | `bg-gold-dark` |
| `bg-[#1c1917]` | `bg-sidebar` |
| `ring-[#a98f71]` | `ring-gold-primary` |
| `hover:bg-[#a98f71]` | `hover:bg-gold-primary` |
| `hover:bg-[#8c735a]` | `hover:bg-gold-dark` |
| `focus:ring-[#a98f71]/30` | `focus:ring-gold-primary/30` |

---

## Plano de Execução por Fases

### Fase 1 — Infraestrutura de Tokens (Prioridade: Bloqueante)
**Escopo:** `core` app apenas  
**Arquivos criados/modificados:**
- `core/static/css/tokens.css` — CRIADO (extrai @theme do base.html)
- `core/static/css/components.css` — CRIADO (extrai componentes do app.css)
- `core/templates/base.html` — MODIFICADO (adiciona links para novos CSS, remove @theme inline)

**Resultado:** Base limpa, tokens disponíveis como classes Tailwind.

---

### Fase 2 — `base_dashboard.html` e `base_public.html` (Bloqueante)
**Escopo:** Templates base do layout  
**Arquivos modificados:**
- `core/templates/base_dashboard.html` — substituir ~60 ocorrências de `#a98f71`/`#1c1917`
- `core/templates/base_public.html` — substituir cores do navbar público
- `core/templates/landing_page.html` — substituir cores do landing

**Resultado:** Todo app que herda de `base_dashboard.html` ganha o design padronizado automaticamente.

---

### Fase 3 — `atendimento_unificado` (Workspace / Chat Evolution)
**Escopo:** App mais complexo — tratado como referência de implementação correta  
**Arquivos criados/modificados:**
- `atendimento_unificado/static/atendimento_unificado/css/workspace.css` — CRIADO
  - Estilos específicos do chat: scrollbar customizado, bolhas de mensagem, layout fixo
- `atendimento_unificado/templates/atendimento_unificado/workspace.html` — substituir cores
- `atendimento_unificado/templates/atendimento_unificado/partials/*.html` — substituir cores

**Conteúdo do `workspace.css`:**
```css
/* Estilos específicos do Workspace — não fazem sentido como globais */
.chat-bubble-inbound  { @apply bg-stone-100 text-stone-800 rounded-2xl rounded-tl-sm; }
.chat-bubble-outbound { @apply bg-gold-primary/10 text-stone-800 rounded-2xl rounded-tr-sm; }
.conv-list-item       { @apply w-full text-left px-3 py-3 hover:bg-stone-50 transition-colors flex gap-3 items-start; }
.conv-list-item--active { @apply bg-gold-primary/5 border-l-2 border-l-gold-primary; }
.workspace-avatar     { @apply h-10 w-10 shrink-0 rounded-full bg-gold-primary flex items-center justify-center text-white font-bold text-xs; }
```

**Resultado:** `atendimento_unificado` vira o modelo de como todo app deve ser estruturado.

---

### Fase 4 — Apps de Configuração (`tenants`, `evolution_sync`, `settings_manager`)
**Escopo:** Templates de configuração e administração  
**Abordagem:** Substituição de cores + adoção de `.ui-btn`, `.badge`, `.ui-input` do `components.css`  
**Estimativa:** ~15 templates

---

### Fase 5 — Apps de Conteúdo (`treinamento`, `usuarios`, `oraculo`)
**Escopo:** Formulários, listagens, autenticação  
**Estimativa:** ~12 templates

---

### Fase 6 — Partials de Componentes (Core)
**Escopo:** Padrões repetidos extraídos para includes reutilizáveis  
**Arquivos criados:**
```
core/templates/components/
├── _page_header.html   {% include 'components/_page_header.html' with title="..." subtitle="..." %}
├── _card.html          {% include 'components/_card.html' with title="..." %}
└── _alert.html         (substitui bloco {% if messages %} repetido em 20+ templates)
```

---

## Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Tailwind v4 não processar `tokens.css` externo via CDN | Baixa | Alto | Manter `@theme` no `base.html` via `<style type="text/tailwindcss">` inline; `tokens.css` vira arquivo `.css` puro sem Tailwind syntax |
| Variante de cor com opacidade (`/10`, `/30`) não funcionar com token custom | Baixa | Médio | Tailwind v4 suporta nativamente. Testar em browser antes da fase 2 |
| Regressão visual em algum template | Média | Médio | Mapeamento 1:1 rigoroso (tabela de substituição acima). Revisar visualmente após cada fase |
| App com CSS específico conflitando com global | Baixa | Baixo | Ordem de carregamento: global primeiro, app depois via `{% block extra_head %}` |

---

## Métricas de Sucesso

- [ ] `grep -r "#a98f71" src/ --include="*.html"` → 0 resultados
- [ ] `grep -r "#8b7355\|#8c735a\|#1c1917" src/ --include="*.html"` → 0 resultados
- [ ] `grep -rn "ui-btn\|badge\|ui-input" src/ --include="*.html"` → ≥ 30 ocorrências (adoção real)
- [ ] Todos os 64 templates herdam de `base.html` ou `base_dashboard.html` (sem orphans)
- [ ] `app.css` final tem ≤ 50 linhas (layout only; componentes em `components.css`)

---

## Timeline

| Fase | Descrição | Complexidade | Status |
|------|-----------|-------------|--------|
| 1 | Infraestrutura de Tokens (core) | Baixa | Pendente |
| 2 | Templates Base (`base_dashboard`, `base_public`) | Média | Pendente |
| 3 | `atendimento_unificado` — referência + `workspace.css` | Alta | Pendente |
| 4 | Apps de Configuração (tenants, evolution_sync, settings_manager) | Média | Pendente |
| 5 | Apps de Conteúdo (treinamento, usuarios, oraculo) | Baixa | Pendente |
| 6 | Partials de Componentes no Core | Baixa | Pendente |

---

## Aprovações

| Papel | Nome | Data | Status |
|-------|------|------|--------|
| Product Owner | pwlimaverde | 2026-05-24 | Pendente |
| Tech Lead | — | — | Pendente |
