# Módulo 3 - Onboarding Wizard

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                                       |
| -------------------- | ------------------------------------------- |
| **Total de Páginas** | 4 (+ 1 API)                                 |
| **Template Base**    | `tenants/onboarding/base.html` (standalone) |
| **Autenticação**     | ❌ Não requerida                            |
| **App**              | `tenants`                                   |
| **Fluxo**            | Wizard sequencial (Step 1 → 2 → 3 → 4)      |

---

## Página 1: Step 1 - Dados do Tenant

### Informações Básicas

| Campo             | Valor                                     |
| ----------------- | ----------------------------------------- |
| **Nome**          | Onboarding Step 1 - Empresa               |
| **URL**           | `/tenants/onboarding/`                    |
| **URL Name**      | `tenants:onboarding_step_1`               |
| **View**          | `Step1TenantView` (Class-Based, FormView) |
| **Template**      | `tenants/onboarding/step_1_tenant.html`   |
| **Template Base** | `tenants/onboarding/base.html`            |
| **App**           | `tenants`                                 |
| **Arquivo View**  | `app/tenants/views/onboarding.py:29-43`   |

### Comportamento

| Ação                  | Resultado                                   |
| --------------------- | ------------------------------------------- |
| Form válido submetido | Cria `Tenant` e salva `tenant_id` na sessão |
| Sucesso               | Redireciona para Step 2                     |

### Permissões

| Tipo                 | Valor              |
| -------------------- | ------------------ |
| **Autenticação**     | ❌ Não requerida   |
| **Roles Permitidos** | 🌐 Todos (público) |
| **Módulo**           | N/A                |
| **Decorator/Mixin**  | Nenhum             |

### Links da Página

| #   | Nome do Link    | URL de Destino                | URL Name                    | Resumo         |
| --- | --------------- | ----------------------------- | --------------------------- | -------------- |
| 1   | Próximo (botão) | `/tenants/onboarding/step/2/` | `tenants:onboarding_step_2` | Step 2 - Plano |

### Formulário

| Campo           | Nome          | Tipo  | Obrigatório |
| --------------- | ------------- | ----- | ----------- |
| Nome da Empresa | `name`        | text  | ✅          |
| Slug            | `slug`        | text  | ✅          |
| Email           | `owner_email` | email | ✅          |
| Nome do Owner   | `owner_name`  | text  | ✅          |

### Auditoria Design System

| Item                  | Status       | Observação              |
| --------------------- | ------------ | ----------------------- |
| Template base correto | ⏳ Verificar | Usa template standalone |
| Sidebar visível       | N/A          | Wizard standalone       |
| Navegação funcional   | ⏳ Verificar | Stepper visual          |
| Responsividade        | ⏳ Verificar | CSS customizado         |
| Padrões visuais       | ⏳ Verificar | Cores `#a98f71`         |

---

## Página 2: Step 2 - Seleção de Plano

### Informações Básicas

| Campo             | Valor                                          |
| ----------------- | ---------------------------------------------- |
| **Nome**          | Onboarding Step 2 - Plano                      |
| **URL**           | `/tenants/onboarding/step/2/`                  |
| **URL Name**      | `tenants:onboarding_step_2`                    |
| **View**          | `Step2PaymentView` (Class-Based, TemplateView) |
| **Template**      | `tenants/onboarding/step_2_payment.html`       |
| **Template Base** | `tenants/onboarding/base.html`                 |
| **App**           | `tenants`                                      |
| **Arquivo View**  | `app/tenants/views/onboarding.py:46-68`        |

### Comportamento

| Ação                  | Resultado                |
| --------------------- | ------------------------ |
| Plano selecionado     | Atualiza plano do Tenant |
| Sem plano selecionado | Volta para Step 2        |
| Sucesso               | Redireciona para Step 3  |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ❌ Não requerida                           |
| **Roles Permitidos** | 🌐 Todos (público)                         |
| **Módulo**           | N/A                                        |
| **Decorator/Mixin**  | `OnboardingSessionMixin` (verifica sessão) |

### Links da Página

| #   | Nome do Link    | URL de Destino                | URL Name                    | Resumo |
| --- | --------------- | ----------------------------- | --------------------------- | ------ |
| 1   | Voltar (botão)  | `/tenants/onboarding/`        | `tenants:onboarding_step_1` | Step 1 |
| 2   | Próximo (botão) | `/tenants/onboarding/step/3/` | `tenants:onboarding_step_3` | Step 3 |

### Auditoria Design System

| Item                  | Status       | Observação              |
| --------------------- | ------------ | ----------------------- |
| Template base correto | ⏳ Verificar | Usa template standalone |
| Sidebar visível       | N/A          | Wizard standalone       |
| Navegação funcional   | ⏳ Verificar | Stepper visual          |
| Responsividade        | ⏳ Verificar | CSS customizado         |
| Padrões visuais       | ⏳ Verificar | Cores `#a98f71`         |

---

## Página 3: Step 3 - Configuração

### Informações Básicas

| Campo             | Valor                                     |
| ----------------- | ----------------------------------------- |
| **Nome**          | Onboarding Step 3 - Config                |
| **URL**           | `/tenants/onboarding/step/3/`             |
| **URL Name**      | `tenants:onboarding_step_3`               |
| **View**          | `Step3ConfigView` (Class-Based, FormView) |
| **Template**      | `tenants/onboarding/step_3_config.html`   |
| **Template Base** | `tenants/onboarding/base.html`            |
| **App**           | `tenants`                                 |
| **Arquivo View**  | `app/tenants/views/onboarding.py:71-87`   |

### Comportamento

| Ação             | Resultado                        |
| ---------------- | -------------------------------- |
| Config submetida | Atualiza configurações do Tenant |
| Sucesso          | Redireciona para Step 4          |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ❌ Não requerida                           |
| **Roles Permitidos** | 🌐 Todos (público)                         |
| **Módulo**           | N/A                                        |
| **Decorator/Mixin**  | `OnboardingSessionMixin` (verifica sessão) |

### Links da Página

| #   | Nome do Link    | URL de Destino                | URL Name                    | Resumo |
| --- | --------------- | ----------------------------- | --------------------------- | ------ |
| 1   | Voltar (botão)  | `/tenants/onboarding/step/2/` | `tenants:onboarding_step_2` | Step 2 |
| 2   | Próximo (botão) | `/tenants/onboarding/step/4/` | `tenants:onboarding_step_4` | Step 4 |

### Auditoria Design System

| Item                  | Status       | Observação              |
| --------------------- | ------------ | ----------------------- |
| Template base correto | ⏳ Verificar | Usa template standalone |
| Sidebar visível       | N/A          | Wizard standalone       |
| Navegação funcional   | ⏳ Verificar | Stepper visual          |
| Responsividade        | ⏳ Verificar | CSS customizado         |
| Padrões visuais       | ⏳ Verificar | Cores `#a98f71`         |

---

## Página 4: Step 4 - Provisionamento

### Informações Básicas

| Campo             | Valor                                            |
| ----------------- | ------------------------------------------------ |
| **Nome**          | Onboarding Step 4 - Pronto                       |
| **URL**           | `/tenants/onboarding/step/4/`                    |
| **URL Name**      | `tenants:onboarding_step_4`                      |
| **View**          | `Step4ProvisionView` (Class-Based, TemplateView) |
| **Template**      | `tenants/onboarding/step_4_provision.html`       |
| **Template Base** | `tenants/onboarding/base.html`                   |
| **App**           | `tenants`                                        |
| **Arquivo View**  | `app/tenants/views/onboarding.py:90-114`         |

### Comportamento

| Ação        | Resultado                                 |
| ----------- | ----------------------------------------- |
| POST (AJAX) | Ativa tenant e retorna `redirect_url`     |
| Sucesso     | Limpa sessão e redireciona para dashboard |
| Erro        | Retorna JSON com erro                     |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ❌ Não requerida                           |
| **Roles Permitidos** | 🌐 Todos (público)                         |
| **Módulo**           | N/A                                        |
| **Decorator/Mixin**  | `OnboardingSessionMixin` (verifica sessão) |

### Links da Página

| #   | Nome do Link           | URL de Destino | URL Name | Resumo                           |
| --- | ---------------------- | -------------- | -------- | -------------------------------- |
| 1   | Finalizar (botão AJAX) | Dinâmico       | N/A      | Redireciona após provisionamento |

### Auditoria Design System

| Item                  | Status       | Observação              |
| --------------------- | ------------ | ----------------------- |
| Template base correto | ⏳ Verificar | Usa template standalone |
| Sidebar visível       | N/A          | Wizard standalone       |
| Navegação funcional   | ⏳ Verificar | Stepper visual          |
| Responsividade        | ⏳ Verificar | CSS customizado         |
| Padrões visuais       | ⏳ Verificar | Cores `#a98f71`         |

---

## API: Check Slug

### Informações Básicas

| Campo            | Valor                                     |
| ---------------- | ----------------------------------------- |
| **Nome**         | API - Verificar Slug                      |
| **URL**          | `/tenants/api/onboarding/check-slug/`     |
| **URL Name**     | `tenants:api_check_slug`                  |
| **View**         | `CheckSlugView` (Class-Based, View)       |
| **Tipo**         | API JSON                                  |
| **App**          | `tenants`                                 |
| **Arquivo View** | `app/tenants/views/onboarding.py:117-137` |

### Comportamento

| Parâmetro       | Resposta                                       |
| --------------- | ---------------------------------------------- |
| `?slug=<value>` | `{"available": true/false, "slug": "<value>"}` |
| Slug reservado  | `{"available": false, "message": "Reservado"}` |

### Slugs Reservados

`admin`, `api`, `www`, `app`, `painel`, `dashboard`, `public`, `static`, `media`, `tenant`, `setup`

### Permissões

| Tipo             | Valor            |
| ---------------- | ---------------- |
| **Autenticação** | ❌ Não requerida |
| **Decorator**    | `@never_cache`   |

---

## Redirecionamentos do Módulo

| Origem                                  | Destino                       | Condição                   | View                     |
| --------------------------------------- | ----------------------------- | -------------------------- | ------------------------ |
| `/tenants/onboarding/` (sucesso)        | `/tenants/onboarding/step/2/` | Form válido                | `Step1TenantView`        |
| `/tenants/onboarding/step/2/` (sucesso) | `/tenants/onboarding/step/3/` | Plano selecionado          | `Step2PaymentView`       |
| `/tenants/onboarding/step/3/` (sucesso) | `/tenants/onboarding/step/4/` | Config OK                  | `Step3ConfigView`        |
| `/tenants/onboarding/step/4/` (sucesso) | Dashboard do Tenant           | Provisionamento OK         | `Step4ProvisionView`     |
| Qualquer step (sem sessão)              | `/tenants/onboarding/`        | Sem `onboarding_tenant_id` | `OnboardingSessionMixin` |

---

## Pontos de Atenção Identificados

### 🟡 Observações

1. **Template Standalone** - O wizard usa template completamente independente (`onboarding/base.html`), não herda de `base_public.html`
2. **Validação de Sessão** - Steps 2-4 requerem `OnboardingSessionMixin` para garantir fluxo sequencial

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas
- [ ] Template base auditado
- [ ] Redirecionamentos documentados
- [ ] **APROVADO PELO USUÁRIO**
