# Mapa de Navegação - Smart Core Assistant Painel

> 📋 **Última Atualização**: 2026-01-15
> 📁 **Localização**: `docs_dev/planejamento/mapa_navegacao/`
> 🔗 **Plano AI-Context**: [refactor-ui-design-system-v2.md](../../../.context/plans/refactor-ui-design-system-v2.md)

## Objetivo

Documentar **todas as páginas navegáveis** do sistema, incluindo:

- URLs e views correspondentes
- Templates utilizados
- Permissões de acesso
- Links presentes em cada página
- Status de conformidade com Design System

## Estrutura de Arquivos

| #   | Arquivo                                              | Módulo                   | Status         |
| --- | ---------------------------------------------------- | ------------------------ | -------------- |
| 01  | [01_paginas_publicas.md](./01_paginas_publicas.md)   | Páginas Públicas e Erros | ✅ Documentado |
| 02  | [02_autenticacao.md](./02_autenticacao.md)           | Autenticação             | ✅ Documentado |
| 03  | [03_onboarding.md](./03_onboarding.md)               | Onboarding Wizard        | ✅ Documentado |
| 04  | [04_backoffice.md](./04_backoffice.md)               | Backoffice (Super Admin) | ✅ Documentado |
| 05  | [05_dashboard_tenant.md](./05_dashboard_tenant.md)   | Dashboard Tenant         | ✅ Documentado |
| 06  | [06_configuracoes.md](./06_configuracoes.md)         | Configurações            | ✅ Documentado |
| 07  | [07_gestao_usuarios.md](./07_gestao_usuarios.md)     | Gestão de Usuários       | ✅ Documentado |
| 08  | [08_treinamento_ia.md](./08_treinamento_ia.md)       | Treinamento IA           | ✅ Documentado |
| 09  | [09_dashboard_gerente.md](./09_dashboard_gerente.md) | Dashboard Gerente        | ✅ Documentado |

## Legenda de Status

| Símbolo | Significado                                 |
| ------- | ------------------------------------------- |
| ⏳      | Pendente - Ainda não documentado            |
| 🔄      | Em Andamento - Mapeamento em progresso      |
| ✅      | Aprovado - Documentação completa e aprovada |
| ⚠️      | Revisão Necessária - Aguardando correções   |

## Resumo de Páginas por Módulo

### 1. Páginas Públicas e Erros (4 páginas)

| Página   | URL           | View                       | Template            |
| -------- | ------------- | -------------------------- | ------------------- |
| Landing  | `/`           | `LandingPageView`          | `landing_page.html` |
| Erro 403 | N/A (handler) | `custom_permission_denied` | `403.html`          |
| Erro 404 | N/A (handler) | `custom_page_not_found`    | `404.html`          |
| Erro 500 | N/A (handler) | `custom_server_error`      | `500.html`          |

### 2. Autenticação (3 páginas)

| Página   | URL                   | View          | Template        |
| -------- | --------------------- | ------------- | --------------- |
| Login    | `/usuarios/login/`    | `login`       | `login.html`    |
| Cadastro | `/usuarios/cadastro/` | `cadastro`    | `cadastro.html` |
| Logout   | `/usuarios/logout/`   | `logout_view` | N/A (redirect)  |

### 3. Onboarding (4 páginas)

| Página             | URL                           | View                 | Template                |
| ------------------ | ----------------------------- | -------------------- | ----------------------- |
| Step 1 - Tenant    | `/tenants/onboarding/`        | `Step1TenantView`    | `step_1_tenant.html`    |
| Step 2 - Payment   | `/tenants/onboarding/step/2/` | `Step2PaymentView`   | `step_2_payment.html`   |
| Step 3 - Config    | `/tenants/onboarding/step/3/` | `Step3ConfigView`    | `step_3_config.html`    |
| Step 4 - Provision | `/tenants/onboarding/step/4/` | `Step4ProvisionView` | `step_4_provision.html` |

### 4. Backoffice (2 páginas)

| Página           | URL                                           | View                      | Template                           |
| ---------------- | --------------------------------------------- | ------------------------- | ---------------------------------- |
| Dashboard        | `/tenants/bo/`                                | `BackofficeDashboardView` | `backoffice/dashboard.html`        |
| Register Payment | `/tenants/bo/tenant/<uuid>/register-payment/` | `RegisterPaymentView`     | `backoffice/register_payment.html` |

### 5. Dashboard Tenant (1 página)

| Página    | URL                   | View            | Template                 |
| --------- | --------------------- | --------------- | ------------------------ |
| Dashboard | `/tenants/dashboard/` | `DashboardView` | `tenants/dashboard.html` |

### 6. Configurações (5 páginas)

| Página    | URL                          | View                  | Template                |
| --------- | ---------------------------- | --------------------- | ----------------------- |
| Database  | `/tenants/config/database/`  | `DatabaseConfigView`  | `config_database.html`  |
| Evolution | `/tenants/config/evolution/` | `EvolutionConfigView` | `config_evolution.html` |
| Trello    | `/tenants/config/trello/`    | `TrelloConfigView`    | `config_trello.html`    |
| AI        | `/tenants/config/ai/`        | `AIConfigView`        | `config_ai.html`        |
| Debug     | `/tenants/config/debug/`     | `ConfigDebugView`     | `config_debug.html`     |

### 7. Gestão de Usuários (5 páginas)

| Página            | URL                                | View               | Template                      |
| ----------------- | ---------------------------------- | ------------------ | ----------------------------- |
| Lista de Usuários | `/tenants/users/`                  | `list_users`       | `users/list.html`             |
| Convidar Usuário  | `/tenants/users/invite/`           | `invite_user`      | `users/invite.html`           |
| Editar Permissões | `/tenants/users/<id>/permissions/` | `edit_permissions` | `users/edit_permissions.html` |
| Ativar Conta      | `/tenants/activate/<token>/`       | `activate_account` | `users/activate.html`         |
| Convite Expirado  | N/A                                | N/A                | `users/invite_expired.html`   |

### 8. Treinamento IA (5 páginas)

| Página                 | URL                                     | View                                 | Template                       |
| ---------------------- | --------------------------------------- | ------------------------------------ | ------------------------------ |
| Treinar IA             | `/treinamento/treinar-ia/`              | `treinar_ia`                         | `treinar_ia.html`              |
| Pré-processamento      | `/treinamento/pre-processamento/<id>/`  | `pre_processamento`                  | `pre_processamento.html`       |
| Verificar Treinamentos | `/treinamento/verificar-treinamentos/`  | `verificar_treinamentos_vetorizados` | `verificar_treinamentos.html`  |
| Cadastrar Query        | `/treinamento/cadastrar-query-compose/` | `cadastrar_query_compose`            | `cadastrar_query_compose.html` |
| Verificar Query        | `/treinamento/verificar-query-compose/` | `verificar_query_compose`            | `verificar_query_compose.html` |

### 9. Dashboard Gerente (2 páginas)

| Página            | URL                            | View                | Template                 |
| ----------------- | ------------------------------ | ------------------- | ------------------------ |
| Dashboard Gerente | `/usuarios/dashboard-gerente/` | `dashboard_gerente` | `dashboard_gerente.html` |
| Permissões        | `/usuarios/permissoes/`        | `permissoes`        | `permissoes.html`        |

---

## Total de Páginas: 31

| Categoria          | Quantidade |
| ------------------ | ---------- |
| Páginas Públicas   | 4          |
| Autenticação       | 3          |
| Onboarding         | 4          |
| Backoffice         | 2          |
| Dashboard Tenant   | 1          |
| Configurações      | 5          |
| Gestão de Usuários | 5          |
| Treinamento IA     | 5          |
| Dashboard Gerente  | 2          |
| **TOTAL**          | **31**     |

---

## Processo de Validação

1. **Criar documento** do módulo (ex: `01_paginas_publicas.md`)
2. **Mapear cada página** com detalhes completos
3. **Auditar Design System** - verificar templates e componentes
4. **Mapear links** - documentar destinos
5. **Verificar permissões** - testar roles
6. **Solicitar aprovação** antes de avançar

> ⚠️ **REGRA**: Só avançar para o próximo módulo após aprovação do anterior
