# Design - Refatoração UI Design System v2

> 📋 **Proposta**: [proposal.md](./proposal.md)
> 📋 **Plano AI-Context**: [refactor-ui-design-system-v2.md](../../../.context/plans/refactor-ui-design-system-v2.md)
> 📅 **Data**: 2026-01-15

---

## 1. Arquitetura de Templates

### 1.1 Hierarquia Atual

```
base.html
│   ├── Fornece estrutura HTML básica
│   └── Carrega CSS/JS base
│
├── base_public.html
│   ├── Estende: base.html
│   ├── Layout para páginas públicas
│   ├── Sem sidebar
│   └── Navbar simples (se houver)
│
├── base_dashboard.html
│   ├── Layout para área autenticada
│   ├── Sidebar de navegação
│   ├── Header com usuário
│   └── Container principal
│
└── base_tenants.html
    ├── Estende: base_dashboard.html (presumido)
    └── Contexto específico do tenant
```

### 1.2 Problemas Identificados

| Problema                               | Impacto                       | Páginas Afetadas |
| -------------------------------------- | ----------------------------- | ---------------- |
| Páginas de erro usam `base.html`       | Sem estilo consistente        | 403, 404, 500    |
| Template onboarding é standalone       | Desconectado do design system | 4 páginas        |
| Herança de `base_tenants.html` incerta | Sidebar pode não aparecer     | Várias           |

### 1.3 Proposta de Padronização

#### Páginas Públicas

```html
{% extends "base_public.html" %}
```

**Páginas**: Landing, Login, Cadastro, Ativação de Conta, 403, 404, 500

#### Área Autenticada (Tenant)

```html
{% extends "base_tenants.html" %}
```

**Páginas**: Dashboard, Configurações, Gestão de Usuários

#### Área Autenticada (Treinamento)

```html
{% extends "base_dashboard.html" %}
```

**Páginas**: Treinar IA, Pré-processamento, Verificar Treinamentos

#### Backoffice (Super Admin)

```html
{% extends "base_dashboard.html" %}
```

**Páginas**: Dashboard Backoffice, Registrar Pagamento

#### Onboarding (Wizard)

```html
<!-- Mantém template standalone -->
{% extends "tenants/onboarding/base.html" %}
```

**Justificativa**: O wizard de onboarding tem um fluxo visual específico (stepper) que não se encaixa no layout dashboard. Manter isolado é uma decisão de design válida.

---

## 2. Sistema de Permissões

### 2.1 Camadas de Controle

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADAS DE PERMISSÃO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. AUTENTICAÇÃO (Django Auth)                                  │
│     └── @login_required, LoginRequiredMixin                     │
│                                                                 │
│  2. ROLES (TenantRoleType)                                      │
│     └── ADMIN, MANAGER, STAFF, VIEWER                           │
│                                                                 │
│  3. MÓDULOS (TenantModule)                                      │
│     └── CLIENTES, OPERACIONAL, TREINAMENTO, ATENDIMENTOS,       │
│         CONFIGURACOES                                           │
│                                                                 │
│  4. PERMISSÕES GRANULARES (RolePermissions)                     │
│     └── has_permission('treinar_ia'), etc.                      │
│                                                                 │
│  5. SUPERUSER (is_superuser)                                    │
│     └── Acesso total ao backoffice                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Matriz de Acesso por Módulo

| Área              | Público | Auth | Admin | Manager | Staff | Viewer | Super |
| ----------------- | ------- | ---- | ----- | ------- | ----- | ------ | ----- |
| Landing           | ✅      | ✅   | ✅    | ✅      | ✅    | ✅     | ✅    |
| Login/Cadastro    | ✅      | ✅   | ✅    | ✅      | ✅    | ✅     | ✅    |
| Onboarding        | ✅      | ✅   | ✅    | ✅      | ✅    | ✅     | ✅    |
| Dashboard         | ❌      | ✅   | ✅    | ✅      | ✅    | ✅     | ❌\*  |
| Configurações     | ❌      | ❌   | ✅    | ✅      | ❌    | ❌     | ❌\*  |
| Gestão Usuários   | ❌      | ❌   | ✅    | ❌      | ❌    | ❌     | ❌\*  |
| Treinamento IA    | ❌      | ❌   | ✅    | ✅      | ⚙️    | ❌     | ✅    |
| Dashboard Gerente | ❌      | ❌   | ❌    | ❌      | ⚙️    | ❌     | ✅    |
| Backoffice        | ❌      | ❌   | ❌    | ❌      | ❌    | ❌     | ✅    |

**Legenda**:

- ✅ Acesso permitido
- ❌ Acesso negado
- ⚙️ Depende de permissão específica
- ❌\* Superuser é redirecionado para /admin/

---

## 3. Design de Navegação

### 3.1 Sidebar (Área Autenticada)

```
┌─────────────────────────┐
│  🏠 Dashboard           │
├─────────────────────────┤
│  ⚙️ Configurações       │
│     ├── Database        │
│     ├── Evolution       │
│     ├── Trello          │
│     ├── IA              │
│     └── Debug           │
├─────────────────────────┤
│  👥 Usuários            │
├─────────────────────────┤
│  🤖 Treinamento         │
│     ├── Treinar IA      │
│     ├── Verificar       │
│     └── Intents         │
├─────────────────────────┤
│  📊 Gerente             │
├─────────────────────────┤
│  🚪 Sair                │
└─────────────────────────┘
```

### 3.2 Navegação de Breadcrumbs

```
Dashboard > Configurações > Database
Dashboard > Treinamento > Treinar IA
Dashboard > Usuários > Convidar
```

---

## 4. Padrões Visuais

### 4.1 Cores do Design System

| Nome             | Hex       | Uso                      |
| ---------------- | --------- | ------------------------ |
| Primary          | `#a98f71` | Botões, links, destaques |
| Primary Dark     | `#8b7355` | Hover states             |
| Background Dark  | `#1c1917` | Páginas públicas         |
| Background Light | `#fafaf9` | Área autenticada         |
| Text Main        | `#1c1917` | Texto principal          |
| Text Muted       | `#78716c` | Texto secundário         |
| Border           | `#e7e5e4` | Bordas                   |
| Success          | `#10b981` | Sucesso                  |
| Error            | `#ef4444` | Erro                     |

### 4.2 Componentes Padrão

| Componente    | Classes Base                                             |
| ------------- | -------------------------------------------------------- |
| Botão Primary | `bg-[#a98f71] hover:bg-[#8b7355] text-white`             |
| Botão Outline | `border border-stone-600 hover:border-[#a98f71]`         |
| Input         | `bg-stone-800/50 ring-white/10 focus:ring-[#a98f71]`     |
| Card          | `bg-white rounded-2xl shadow-sm border border-stone-100` |

---

## 5. Decisões de Trade-off

### 5.1 Manter Onboarding Standalone

**Decisão**: Não integrar o wizard de onboarding ao `base_dashboard.html`

**Justificativa**:

- O wizard tem um fluxo visual distinto (stepper 1-2-3-4)
- Usuário ainda não tem contexto de tenant durante onboarding
- Migrar quebraria a experiência existente

**Alternativas descartadas**:

- Integrar ao base_public.html (perderia identidade visual do wizard)
- Criar novo template wizard (complexidade desnecessária)

### 5.2 Páginas de Erro

**Decisão**: Avaliar migração de `base.html` para `base_public.html`

**Justificativa**:

- Páginas de erro devem ter aparência consistente com sistema
- `base_public.html` já tem estilo apropriado

**Riscos**:

- `base_public.html` pode ter dependências de contexto
- Erro 500 não deve falhar por causa de contexto

**Mitigação**: Testar renderização com contexto mínimo

---

## 6. Referências

- [Django Templates Documentation](https://docs.djangoproject.com/en/5.2/topics/templates/)
- [Jazzmin Theme](https://django-jazzmin.readthedocs.io/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [RolePermissions](https://django-role-permissions.readthedocs.io/)
