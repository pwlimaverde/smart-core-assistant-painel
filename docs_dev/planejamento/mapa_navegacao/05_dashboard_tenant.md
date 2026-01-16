# Módulo 5 - Dashboard Tenant

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                          |
| -------------------- | ------------------------------ |
| **Total de Páginas** | 1                              |
| **Template Base**    | `tenants/dashboard.html`       |
| **Autenticação**     | ✅ Requerida                   |
| **Permissão**        | Usuário autenticado com tenant |
| **App**              | `tenants`                      |

---

## Página 1: Dashboard Principal do Tenant

### Informações Básicas

| Campo             | Valor                                                                      |
| ----------------- | -------------------------------------------------------------------------- |
| **Nome**          | Dashboard do Tenant                                                        |
| **URL**           | `/tenants/dashboard/`                                                      |
| **URL Name**      | `tenants:dashboard`                                                        |
| **View**          | `DashboardView` (Class-Based, TemplateView)                                |
| **Template**      | `tenants/dashboard.html`                                                   |
| **Template Base** | ⚠️ A verificar (provavelmente `base_tenants.html` → `base_dashboard.html`) |
| **App**           | `tenants`                                                                  |
| **Arquivo View**  | `app/tenants/views/legacy_views.py:94-113`                                 |

### Permissões

| Tipo                 | Valor                                                   |
| -------------------- | ------------------------------------------------------- |
| **Autenticação**     | ✅ Requerida                                            |
| **Roles Permitidos** | `ADMIN`, `MANAGER`, `STAFF`, `VIEWER` (todos do tenant) |
| **Módulo**           | N/A (dashboard geral)                                   |
| **Decorator/Mixin**  | `LoginRequiredMixin`, `TenantOwnerRequiredMixin`        |

### Contexto Exibido

| Variável       | Descrição                         |
| -------------- | --------------------------------- |
| `tenant`       | Objeto Tenant atual               |
| `subscription` | Assinatura do tenant              |
| `config`       | Configurações do tenant           |
| Estatísticas   | Métricas de uso (se implementado) |

### Links da Página (Previstos)

| #   | Nome do Link         | URL de Destino               | URL Name                   | Resumo                |
| --- | -------------------- | ---------------------------- | -------------------------- | --------------------- |
| 1   | Configurar Database  | `/tenants/config/database/`  | `tenants:config_database`  | Config PostgreSQL     |
| 2   | Configurar Evolution | `/tenants/config/evolution/` | `tenants:config_evolution` | Config WhatsApp       |
| 3   | Configurar Trello    | `/tenants/config/trello/`    | `tenants:config_trello`    | Config Trello         |
| 4   | Configurar IA        | `/tenants/config/ai/`        | `tenants:config_ai`        | Config IA/Prompts     |
| 5   | Gerenciar Usuários   | `/tenants/users/`            | `tenants:user_list`        | Lista de funcionários |
| 6   | Treinamento IA       | `/treinamento/treinar-ia/`   | `treinamento:treinar_ia`   | Treinar IA            |
| 7   | Debug Config         | `/tenants/config/debug/`     | `tenants:config_debug`     | Verificar configs     |

### Auditoria Design System

| Item                  | Status       | Observação                               |
| --------------------- | ------------ | ---------------------------------------- |
| Template base correto | ⏳ Verificar | Deve usar `base_dashboard.html`          |
| Sidebar visível       | ⏳ Verificar | **CRÍTICO** - Deve ter navegação lateral |
| Navegação funcional   | ⏳ Verificar | Links para todas as áreas                |
| Responsividade        | ⏳ Verificar | Layout adaptável                         |
| Padrões visuais       | ⏳ Verificar | Cards, métricas, ícones                  |

---

## Controle de Acesso

### Matriz de Permissões

| Role           | Dashboard                       |
| -------------- | ------------------------------- |
| Owner (Tenant) | ✅                              |
| Admin          | ✅                              |
| Manager        | ✅                              |
| Staff          | ✅                              |
| Viewer         | ✅                              |
| Superuser      | ❌ (redireciona para `/admin/`) |

### Comportamento de Redirecionamento

| Condição                       | Destino               |
| ------------------------------ | --------------------- |
| Superuser acessa `/dashboard/` | `/admin/`             |
| Usuário sem tenant             | 403 ou página de erro |
| Usuário de outro tenant        | 403                   |

---

## Redirecionamentos Relacionados

| Origem               | Destino               | Condição                      | View                 |
| -------------------- | --------------------- | ----------------------------- | -------------------- |
| `/` (landing)        | `/tenants/dashboard/` | Usuário autenticado não-super | `LandingPageView`    |
| `/dashboard/` (core) | `/tenants/dashboard/` | Usuário autenticado não-super | `dashboard` (core)   |
| Login sucesso        | `/tenants/dashboard/` | Sem atendente vinculado       | `login`              |
| Onboarding sucesso   | `/tenants/dashboard/` | Provisionamento completo      | `Step4ProvisionView` |

---

## Pontos de Atenção Identificados

### 🔴 Issues Críticos

1. **Verificar herança de template** - Confirmar que usa `base_dashboard.html` para ter sidebar
2. **Mixins de permissão** - Verificar implementação de `TenantOwnerRequiredMixin`

### 🟡 Melhorias Sugeridas

1. **Onboarding incompleto** - Exibir alerta se configurações pendentes
2. **Status de integração** - Mostrar status de Evolution/Trello no dashboard

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas
- [ ] Template base auditado
- [ ] Sidebar funcional
- [ ] Redirecionamentos documentados
- [ ] **APROVADO PELO USUÁRIO**
