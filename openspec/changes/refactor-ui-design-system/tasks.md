# Tasks: Refatorar UI para Design System "Smart Core"

Este documento lista as tarefas ordenadas para implementar o refatoramento do Design System.

---

## Fase 1: Correção de Herança de Templates (Crítico)

### 1.1 Migrar templates de `treinamento` para `base_dashboard.html`

- [x] **T1.1.1** Atualizar `verificar_treinamentos.html`
  - Mudar `{% extends "base.html" %}` para `{% extends "base_dashboard.html" %}`
  - Remover `<header>` e `<main>` hardcoded (já existem no base)
  - Mover conteúdo para dentro do bloco `{% block content %}`
- [x] **T1.1.2** Atualizar `treinar_ia.html`
  - Mesmo padrão de T1.1.1
- [x] **T1.1.3** Atualizar `pre_processamento.html`
  - Mesmo padrão de T1.1.1
- [x] **T1.1.4** Atualizar `cadastrar_query_compose.html`
  - Mesmo padrão de T1.1.1
- [x] **T1.1.5** Atualizar `verificar_query_compose.html`
  - Mesmo padrão de T1.1.1

**Validação**: Navegar para cada URL e confirmar que sidebar aparece

---

## Fase 2: Reestruturação de Navegação (Alta Prioridade)

### 2.1 Corrigir redirecionamento no login

- [x] **T2.1.1** Modificar `usuarios/views.py` - função `login`
  - Após autenticação bem-sucedida:
    - Se `user.is_superuser`: redirecionar para `/admin/`
    - Caso contrário: redirecionar para `/tenants/dashboard/`

### 2.2 Corrigir links da sidebar

- [x] **T2.2.1** Modificar `base_dashboard.html`
  - Trocar link de "Dashboard" de `{% url 'tenants:dashboard' %}` para lógica condicional
  - **Decisão**: Manter como `/tenants/dashboard/` (é o comportamento correto para tenant users)

### 2.3 Remover ou redirecionar rota `/dashboard/` duplicada

- [x] **T2.3.1** Modificar `core/urls.py`

  - Opção A: Remover rota `path("dashboard/", views.dashboard, ...)`
  - Opção B: Redirecionar para `/tenants/dashboard/`
  - **Recomendação**: Opção B para manter compatibilidade

- [x] **T2.3.2** Modificar `core/views.py` - função `dashboard`
  - Alterar para redirect: `return redirect('tenants:dashboard')`

---

## Fase 3: Sidebar Baseada em Permissões (Média Prioridade)

### 3.1 Ocultar seção "Painel Admin" para não-staff

- [x] **T3.1.1** `base_dashboard.html` já tem `{% if request.user.is_staff %}` ✅
  - Verificar se está funcionando corretamente

### 3.2 Ocultar seção "Gestão > Usuários" para não-admins

- [x] **T3.2.1** Modificar `base_dashboard.html`
  - Adicionar verificação de role antes do link de Usuários
  - Usar: `{% if tenant_user.role == 'admin' or request.user == tenant.owner %}`

### 3.3 Ocultar seções por `module_permissions`

- [x] **T3.3.1** Criar template tag `can_view_module`

  - Input: nome do módulo (ex: 'treinamento', 'configuracoes')
  - Output: boolean baseado em `TenantUser.has_module_permission()`

- [x] **T3.3.2** Aplicar template tag nas seções da sidebar
  - Seção "Configurações": `{% if can_view_module 'configuracoes' %}`
  - Seção "Treinamento" (futura): `{% if can_view_module 'treinamento' %}`

---

## Fase 4: Correções Visuais do Dashboard (Baixa Prioridade)

### 4.1 Padronizar altura dos cards

- [x] **T4.1.1** Modificar `tenants/dashboard.html`
  - Adicionar `h-full` aos cards para equalizar altura
  - Grid já está correto: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`

### 4.2 Remover cards de funcionalidades não implementadas

- [x] **T4.2.1** Revisar se todos os cards apontam para funcionalidades existentes
  - "Treinamentos" ✅
  - "Queries" ✅
  - "Painel do Cliente" - Verificar se existe

### 4.3 Corrigir erro no final da página

- [x] **T4.3.1** Investigar e corrigir erro visual reportado
  - Provavelmente relacionado a template tag ou variável não definida

---

## Fase 5: Cleanup e Padronização (Baixa Prioridade)

### 5.1 Deprecar `base_tenants.html`

- [ ] **T5.1.1** Migrar `signup.html` para usar `base_public.html`
- [ ] **T5.1.2** Verificar se `config_form.html` é utilizado; se não, remover
- [ ] **T5.1.3** Após migração, deletar `base_tenants.html`

### 5.2 Documentar Design System

- [ ] **T5.2.1** Criar arquivo `DESIGN_SYSTEM.md` na pasta `docs/`
  - Documentar tokens de cor, tipografia, componentes padrão

---

## Ordem de Execução Recomendada

```
Fase 1 (T1.1.1 → T1.1.5) - Crítico, pode ser paralelizado
    ↓
Fase 2 (T2.1.1 → T2.3.2) - Depende de Fase 1 estar estável
    ↓
Fase 3 (T3.1.1 → T3.3.2) - Pode ser feito em paralelo com Fase 4
    ↓
Fase 4 (T4.1.1 → T4.3.1) - Correções visuais
    ↓
Fase 5 (T5.1.1 → T5.2.1) - Cleanup final
```

---

## Critérios de Aceite

1. **Consistência Visual**: Todas as páginas internas exibem sidebar
2. **Navegação Correta**: Links direcionam para destinos corretos
3. **Permissões Funcionais**: Sidebar mostra apenas opções permitidas ao usuário
4. **Zero Regressões**: Funcionalidades existentes continuam funcionando
5. **Responsividade**: Layout funciona em desktop (mobile é secundário)
