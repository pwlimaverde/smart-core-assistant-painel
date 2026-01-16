# Módulo 1 - Páginas Públicas e Erros

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                           |
| -------------------- | ------------------------------- |
| **Total de Páginas** | 4                               |
| **Template Base**    | `base.html`, `base_public.html` |
| **Autenticação**     | ❌ Não requerida                |
| **Permissões**       | 🌐 Público                      |

---

## Página 1: Landing Page

### Informações Básicas

| Campo             | Valor                           |
| ----------------- | ------------------------------- |
| **Nome**          | Landing Page                    |
| **URL**           | `/`                             |
| **URL Name**      | `landing`                       |
| **View**          | `LandingPageView` (Class-Based) |
| **Template**      | `landing_page.html`             |
| **Template Base** | `base_public.html`              |
| **App**           | `ui.core`                       |
| **Arquivo View**  | `app/ui/core/views.py:101-111`  |

### Comportamento Especial

| Condição                        | Ação                                 |
| ------------------------------- | ------------------------------------ |
| Usuário autenticado + Superuser | Redireciona para `/admin/`           |
| Usuário autenticado + Normal    | Redireciona para `tenants:dashboard` |
| Usuário não autenticado         | Redireciona para `login`             |

> ⚠️ **Nota**: A landing page atual redireciona todos os visitantes para login, pois a landing page principal é externa (Cloudflare Pages).

### Permissões

| Tipo                 | Valor              |
| -------------------- | ------------------ |
| **Autenticação**     | ❌ Não requerida   |
| **Roles Permitidos** | 🌐 Todos (público) |
| **Módulo**           | N/A                |
| **Decorator/Mixin**  | Nenhum             |

### Links da Página

| #   | Nome do Link        | URL de Destino         | URL Name                    | Resumo               |
| --- | ------------------- | ---------------------- | --------------------------- | -------------------- |
| 1   | Acessar Plataforma  | `/usuarios/login/`     | `login`                     | Página de login      |
| 2   | Criar Conta         | `/tenants/onboarding/` | `tenants:onboarding_step_1` | Wizard de onboarding |
| 3   | Começar Agora (CTA) | `/tenants/onboarding/` | `tenants:onboarding_step_1` | Wizard de onboarding |

### Auditoria Design System

| Item                  | Status       | Observação                 |
| --------------------- | ------------ | -------------------------- |
| Template base correto | ⏳ Verificar | Usa `base_public.html`     |
| Sidebar visível       | N/A          | Página pública             |
| Navegação funcional   | ⏳ Verificar | Links verificados          |
| Responsividade        | ⏳ Verificar | Classes Tailwind presentes |
| Padrões visuais       | ⏳ Verificar | Cores `#a98f71`, `#1c1917` |

---

## Página 2: Erro 403 (Acesso Negado)

### Informações Básicas

| Campo             | Valor                                       |
| ----------------- | ------------------------------------------- |
| **Nome**          | Erro 403 - Acesso Negado                    |
| **URL**           | N/A (handler)                               |
| **URL Name**      | N/A                                         |
| **View**          | `custom_permission_denied` (Function-Based) |
| **Template**      | `403.html`                                  |
| **Template Base** | `base.html`                                 |
| **App**           | `ui.core`                                   |
| **Arquivo View**  | `app/ui/core/views.py:176-180`              |
| **Handler**       | `handler403` em `urls.py`                   |

### Permissões

| Tipo                 | Valor                                           |
| -------------------- | ----------------------------------------------- |
| **Autenticação**     | ❌ Não requerida (exibida quando acesso negado) |
| **Roles Permitidos** | 🌐 Todos (é uma página de erro)                 |
| **Módulo**           | N/A                                             |
| **Decorator/Mixin**  | Nenhum                                          |

### Links da Página

| #   | Nome do Link       | URL de Destino     | URL Name  | Resumo          | Condição           |
| --- | ------------------ | ------------------ | --------- | --------------- | ------------------ |
| 1   | Voltar para a Home | `/`                | `landing` | Página inicial  | Sempre             |
| 2   | Fazer Login        | `/usuarios/login/` | `login`   | Página de login | Se não autenticado |

### Auditoria Design System

| Item                  | Status         | Observação                                        |
| --------------------- | -------------- | ------------------------------------------------- |
| Template base correto | ⚠️ **Revisar** | Usa `base.html` - deveria ser `base_public.html`? |
| Sidebar visível       | N/A            | Página de erro                                    |
| Navegação funcional   | ⏳ Verificar   | 2 links                                           |
| Responsividade        | ⏳ Verificar   | Classes Tailwind presentes                        |
| Padrões visuais       | ⏳ Verificar   | Cor `#a98f71`                                     |

---

## Página 3: Erro 404 (Página Não Encontrada)

### Informações Básicas

| Campo             | Valor                                    |
| ----------------- | ---------------------------------------- |
| **Nome**          | Erro 404 - Página Não Encontrada         |
| **URL**           | N/A (handler)                            |
| **URL Name**      | N/A                                      |
| **View**          | `custom_page_not_found` (Function-Based) |
| **Template**      | `404.html`                               |
| **Template Base** | `base.html`                              |
| **App**           | `ui.core`                                |
| **Arquivo View**  | `app/ui/core/views.py:169-173`           |
| **Handler**       | `handler404` em `urls.py`                |

### Permissões

| Tipo                 | Valor                                               |
| -------------------- | --------------------------------------------------- |
| **Autenticação**     | ❌ Não requerida (exibida quando página não existe) |
| **Roles Permitidos** | 🌐 Todos (é uma página de erro)                     |
| **Módulo**           | N/A                                                 |
| **Decorator/Mixin**  | Nenhum                                              |

### Links da Página

| #   | Nome do Link       | URL de Destino | URL Name  | Resumo         |
| --- | ------------------ | -------------- | --------- | -------------- |
| 1   | Voltar para a Home | `/`            | `landing` | Página inicial |

### Auditoria Design System

| Item                  | Status         | Observação                                        |
| --------------------- | -------------- | ------------------------------------------------- |
| Template base correto | ⚠️ **Revisar** | Usa `base.html` - deveria ser `base_public.html`? |
| Sidebar visível       | N/A            | Página de erro                                    |
| Navegação funcional   | ⏳ Verificar   | 1 link                                            |
| Responsividade        | ⏳ Verificar   | Classes Tailwind presentes                        |
| Padrões visuais       | ⏳ Verificar   | Cor `#a98f71`                                     |

---

## Página 4: Erro 500 (Erro Interno)

### Informações Básicas

| Campo             | Valor                                  |
| ----------------- | -------------------------------------- |
| **Nome**          | Erro 500 - Erro Interno do Servidor    |
| **URL**           | N/A (handler)                          |
| **URL Name**      | N/A                                    |
| **View**          | `custom_server_error` (Function-Based) |
| **Template**      | `500.html`                             |
| **Template Base** | `base.html`                            |
| **App**           | `ui.core`                              |
| **Arquivo View**  | `app/ui/core/views.py:183-185`         |
| **Handler**       | `handler500` em `urls.py`              |

### Permissões

| Tipo                 | Valor                                          |
| -------------------- | ---------------------------------------------- |
| **Autenticação**     | ❌ Não requerida (exibida em erro do servidor) |
| **Roles Permitidos** | 🌐 Todos (é uma página de erro)                |
| **Módulo**           | N/A                                            |
| **Decorator/Mixin**  | Nenhum                                         |

### Links da Página

| #   | Nome do Link       | URL de Destino | URL Name  | Resumo         |
| --- | ------------------ | -------------- | --------- | -------------- |
| 1   | Voltar para a Home | `/`            | `landing` | Página inicial |

### Auditoria Design System

| Item                  | Status         | Observação                                        |
| --------------------- | -------------- | ------------------------------------------------- |
| Template base correto | ⚠️ **Revisar** | Usa `base.html` - deveria ser `base_public.html`? |
| Sidebar visível       | N/A            | Página de erro                                    |
| Navegação funcional   | ⏳ Verificar   | 1 link                                            |
| Responsividade        | ⏳ Verificar   | Classes Tailwind presentes                        |
| Padrões visuais       | ⏳ Verificar   | Cor `#a98f71`                                     |

---

## Pontos de Atenção Identificados

### 🔴 Issues Críticos

1. **Templates de Erro usam `base.html`** - Páginas 403, 404, 500 estendem `base.html` em vez de `base_public.html`. Avaliar se isso causa problemas de layout ou dependências de contexto.

### 🟡 Melhorias Sugeridas

1. **Padronizar template base** - Considerar usar `base_public.html` para todas as páginas públicas/erro
2. **Link de Login no 404** - Página 404 não tem link de login como o 403
3. **Consistência visual** - Verificar se todas as páginas de erro seguem mesmo padrão

---

## Redirecionamentos Relacionados

| Origem        | Destino               | Condição              | View                  |
| ------------- | --------------------- | --------------------- | --------------------- |
| `/`           | `/admin/`             | Superuser autenticado | `LandingPageView.get` |
| `/`           | `/tenants/dashboard/` | Usuário autenticado   | `LandingPageView.get` |
| `/`           | `/usuarios/login/`    | Não autenticado       | `LandingPageView.get` |
| `/dashboard/` | `/admin/`             | Superuser             | `dashboard` (core)    |
| `/dashboard/` | `/tenants/dashboard/` | Usuário normal        | `dashboard` (core)    |

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas
- [ ] Template base auditado
- [ ] Redirecionamentos documentados
- [ ] **APROVADO PELO USUÁRIO**
