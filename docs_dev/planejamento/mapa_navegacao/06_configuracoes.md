# Módulo 6 - Configurações

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                                       |
| -------------------- | ------------------------------------------- |
| **Total de Páginas** | 5                                           |
| **Template Base**    | `base_tenants.html` → `base_dashboard.html` |
| **Autenticação**     | ✅ Requerida                                |
| **Permissão**        | `CONFIGURACOES` ou `ADMIN`/`MANAGER`        |
| **App**              | `tenants`                                   |

---

## Página 1: Configuração de Database

### Informações Básicas

| Campo             | Valor                                          |
| ----------------- | ---------------------------------------------- |
| **Nome**          | Configuração de Database                       |
| **URL**           | `/tenants/config/database/`                    |
| **URL Name**      | `tenants:config_database`                      |
| **View**          | `DatabaseConfigView` (Class-Based, UpdateView) |
| **Template**      | `tenants/config_database.html`                 |
| **Template Base** | `base_tenants.html`                            |
| **App**           | `tenants`                                      |
| **Arquivo View**  | `app/tenants/views/legacy_views.py:252-271`    |
| **Model**         | `TenantDatabase`                               |
| **Form**          | `TenantDatabaseForm`                           |

### Permissões

| Tipo                 | Valor                                            |
| -------------------- | ------------------------------------------------ |
| **Autenticação**     | ✅ Requerida                                     |
| **Roles Permitidos** | `ADMIN`, `MANAGER`                               |
| **Módulo**           | `CONFIGURACOES`                                  |
| **Decorator/Mixin**  | `LoginRequiredMixin`, `TenantOwnerRequiredMixin` |

### Links da Página

| #   | Nome do Link        | URL de Destino                       | URL Name                  | Resumo              |
| --- | ------------------- | ------------------------------------ | ------------------------- | ------------------- |
| 1   | Testar Conexão      | `/tenants/test-connection/database/` | `tenants:test_connection` | API de teste        |
| 2   | Executar Migrations | `/tenants/run-migrations/`           | `tenants:run_migrations`  | Rodar migrations    |
| 3   | Dashboard           | `/tenants/dashboard/`                | `tenants:dashboard`       | Voltar ao dashboard |

### Formulário

| Campo    | Tipo     | Obrigatório | Descrição              |
| -------- | -------- | ----------- | ---------------------- |
| Host     | text     | ✅          | Endereço do PostgreSQL |
| Port     | number   | ✅          | Porta (default: 5432)  |
| Database | text     | ✅          | Nome do banco          |
| User     | text     | ✅          | Usuário                |
| Password | password | ✅          | Senha                  |

### Auditoria Design System

| Item                  | Status       | Observação           |
| --------------------- | ------------ | -------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html`  |
| Sidebar visível       | ⏳ Verificar | Navegação de configs |
| Navegação funcional   | ⏳ Verificar | Links de ação        |
| Responsividade        | ⏳ Verificar | Formulário adaptável |
| Padrões visuais       | ⏳ Verificar | Inputs, botões       |

---

## Página 2: Configuração Evolution (WhatsApp)

### Informações Básicas

| Campo             | Valor                                           |
| ----------------- | ----------------------------------------------- |
| **Nome**          | Configuração Evolution                          |
| **URL**           | `/tenants/config/evolution/`                    |
| **URL Name**      | `tenants:config_evolution`                      |
| **View**          | `EvolutionConfigView` (Class-Based, UpdateView) |
| **Template**      | `tenants/config_evolution.html`                 |
| **Template Base** | `base_tenants.html`                             |
| **App**           | `tenants`                                       |
| **Arquivo View**  | `app/tenants/views/legacy_views.py:200-208`     |
| **Model**         | `TenantEvolution`                               |
| **Form**          | `TenantEvolutionForm`                           |

### Permissões

| Tipo                 | Valor                                            |
| -------------------- | ------------------------------------------------ |
| **Autenticação**     | ✅ Requerida                                     |
| **Roles Permitidos** | `ADMIN`, `MANAGER`                               |
| **Módulo**           | `CONFIGURACOES`                                  |
| **Decorator/Mixin**  | `LoginRequiredMixin`, `TenantOwnerRequiredMixin` |

### Links da Página

| #   | Nome do Link   | URL de Destino                        | URL Name                  | Resumo              |
| --- | -------------- | ------------------------------------- | ------------------------- | ------------------- |
| 1   | Testar Conexão | `/tenants/test-connection/evolution/` | `tenants:test_connection` | API de teste        |
| 2   | Dashboard      | `/tenants/dashboard/`                 | `tenants:dashboard`       | Voltar ao dashboard |

### Auditoria Design System

| Item                  | Status       | Observação          |
| --------------------- | ------------ | ------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html` |
| Sidebar visível       | ⏳ Verificar | Navegação           |
| Navegação funcional   | ⏳ Verificar | Links               |
| Responsividade        | ⏳ Verificar | Formulário          |
| Padrões visuais       | ⏳ Verificar | Inputs, botões      |

---

## Página 3: Configuração Trello

### Informações Básicas

| Campo             | Valor                                        |
| ----------------- | -------------------------------------------- |
| **Nome**          | Configuração Trello                          |
| **URL**           | `/tenants/config/trello/`                    |
| **URL Name**      | `tenants:config_trello`                      |
| **View**          | `TrelloConfigView` (Class-Based, UpdateView) |
| **Template**      | `tenants/config_trello.html`                 |
| **Template Base** | `base_tenants.html`                          |
| **App**           | `tenants`                                    |
| **Arquivo View**  | `app/tenants/views/legacy_views.py:211-237`  |
| **Model**         | `TenantTrello`                               |
| **Form**          | `TenantTrelloForm`                           |

### Permissões

| Tipo                 | Valor                                            |
| -------------------- | ------------------------------------------------ |
| **Autenticação**     | ✅ Requerida                                     |
| **Roles Permitidos** | `ADMIN`, `MANAGER`                               |
| **Módulo**           | `CONFIGURACOES`                                  |
| **Decorator/Mixin**  | `LoginRequiredMixin`, `TenantOwnerRequiredMixin` |

### Links da Página

| #   | Nome do Link      | URL de Destino                      | URL Name                          | Resumo              |
| --- | ----------------- | ----------------------------------- | --------------------------------- | ------------------- |
| 1   | Registrar Webhook | `/tenants/register-trello-webhook/` | `tenants:register_trello_webhook` | Registrar webhook   |
| 2   | Deletar Webhook   | `/tenants/delete-trello-webhook/`   | `tenants:delete_trello_webhook`   | Remover webhook     |
| 3   | Dashboard         | `/tenants/dashboard/`               | `tenants:dashboard`               | Voltar ao dashboard |

### Auditoria Design System

| Item                  | Status       | Observação          |
| --------------------- | ------------ | ------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html` |
| Sidebar visível       | ⏳ Verificar | Navegação           |
| Navegação funcional   | ⏳ Verificar | Links de webhook    |
| Responsividade        | ⏳ Verificar | Formulário          |
| Padrões visuais       | ⏳ Verificar | Inputs, botões      |

---

## Página 4: Configuração IA

### Informações Básicas

| Campo             | Valor                                       |
| ----------------- | ------------------------------------------- |
| **Nome**          | Configuração IA                             |
| **URL**           | `/tenants/config/ai/`                       |
| **URL Name**      | `tenants:config_ai`                         |
| **View**          | `AIConfigView` (Class-Based, UpdateView)    |
| **Template**      | `tenants/config_ai.html`                    |
| **Template Base** | `base_tenants.html`                         |
| **App**           | `tenants`                                   |
| **Arquivo View**  | `app/tenants/views/legacy_views.py:240-249` |
| **Model**         | `TenantConfig`                              |
| **Form**          | `TenantConfigForm`                          |

### Permissões

| Tipo                 | Valor                                            |
| -------------------- | ------------------------------------------------ |
| **Autenticação**     | ✅ Requerida                                     |
| **Roles Permitidos** | `ADMIN`, `MANAGER`                               |
| **Módulo**           | `CONFIGURACOES`                                  |
| **Decorator/Mixin**  | `LoginRequiredMixin`, `TenantOwnerRequiredMixin` |

### Links da Página

| #   | Nome do Link   | URL de Destino             | URL Name                 | Resumo              |
| --- | -------------- | -------------------------- | ------------------------ | ------------------- |
| 1   | Treinamento IA | `/treinamento/treinar-ia/` | `treinamento:treinar_ia` | Treinar IA          |
| 2   | Dashboard      | `/tenants/dashboard/`      | `tenants:dashboard`      | Voltar ao dashboard |

### Auditoria Design System

| Item                  | Status       | Observação          |
| --------------------- | ------------ | ------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html` |
| Sidebar visível       | ⏳ Verificar | Navegação           |
| Navegação funcional   | ⏳ Verificar | Links               |
| Responsividade        | ⏳ Verificar | Formulário          |
| Padrões visuais       | ⏳ Verificar | Textareas, botões   |

---

## Página 5: Debug de Configurações

### Informações Básicas

| Campo             | Valor                                         |
| ----------------- | --------------------------------------------- |
| **Nome**          | Debug de Configurações                        |
| **URL**           | `/tenants/config/debug/`                      |
| **URL Name**      | `tenants:config_debug`                        |
| **View**          | `ConfigDebugView` (Class-Based, TemplateView) |
| **Template**      | `tenants/config_debug.html`                   |
| **Template Base** | `base_tenants.html`                           |
| **App**           | `tenants`                                     |
| **Arquivo View**  | `app/tenants/views/legacy_views.py:354-522`   |

### Permissões

| Tipo                 | Valor                                            |
| -------------------- | ------------------------------------------------ |
| **Autenticação**     | ✅ Requerida                                     |
| **Roles Permitidos** | `ADMIN` (apenas)                                 |
| **Módulo**           | `CONFIGURACOES`                                  |
| **Decorator/Mixin**  | `LoginRequiredMixin`, `TenantOwnerRequiredMixin` |

### Informações Exibidas

- Todas as configurações do `RuntimeConfig`
- Status de conexões
- Variáveis de ambiente (mascaradas)
- Configurações Core vs Tenant

### Links da Página

| #   | Nome do Link | URL de Destino        | URL Name            | Resumo              |
| --- | ------------ | --------------------- | ------------------- | ------------------- |
| 1   | Dashboard    | `/tenants/dashboard/` | `tenants:dashboard` | Voltar ao dashboard |

### Auditoria Design System

| Item                  | Status       | Observação          |
| --------------------- | ------------ | ------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html` |
| Sidebar visível       | ⏳ Verificar | Navegação           |
| Navegação funcional   | ⏳ Verificar | Links               |
| Responsividade        | ⏳ Verificar | Tabelas de debug    |
| Padrões visuais       | ⏳ Verificar | Código, valores     |

---

## APIs de Suporte

### Test Connection

| Campo            | Valor                                      |
| ---------------- | ------------------------------------------ |
| **URL**          | `/tenants/test-connection/<service_type>/` |
| **URL Name**     | `tenants:test_connection`                  |
| **View**         | `TestConnectionView`                       |
| **Método**       | POST                                       |
| **service_type** | `database`, `evolution`, `trello`          |

### Run Migrations

| Campo        | Valor                      |
| ------------ | -------------------------- |
| **URL**      | `/tenants/run-migrations/` |
| **URL Name** | `tenants:run_migrations`   |
| **View**     | `RunMigrationsView`        |
| **Método**   | POST                       |

### Register Trello Webhook

| Campo        | Valor                               |
| ------------ | ----------------------------------- |
| **URL**      | `/tenants/register-trello-webhook/` |
| **URL Name** | `tenants:register_trello_webhook`   |
| **View**     | `RegisterTrelloWebhookView`         |
| **Método**   | POST                                |

### Delete Trello Webhook

| Campo        | Valor                             |
| ------------ | --------------------------------- |
| **URL**      | `/tenants/delete-trello-webhook/` |
| **URL Name** | `tenants:delete_trello_webhook`   |
| **View**     | `DeleteTrelloWebhookView`         |
| **Método**   | POST                              |

---

## Controle de Acesso

### Matriz de Permissões

| Role    | Database | Evolution | Trello | AI  | Debug |
| ------- | -------- | --------- | ------ | --- | ----- |
| Admin   | ✅       | ✅        | ✅     | ✅  | ✅    |
| Manager | ✅       | ✅        | ✅     | ✅  | ❌    |
| Staff   | ❌       | ❌        | ❌     | ❌  | ❌    |
| Viewer  | ❌       | ❌        | ❌     | ❌  | ❌    |

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas por role
- [ ] Template base auditado
- [ ] APIs de suporte verificadas
- [ ] **APROVADO PELO USUÁRIO**
