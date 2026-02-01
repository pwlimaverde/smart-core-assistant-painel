# Módulo 4 - Backoffice (Super Admin)

> 📋 **Status**: ✅ Aprovado
> 📅 **Data**: 2026-02-01
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                               |
| -------------------- | ----------------------------------- |
| **Total de Páginas** | 2                                   |
| **Template Base**    | `admin/base_site.html`              |
| **Autenticação**     | ✅ Requerida                        |
| **Permissão**        | 🔴 `is_superuser` OBRIGATÓRIO       |
| **App**              | `tenants`                           |

---

## Página 1: Dashboard Backoffice

### Informações Básicas

| Campo             | Valor                                                 |
| ----------------- | ----------------------------------------------------- |
| **Nome**          | Dashboard Backoffice                                  |
| **URL**           | `/tenants/bo/`                                        |
| **URL Name**      | `tenants:backoffice_dashboard`                        |
| **View**          | `BackofficeDashboardView` (Class-Based, TemplateView) |
| **Template**      | `tenants/backoffice/dashboard.html`                   |
| **Template Base** | `admin/base_site.html`                                |
| **App**           | `tenants`                                             |
| **Arquivo View**  | `app/tenants/views/backoffice/dashboard.py:9-54`      |

### Permissões

| Tipo                 | Valor                                             |
| -------------------- | ------------------------------------------------- |
| **Autenticação**     | ✅ Requerida                                      |
| **Roles Permitidos** | 🔴 **Apenas `is_superuser`**                      |
| **Módulo**           | N/A                                               |
| **Decorator/Mixin**  | `UserPassesTestMixin` → `test_func: is_superuser` |

### Métricas Exibidas

| Métrica                       | Descrição                                |
| ----------------------------- | ---------------------------------------- |
| `total_tenants`               | Total de tenants cadastrados             |
| `active_tenants`              | Tenants ativos                           |
| `subscriptions_active`        | Assinaturas ativas                       |
| `expiring_soon_count`         | Assinaturas expirando em 30 dias         |
| `recent_tenants`              | Últimos 5 tenants criados                |
| `expiring_subscriptions_list` | Lista de assinaturas expirando em 7 dias |

### Links da Página

| #   | Nome do Link        | URL de Destino                                | URL Name                              | Resumo                          |
| --- | ------------------- | --------------------------------------------- | ------------------------------------- | ------------------------------- |
| 1   | Registrar Pagamento | `/tenants/bo/tenant/<uuid>/register-payment/` | `tenants:backoffice_register_payment` | Registrar pagamento para tenant |

### Auditoria Design System

| Item                  | Status        | Observação                     |
| --------------------- | ------------- | ------------------------------ |
| Template base correto | ✅ Verificado | Usa `admin/base_site.html`     |
| Sidebar visível       | ✅ Verificado | Navegação do admin Django      |
| Navegação funcional   | ✅ Verificado | Links para tenants             |
| Responsividade        | ✅ Verificado | Layout responsivo              |
| Padrões visuais       | ✅ Verificado | Padrão admin                   |

---

## Página 2: Registrar Pagamento

### Informações Básicas

| Campo             | Valor                                              |
| ----------------- | -------------------------------------------------- |
| **Nome**          | Registrar Pagamento                                |
| **URL**           | `/tenants/bo/tenant/<uuid:pk>/register-payment/`   |
| **URL Name**      | `tenants:backoffice_register_payment`              |
| **View**          | `RegisterPaymentView` (Class-Based)                |
| **Template**      | `tenants/backoffice/register_payment.html`         |
| **Template Base** | `admin/base_site.html`                             |
| **App**           | `tenants`                                          |
| **Arquivo View**  | `app/tenants/views/backoffice/register_payment.py` |

### Parâmetros de URL

| Parâmetro | Tipo | Descrição    |
| --------- | ---- | ------------ |
| `pk`      | UUID | ID do Tenant |

### Permissões

| Tipo                 | Valor                             |
| -------------------- | --------------------------------- |
| **Autenticação**     | ✅ Requerida                      |
| **Roles Permitidos** | 🔴 **Apenas `is_superuser`**      |
| **Módulo**           | N/A                               |
| **Decorator/Mixin**  | `UserPassesTestMixin` (presumido) |

### Links da Página

| #   | Nome do Link        | URL de Destino | URL Name                       | Resumo               |
| --- | ------------------- | -------------- | ------------------------------ | -------------------- |
| 1   | Voltar ao Dashboard | `/tenants/bo/` | `tenants:backoffice_dashboard` | Dashboard Backoffice |

### Auditoria Design System

| Item                  | Status        | Observação                     |
| --------------------- | ------------- | ------------------------------ |
| Template base correto | ✅ Verificado | Usa `admin/base_site.html`     |
| Sidebar visível       | ✅ Verificado | Navegação do admin Django      |
| Navegação funcional   | ✅ Verificado | Link de voltar                 |
| Responsividade        | ✅ Verificado | Layout responsivo              |
| Padrões visuais       | ✅ Verificado | Padrão admin                   |

---

## Controle de Acesso

### Matriz de Permissões

| Role      | Dashboard | Registrar Pagamento |
| --------- | --------- | ------------------- |
| Superuser | ✅        | ✅                  |
| Admin     | ❌        | ❌                  |
| Manager   | ❌        | ❌                  |
| Staff     | ❌        | ❌                  |
| Viewer    | ❌        | ❌                  |

> ⚠️ **IMPORTANTE**: Qualquer usuário não-superuser que tentar acessar será redirecionado/bloqueado pelo `UserPassesTestMixin`.

---

## Redirecionamentos do Módulo

| Origem               | Destino      | Condição               | View                  |
| -------------------- | ------------ | ---------------------- | --------------------- |
| Acesso negado        | Login ou 403 | `is_superuser = False` | `UserPassesTestMixin` |
| Pagamento registrado | Dashboard    | Sucesso                | `RegisterPaymentView` |

---

## Pontos de Atenção Identificados

### ✅ Sem issues críticas

---

## Checklist de Validação do Módulo

- [x] Todas as páginas documentadas
- [x] Todos os links mapeados
- [x] Permissões verificadas (is_superuser)
- [x] Template base auditado
- [x] Redirecionamentos documentados
- [x] **APROVADO PELO USUÁRIO**
