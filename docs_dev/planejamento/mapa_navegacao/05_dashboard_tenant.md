# Módulo 5 - Dashboard Tenant

> 📋 **Status**: ✅ Aprovado
> 📅 **Data**: 2026-02-01
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                          |
| -------------------- | ------------------------------ |
| **Total de Páginas** | 1                              |
| **Template Base**    | `tenants/dashboard.html`       |
| **Autenticação**     | ✅ Requerida                   |
| **Permissão**        | Autenticado; cards exigem módulo **configuracoes** |
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
| **Template Base** | `base_dashboard.html`                                                      |
| **App**           | `tenants`                                                                  |
| **Arquivo View**  | `app/tenants/views/legacy_views.py:94-113`                                 |

### Permissões

| Tipo                 | Valor                                                                           |
| -------------------- | ------------------------------------------------------------------------------- |
| **Autenticação**     | ✅ Requerida                                                                    |
| **Roles Permitidos** | Todos os usuários do tenant (conteúdo varia por permissões de módulo)          |
| **Módulo**           | **configuracoes** controla exibição de cards e menu de configurações            |
| **Decorator/Mixin**  | `LoginRequiredMixin`                                                            |

### Contexto Exibido

| Variável       | Descrição                         |
| -------------- | --------------------------------- |
| `tenant`       | Objeto Tenant atual               |
| `subscription` | Assinatura do tenant              |
| `config`       | Configurações do tenant           |
| Estatísticas   | Métricas de uso (se implementado) |

### Links da Página (Previstos)

| #   | Nome do Link         | URL de Destino               | URL Name                   | Resumo            | Condição |
| --- | -------------------- | ---------------------------- | -------------------------- | ----------------- | -------- |
| 1   | Configurar Database  | `/tenants/config/database/`  | `tenants:config_database`  | Config PostgreSQL | owner ou **configuracoes** |
| 2   | Configurar Evolution | `/tenants/config/evolution/` | `tenants:config_evolution` | Config WhatsApp   | owner ou **configuracoes** |
| 3   | Configurar Trello    | `/tenants/config/trello/`    | `tenants:config_trello`    | Config Trello     | owner ou **configuracoes** |
| 4   | Configurar IA        | `/tenants/config/ai/`        | `tenants:config_ai`        | Config IA/Prompts | owner ou **configuracoes** |
| 5   | Debug Config         | `/tenants/config/debug/`     | `tenants:config_debug`     | Verificar configs | owner ou **configuracoes** |

### Auditoria Design System

| Item                  | Status       | Observação                               |
| --------------------- | ------------ | ---------------------------------------- |
| Template base correto | ✅ Verificado | Usa `base_dashboard.html`                |
| Sidebar visível       | ✅ Verificado | Navegação lateral ativa                  |
| Navegação funcional   | ✅ Verificado | Links e permissões ajustados             |
| Responsividade        | ✅ Verificado | Layout adaptável                         |
| Padrões visuais       | ✅ Verificado | Cards e padrão visual OK                 |

---

## Controle de Acesso

### Matriz de Permissões (Resumo)

| Perfil                         | Conteúdo exibido |
| ----------------------------- | ---------------- |
| Owner                         | Dashboard + cards + menu configurações |
| Usuário com **configuracoes** | Dashboard + cards + menu configurações |
| Usuário sem **configuracoes** | Mensagem "Sem acesso às configurações" |
| Usuário sem módulos           | Mensagem "Acesso limitado" |

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

### ✅ Sem issues críticas

---

## Checklist de Validação do Módulo

- [x] Todas as páginas documentadas
- [x] Todos os links mapeados
- [x] Permissões verificadas
- [x] Template base auditado
- [x] Sidebar funcional
- [x] Redirecionamentos documentados
- [x] **APROVADO PELO USUÁRIO**
