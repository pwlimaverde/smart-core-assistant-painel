# Plano Completo — Design System Desacoplado (Reestruturado)

> **Origem:** `.context/plans/design-system-refactor.md` (plano base v1.2.3)
> **Documentação auxiliar:** `.context/plans/design-system-refactor/info_aux_design-system-refactor.md`
> **Data da reestruturação:** 2026-05-26

---

## Objetivo

Centralizar **toda a camada visual** em `modules/design_system/` com o mínimo de acoplamento ao Django. Os apps Django ficam com **zero templates e zero CSS** — apenas código Python.

Migrar toda a renderização de templates da aplicação do Django Template Language (DTL) para **Jinja2**, mantendo o DTL ativo **exclusivamente** para o painel administrativo do Django (Jazzmin) e seus overrides.

---

## Estado Atual (Validado em 2026-05-26)

### Já implementado ✅

1. **Infraestrutura Jinja2 funcional:**
   - Backend Jinja2 registrado em `settings.py` (primeiro na lista `TEMPLATES`)
   - `jinja2_env.py` com helpers: `url`, `static`, `csrf_input`, `static_versioned`, `now`
   - Helpers de permissão: `can_view_module`, `is_owner_user`, `can_access_admin_panel`, `has_no_module_permissions`, `has_any_module_permission`, `has_full_module_permissions`

2. **Design Tokens:**
   - `tokens.json` seguindo W3C Design Tokens 2025.10 (4 grupos: brand, semantic, chat, radius/layout)
   - `tokens.css` gerado com variáveis `--ws-*` (90 linhas, 45+ variáveis)
   - Tema escuro via `[data-theme="dark"]` em `core.css`

3. **CSS e Build:**
   - `core.css` com Tailwind v4 (`@import "tailwindcss"`, `@theme`, `@source`)
   - `core.build.css` (produção, purgado)
   - Tasks: `uv run task build-css` / `uv run task watch-css`

4. **Templates base em Jinja2:**
   - `base.html`, `base_dashboard.html`, `base_public.html` — já migrados no design_system

5. **Componentes em Jinja2:**
   - 9 componentes: avatar, badge, button, drawer_base, empty_state, input_text, modal_base, spinner, toast

### Pendente de migração ⏳

- **74 templates** ainda residem nos apps Django com DTL
- **44 desses** usam `{% load %}` (DTL puro)
- **2 templates admin** (overrides) que NÃO devem ser migrados

---

## Princípio Central e Arquitetura (Validado)

### 3 Camadas Portáveis

```
Camada 1 — Tokens (100% portável)
  tokens.json → tokens.css → variáveis --ws-*

Camada 2 — CSS (100% portável)
  core.css (Tailwind v4 @theme) + components.css (utilitárias)

Camada 3 — Templates (90% portável)
  Jinja2 + adaptador Django em jinja2_env.py
```

### Estrutura de Diretórios Alvo

```
modules/design_system/
├── tokens/
│   └── tokens.json                   ← W3C Design Tokens (fonte única)
├── static/
│   └── css/
│       ├── tokens.css                ← Variáveis CSS (gerado de tokens.json)
│       ├── core.css                  ← CSS base + Tailwind v4 @theme
│       ├── core.build.css            ← Compilado (produção)
│       └── components.css            ← [NOVO] Classes utilitárias de componentes
├── templates/
│   ├── base.html                     ← ✅ Já em Jinja2
│   ├── base_dashboard.html           ← ✅ Já em Jinja2
│   ├── base_public.html              ← ✅ Já em Jinja2
│   ├── components/                   ← ✅ 9 componentes em Jinja2
│   └── apps/                         ← [NOVO] Templates migrados dos apps
│       ├── atendimento_unificado/
│       ├── chat_evolution/
│       ├── gestao_kanban/
│       ├── tenants/
│       ├── evolution_sync/
│       ├── settings_manager/
│       ├── treinamento/
│       ├── usuarios/
│       ├── core/                     ← dashboard, home, landing_page
│       └── errors/                   ← 403, 404, 500
└── adapters/
    └── django/
        ├── __init__.py
        ├── apps.py                   ← ✅ AppConfig registrada
        └── jinja2_env.py             ← ✅ Adaptador funcional
```

---

## Plano de Execução — 6 Fases

### Fase 1 — Componentes CSS Utilitários (components.css)
**Agente:** frontend-specialist | **PREVC:** E (Execution)

**Objetivo:** Criar `components.css` com classes utilitárias puras que consomem os tokens `--ws-*`, para que os templates migrados usem classes semânticas em vez de inline styles.

**Tarefas:**
1. Criar `modules/design_system/static/css/components.css` com classes:
   - `.ui-btn`, `.ui-btn--primary`, `.ui-btn--danger`, `.ui-btn--ghost`
   - `.ui-badge`, `.ui-badge--success`, `.ui-badge--warning`, `.ui-badge--danger`
   - `.ui-input`, `.ui-textarea`, `.ui-select`
   - `.ui-card`, `.ui-panel`
   - `.ui-modal-overlay`, `.ui-modal-content`
   - `.ui-spinner`
   - `.ui-toast`, `.ui-toast--success`, `.ui-toast--error`
2. Importar `components.css` no `core.css` via `@import "components.css"`.
3. **Não usar `@layer`** — Tailwind v4 gerencia layers internamente.

**Validação:**
- Build CSS sem erros: `uv run task build-css`
- Classes presentes no `core.build.css` resultante
- Nenhuma regressão visual nos templates já em Jinja2

---

### Fase 2 — Migração do Workspace (Atendimento + Chat + Kanban)
**Agente:** frontend-specialist | **PREVC:** E (Execution)

**Objetivo:** Migrar os templates do workspace unificado para o design_system.

**Templates a migrar (18 arquivos):**

| App | Template | Destino |
|-----|----------|---------|
| atendimento_unificado | `base_workspace.html` | `apps/atendimento_unificado/base_workspace.html` |
| atendimento_unificado | `workspace.html` | `apps/atendimento_unificado/workspace.html` |
| atendimento_unificado | `workspace_disabled.html` | `apps/atendimento_unificado/workspace_disabled.html` |
| atendimento_unificado | `partials/focus_segmented.html` | `apps/atendimento_unificado/partials/focus_segmented.html` |
| chat_evolution | `partials/chat_message.html` | `apps/chat_evolution/partials/chat_message.html` |
| chat_evolution | `partials/chat_mini_bar.html` | `apps/chat_evolution/partials/chat_mini_bar.html` |
| chat_evolution | `partials/composer.html` | `apps/chat_evolution/partials/composer.html` |
| chat_evolution | `partials/contact_info_panel.html` | `apps/chat_evolution/partials/contact_info_panel.html` |
| chat_evolution | `partials/conversation_item.html` | `apps/chat_evolution/partials/conversation_item.html` |
| chat_evolution | `partials/media_viewer.html` | `apps/chat_evolution/partials/media_viewer.html` |
| chat_evolution | `partials/typing_indicator.html` | `apps/chat_evolution/partials/typing_indicator.html` |
| gestao_kanban | `partials/custom_fields_panel.html` | `apps/gestao_kanban/partials/custom_fields_panel.html` |
| gestao_kanban | `partials/detail_panel.html` | `apps/gestao_kanban/partials/detail_panel.html` |
| gestao_kanban | `partials/etiquetas_panel.html` | `apps/gestao_kanban/partials/etiquetas_panel.html` |
| gestao_kanban | `partials/kanban_board.html` | `apps/gestao_kanban/partials/kanban_board.html` |
| gestao_kanban | `partials/kanban_card.html` | `apps/gestao_kanban/partials/kanban_card.html` |
| gestao_kanban | `partials/kanban_column.html` | `apps/gestao_kanban/partials/kanban_column.html` |
| gestao_kanban | `partials/notas_panel.html` | `apps/gestao_kanban/partials/notas_panel.html` |
| gestao_kanban | `partials/transfer_modal.html` | `apps/gestao_kanban/partials/transfer_modal.html` |

**Procedimento por template:**
1. Copiar o template para o destino no design_system.
2. Converter DTL → Jinja2 usando o cheat sheet:
   - Remover `{% load static %}`, `{% load permission_tags %}`, etc.
   - `{% url 'name' arg %}` → `{{ url('name', args=[arg]) }}`
   - `{% static 'path' %}` → `{{ static('path') }}` ou `{{ static_versioned('path') }}`
   - `{% csrf_token %}` → `{{ csrf_input(request) }}`
   - `{% with x=y %}` → `{% set x = y %}`
   - `{{ var|default:"val" }}` → `{{ var|default("val") }}`
   - `{{ var|date:"d/m/Y" }}` → `{{ var.strftime("%d/%m/%Y") }}`
   - `{% empty %}` → `{% else %}`
3. Atualizar `{% extends %}` e `{% include %}` para apontar aos novos caminhos.
4. Atualizar as views Django para usar os novos caminhos de template.
5. Remover o template antigo do app.

**Validação:**
- Workspace funcional com login de tenant ativo
- Chat de conversa renderiza corretamente
- Kanban board com drag-and-drop funcional

---

### Fase 3 — Migração de Configurações e Tenants
**Agente:** frontend-specialist | **PREVC:** E (Execution)

**Objetivo:** Migrar os templates de configuração de tenants, onboarding, backoffice e gestão de usuários.

**Templates a migrar (27 arquivos):**

| App | Template | Destino |
|-----|----------|---------|
| tenants | `base_tenants.html` | `apps/tenants/base_tenants.html` |
| tenants | `dashboard.html` | `apps/tenants/dashboard.html` |
| tenants | `config_database.html` | `apps/tenants/config_database.html` |
| tenants | `config_evolution.html` | `apps/tenants/config_evolution.html` |
| tenants | `config_ai.html` | `apps/tenants/config_ai.html` |
| tenants | `config_trello.html` | `apps/tenants/config_trello.html` |
| tenants | `config_debug.html` | `apps/tenants/config_debug.html` |
| tenants | `config_form.html` | `apps/tenants/config_form.html` |
| tenants | `signup.html` | `apps/tenants/signup.html` |
| tenants | `subscription_expired.html` | `apps/tenants/subscription_expired.html` |
| tenants | `tenant_not_found.html` | `apps/tenants/tenant_not_found.html` |
| tenants | `backoffice/dashboard.html` | `apps/tenants/backoffice/dashboard.html` |
| tenants | `backoffice/register_payment.html` | `apps/tenants/backoffice/register_payment.html` |
| tenants | `onboarding/base.html` | `apps/tenants/onboarding/base.html` |
| tenants | `onboarding/email_access_code.html` | `apps/tenants/onboarding/email_access_code.html` |
| tenants | `onboarding/step_1_tenant.html` | `apps/tenants/onboarding/step_1_tenant.html` |
| tenants | `onboarding/step_2_payment.html` | `apps/tenants/onboarding/step_2_payment.html` |
| tenants | `onboarding/step_3_config.html` | `apps/tenants/onboarding/step_3_config.html` |
| tenants | `onboarding/step_4_provision.html` | `apps/tenants/onboarding/step_4_provision.html` |
| tenants | `users/list.html` | `apps/tenants/users/list.html` |
| tenants | `users/invite.html` | `apps/tenants/users/invite.html` |
| tenants | `users/invite_email.html` | `apps/tenants/users/invite_email.html` |
| tenants | `users/invite_expired.html` | `apps/tenants/users/invite_expired.html` |
| tenants | `users/edit_permissions.html` | `apps/tenants/users/edit_permissions.html` |
| tenants | `users/activate.html` | `apps/tenants/users/activate.html` |
| evolution_sync | `instance_list.html` | `apps/evolution_sync/instance_list.html` |
| evolution_sync | `instance_detail.html` | `apps/evolution_sync/instance_detail.html` |

**Mesmos procedimentos de conversão da Fase 2.**

**Validação:**
- Dashboard de tenant renderiza corretamente
- Onboarding completo (steps 1-4) funcional
- Páginas de configuração (DB, Evolution, AI, Trello) salvam corretamente
- Gestão de usuários (listagem, convite, permissões) funcional

---

### Fase 4 — Migração de Settings, Treinamento e Usuários
**Agente:** frontend-specialist | **PREVC:** E (Execution)

**Objetivo:** Migrar os templates restantes de configurações gerais, treinamento de IA e autenticação.

**Templates a migrar (17 arquivos):**

| App | Template | Destino |
|-----|----------|---------|
| settings_manager | `configuracoes/index.html` | `apps/settings_manager/configuracoes/index.html` |
| settings_manager | `configuracoes/whitelist.html` | `apps/settings_manager/configuracoes/whitelist.html` |
| settings_manager | `configuracoes/whitelist_form.html` | `apps/settings_manager/configuracoes/whitelist_form.html` |
| settings_manager | `configuracoes/whitelist_confirm.html` | `apps/settings_manager/configuracoes/whitelist_confirm.html` |
| treinamento | `treinamento/verificar_treinamentos.html` | `apps/treinamento/treinamento/verificar_treinamentos.html` |
| treinamento | `treinamento/verificar_query_compose.html` | `apps/treinamento/treinamento/verificar_query_compose.html` |
| treinamento | `treinamento/treinar_ia.html` | `apps/treinamento/treinamento/treinar_ia.html` |
| treinamento | `treinamento/testar_query.html` | `apps/treinamento/treinamento/testar_query.html` |
| treinamento | `treinamento/pre_processamento.html` | `apps/treinamento/treinamento/pre_processamento.html` |
| treinamento | `treinamento/cadastrar_query_compose.html` | `apps/treinamento/treinamento/cadastrar_query_compose.html` |
| usuarios | `login.html` | `apps/usuarios/login.html` |
| usuarios | `cadastro.html` | `apps/usuarios/cadastro.html` |
| usuarios | `usuarios/password_reset_form.html` | `apps/usuarios/usuarios/password_reset_form.html` |
| usuarios | `usuarios/password_reset_email.html` | `apps/usuarios/usuarios/password_reset_email.html` |
| usuarios | `usuarios/password_reset_done.html` | `apps/usuarios/usuarios/password_reset_done.html` |
| usuarios | `usuarios/password_reset_confirm.html` | `apps/usuarios/usuarios/password_reset_confirm.html` |
| usuarios | `usuarios/password_reset_complete.html` | `apps/usuarios/usuarios/password_reset_complete.html` |

**Atenção especial:**
- Templates de `password_reset_email.html` são renderizados pelo Django Auth internamente com DTL. Verificar se o Django Auth suporta renderização via Jinja2 ou se é necessário manter este template específico em DTL.
- Templates de login/cadastro usam `form.as_p` que no Jinja2 vira `form.as_p()`.

**Validação:**
- Login e cadastro funcionais
- Fluxo de reset de senha completo
- Telas de treinamento de IA renderizam corretamente
- Configurações de whitelist CRUD funcional

---

### Fase 5 — Migração do Core e Páginas de Erro
**Agente:** frontend-specialist | **PREVC:** E (Execution)

**Objetivo:** Migrar os templates do core (dashboard, home, landing) e páginas de erro.

**Templates a migrar (9 arquivos):**

| App | Template | Destino |
|-----|----------|---------|
| core | `core/dashboard.html` | `apps/core/dashboard.html` |
| core | `core/home.html` | `apps/core/home.html` |
| core | `landing_page.html` | `apps/core/landing_page.html` |
| core | `base.html` | **MANTER como fallback DTL** até Fase 6 |
| core | `base_dashboard.html` | **MANTER como fallback DTL** até Fase 6 |
| core | `base_public.html` | **MANTER como fallback DTL** até Fase 6 |
| core | `403.html` | `apps/errors/403.html` |
| core | `404.html` | `apps/errors/404.html` |
| core | `500.html` | `apps/errors/500.html` |

**Atenção especial:**
- Os templates `base*.html` do core servem como fallback DTL para o Admin. Mantê-los até a Fase 6 garante que o Admin não quebre.
- Páginas de erro (403, 404, 500) devem funcionar sem contexto completo do Django (sem request em alguns casos). Validar que os helpers Jinja2 degradam graciosamente.

**Validação:**
- Dashboard principal renderiza
- Landing page carrega corretamente
- Páginas de erro exibem corretamente (testar 404 com URL inválida)

---

### Fase 6 — Limpeza Total e Finalização
**Agente:** frontend-specialist + code-reviewer | **PREVC:** V (Validation) + C (Confirmation)

**Objetivo:** Remover todos os templates antigos dos apps e validar a integridade total.

**Tarefas:**
1. **Remover pastas `templates/` dos apps Django:**
   - `app/atendimento_unificado/templates/` (inteira)
   - `app/chat_evolution/templates/` (inteira)
   - `app/gestao_kanban/templates/` (inteira)
   - `app/tenants/templates/` (inteira)
   - `app/evolution_sync/templates/` (inteira)
   - `app/settings_manager/templates/` (inteira)
   - `app/treinamento/templates/` (inteira)
   - `app/usuarios/templates/` (inteira)

2. **Limpar `app/core/templates/`:**
   - Remover `base.html`, `base_dashboard.html`, `base_public.html` (fallback DTL)
   - Remover `landing_page.html`, `core/dashboard.html`, `core/home.html`
   - Remover `403.html`, `404.html`, `500.html`
   - **MANTER**: `admin/delete_confirmation.html`, `admin/delete_selected_confirmation.html` (overrides DTL para Jazzmin)

3. **Atualizar `settings.py`:**
   - No backend DTL, remover o diretório `modules/design_system/templates` de `DIRS` (já não é necessário lá)
   - Manter apenas `core/templates` (para os overrides admin) em `DIRS` do DTL

4. **Remover CSS obsoleto:**
   - Verificar se `app/core/static/css/app.css` ainda é referenciado. Se não, remover.
   - Atualizar `STATICFILES_DIRS` se necessário.

5. **Rebuild CSS:**
   - `uv run task build-css` (garante que o purge do Tailwind não removeu classes dos novos caminhos)

**Validação Final:**
```bash
# Nenhum HTML nos apps (exceto admin overrides)
Get-ChildItem -Path "src/smart_core_assistant_painel/app" -Filter "*.html" -Recurse |
  Where-Object { $_.FullName -notlike "*admin*" } |
  Measure-Object
# Deve retornar Count: 0

# Nenhum {% load %} no design_system
Select-String -Path "src/smart_core_assistant_painel/modules/design_system/templates/**/*.html" -Pattern "{% load " -Recurse
# Deve retornar vazio

# Build CSS sem erros
uv run task build-css
```

---

## Correções Aplicadas

### 1. Contagem real de templates (Plano original: ~71 → Real: 74)
**Motivo:** O plano original estimava ~71 templates. A contagem real encontrou **74 templates** nos apps, dos quais **2 são overrides admin** que não devem ser migrados. Total efetivo: **72 templates** a migrar (vs os ~71 estimados).

### 2. Fase 1 original (tokens + jinja2_env) → Já implementada
**Motivo:** O plano original listava na Fase 1 tarefas que **já foram concluídas**: `tokens.json` existe, `tokens.css` existe, `jinja2_env.py` está funcional com todos os helpers, o backend Jinja2 está registrado no `settings.py`. A nova Fase 1 foca em `components.css` (ainda inexistente e necessário).

### 3. Fase 2 original (layouts base) → Já implementada
**Motivo:** `base.html`, `base_dashboard.html` e `base_public.html` já estão em Jinja2 no design_system. Foram eliminados como fase separada.

### 4. APP_DIRS do Jinja2 e diretório de busca
**Motivo:** O plano original não mencionava que `APP_DIRS=True` no backend Jinja2 faz ele buscar em `<app>/jinja2/` (não `<app>/templates/`). O projeto usa `DIRS` explícito, então os templates devem ficar sob `modules/design_system/templates/` (não em subdiretórios `jinja2/` dos apps). As views devem referenciar `apps/<app_name>/template.html` como caminho.

### 5. Templates de Password Reset do Django
**Motivo:** O plano original não mencionava que `password_reset_email.html` pode ser renderizado internamente pelo Django Auth com DTL. Adicionada nota de atenção na Fase 4 para verificar compatibilidade.

### 6. Ordem de prioridade dos backends
**Motivo:** Documentado que o Jinja2 está PRIMEIRO em `TEMPLATES`, o que significa que templates com mesmo nome no design_system têm prioridade sobre templates DTL nos apps. Isso é intencional e correto para a migração gradual.

### 7. Referência a `app.css` no `base.html`
**Motivo:** O `base.html` do design_system ainda referencia `{{ static_versioned('css/app.css') }}` (linha 25). Este arquivo está em `app/core/static/css/` e precisa ser verificado se ainda é necessário ou se pode ser removido na Fase 6.

### 8. Reorganização das Fases
**Motivo:** O plano original tinha 6 fases onde as 2 primeiras já estavam implementadas. O plano reestruturado mantém 6 fases mas com escopo atualizado:
- Fase 1 (nova): Components CSS
- Fases 2-5: Migração por domínio funcional (workspace → tenants → settings+users → core+errors)
- Fase 6: Limpeza (similar à original)

---

## Métricas de Sucesso

| Métrica | Valor Alvo |
|---------|------------|
| Templates migrados para Jinja2 | 72 arquivos |
| Templates remanescentes em DTL (admin) | 2 arquivos |
| HTML nos diretórios `app/*/templates/` | 0 (exceto admin) |
| `{% load %}` no design_system | 0 ocorrências |
| Build CSS funcional | ✅ sem erros |
| Apps Django com 100% backend Python | ✅ |
