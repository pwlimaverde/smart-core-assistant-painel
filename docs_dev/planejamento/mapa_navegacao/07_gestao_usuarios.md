# Módulo 7 - Gestão de Usuários

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                                             |
| -------------------- | ------------------------------------------------- |
| **Total de Páginas** | 5                                                 |
| **Template Base**    | Variado (`base_tenants.html`, `base_public.html`) |
| **Autenticação**     | Variado (algumas públicas)                        |
| **App**              | `tenants`                                         |

---

## Página 1: Lista de Usuários

### Informações Básicas

| Campo             | Valor                                |
| ----------------- | ------------------------------------ |
| **Nome**          | Lista de Usuários                    |
| **URL**           | `/tenants/users/`                    |
| **URL Name**      | `tenants:user_list`                  |
| **View**          | `list_users` (Function-Based)        |
| **Template**      | `tenants/users/list.html`            |
| **Template Base** | `base_tenants.html`                  |
| **App**           | `tenants`                            |
| **Arquivo View**  | `app/tenants/views/invites.py:16-63` |

### Permissões

| Tipo                 | Valor                                    |
| -------------------- | ---------------------------------------- |
| **Autenticação**     | ✅ Requerida                             |
| **Roles Permitidos** | `ADMIN` (Owner do tenant)                |
| **Módulo**           | N/A                                      |
| **Decorator/Mixin**  | `@login_required` + verificação de owner |

### Dados Exibidos

- Lista de `TenantUser` do tenant
- Lista de `TenantInvite` pendentes
- Status de cada usuário/convite

### Links da Página

| #   | Nome do Link      | URL de Destino                         | URL Name                     | Resumo            |
| --- | ----------------- | -------------------------------------- | ---------------------------- | ----------------- |
| 1   | Convidar Usuário  | `/tenants/users/invite/`               | `tenants:user_invite`        | Novo convite      |
| 2   | Editar Permissões | `/tenants/users/<id>/permissions/`     | `tenants:user_permissions`   | Editar permissões |
| 3   | Reenviar Convite  | `/tenants/users/invite/<uuid>/resend/` | `tenants:user_invite_resend` | Reenviar email    |
| 4   | Dashboard         | `/tenants/dashboard/`                  | `tenants:dashboard`          | Voltar            |

### Auditoria Design System

| Item                  | Status       | Observação          |
| --------------------- | ------------ | ------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html` |
| Sidebar visível       | ⏳ Verificar | Navegação           |
| Navegação funcional   | ⏳ Verificar | Ações por usuário   |
| Responsividade        | ⏳ Verificar | Tabela de usuários  |
| Padrões visuais       | ⏳ Verificar | Badges, botões      |

---

## Página 2: Convidar Usuário

### Informações Básicas

| Campo             | Valor                                 |
| ----------------- | ------------------------------------- |
| **Nome**          | Convidar Funcionário                  |
| **URL**           | `/tenants/users/invite/`              |
| **URL Name**      | `tenants:user_invite`                 |
| **View**          | `invite_user` (Function-Based)        |
| **Template**      | `tenants/users/invite.html`           |
| **Template Base** | `base_tenants.html`                   |
| **App**           | `tenants`                             |
| **Arquivo View**  | `app/tenants/views/invites.py:66-157` |

### Permissões

| Tipo                 | Valor                                    |
| -------------------- | ---------------------------------------- |
| **Autenticação**     | ✅ Requerida                             |
| **Roles Permitidos** | `ADMIN` (Owner do tenant)                |
| **Módulo**           | N/A                                      |
| **Decorator/Mixin**  | `@login_required` + verificação de owner |

### Formulário

| Campo   | Nome      | Tipo       | Obrigatório |
| ------- | --------- | ---------- | ----------- |
| Nome    | `name`    | text       | ✅          |
| Email   | `email`   | email      | ✅          |
| Módulos | `modules` | checkboxes | ❌          |

### Comportamento

| Ação            | Resultado                         |
| --------------- | --------------------------------- |
| Convite enviado | Cria `TenantInvite` + envia email |
| Email já existe | Erro                              |
| Sucesso         | Redireciona para lista            |

### Links da Página

| #   | Nome do Link | URL de Destino    | URL Name            | Resumo         |
| --- | ------------ | ----------------- | ------------------- | -------------- |
| 1   | Cancelar     | `/tenants/users/` | `tenants:user_list` | Voltar à lista |

### Auditoria Design System

| Item                  | Status       | Observação          |
| --------------------- | ------------ | ------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html` |
| Sidebar visível       | ⏳ Verificar | Navegação           |
| Navegação funcional   | ⏳ Verificar | Botões              |
| Responsividade        | ⏳ Verificar | Formulário          |
| Padrões visuais       | ⏳ Verificar | Checkboxes módulos  |

---

## Página 3: Editar Permissões

### Informações Básicas

| Campo             | Valor                                   |
| ----------------- | --------------------------------------- |
| **Nome**          | Editar Permissões                       |
| **URL**           | `/tenants/users/<user_id>/permissions/` |
| **URL Name**      | `tenants:user_permissions`              |
| **View**          | `edit_permissions` (Function-Based)     |
| **Template**      | `tenants/users/edit_permissions.html`   |
| **Template Base** | `base_tenants.html`                     |
| **App**           | `tenants`                               |
| **Arquivo View**  | `app/tenants/views/invites.py:350-441`  |

### Parâmetros de URL

| Parâmetro | Tipo | Descrição     |
| --------- | ---- | ------------- |
| `user_id` | int  | ID do usuário |

### Permissões

| Tipo                 | Valor                                    |
| -------------------- | ---------------------------------------- |
| **Autenticação**     | ✅ Requerida                             |
| **Roles Permitidos** | `ADMIN` (Owner do tenant)                |
| **Módulo**           | N/A                                      |
| **Decorator/Mixin**  | `@login_required` + verificação de owner |

### Formulário

| Campo   | Nome      | Tipo       | Descrição                |
| ------- | --------- | ---------- | ------------------------ |
| Módulos | `modules` | checkboxes | `TenantModule.choices()` |

### Links da Página

| #   | Nome do Link | URL de Destino    | URL Name            | Resumo         |
| --- | ------------ | ----------------- | ------------------- | -------------- |
| 1   | Cancelar     | `/tenants/users/` | `tenants:user_list` | Voltar à lista |

### Auditoria Design System

| Item                  | Status       | Observação          |
| --------------------- | ------------ | ------------------- |
| Template base correto | ⏳ Verificar | `base_tenants.html` |
| Sidebar visível       | ⏳ Verificar | Navegação           |
| Navegação funcional   | ⏳ Verificar | Botões              |
| Responsividade        | ⏳ Verificar | Formulário          |
| Padrões visuais       | ⏳ Verificar | Checkboxes          |

---

## Página 4: Ativar Conta (Pública)

### Informações Básicas

| Campo             | Valor                                  |
| ----------------- | -------------------------------------- |
| **Nome**          | Ativar Conta                           |
| **URL**           | `/tenants/activate/<token>/`           |
| **URL Name**      | `tenants:activate_account`             |
| **View**          | `activate_account` (Function-Based)    |
| **Template**      | `tenants/users/activate.html`          |
| **Template Base** | `base_public.html` (⚠️ verificar)      |
| **App**           | `tenants`                              |
| **Arquivo View**  | `app/tenants/views/invites.py:272-347` |

### Parâmetros de URL

| Parâmetro | Tipo | Descrição                    |
| --------- | ---- | ---------------------------- |
| `token`   | str  | Token de ativação do convite |

### Permissões

| Tipo                 | Valor                             |
| -------------------- | --------------------------------- |
| **Autenticação**     | ❌ Não requerida (página pública) |
| **Roles Permitidos** | 🌐 Todos (público)                |
| **Módulo**           | N/A                               |
| **Decorator/Mixin**  | Nenhum                            |

### Comportamento

| Condição       | Resultado                        |
| -------------- | -------------------------------- |
| Token válido   | Exibe formulário de senha        |
| Token expirado | Exibe página de convite expirado |
| Senha definida | Cria usuário, loga e redireciona |

### Formulário

| Campo     | Nome               | Tipo     | Obrigatório |
| --------- | ------------------ | -------- | ----------- |
| Senha     | `password`         | password | ✅          |
| Confirmar | `password_confirm` | password | ✅          |

### Links da Página

| #   | Nome do Link | URL de Destino     | URL Name | Resumo        |
| --- | ------------ | ------------------ | -------- | ------------- |
| 1   | Fazer Login  | `/usuarios/login/` | `login`  | Ir para login |

### Auditoria Design System

| Item                  | Status       | Observação       |
| --------------------- | ------------ | ---------------- |
| Template base correto | ⏳ Verificar | Deve ser público |
| Sidebar visível       | N/A          | Página pública   |
| Navegação funcional   | ⏳ Verificar | Links            |
| Responsividade        | ⏳ Verificar | Formulário       |
| Padrões visuais       | ⏳ Verificar | Similar a login  |

---

## Página 5: Convite Expirado

### Informações Básicas

| Campo             | Valor                                    |
| ----------------- | ---------------------------------------- |
| **Nome**          | Convite Expirado                         |
| **URL**           | N/A (renderizado por `activate_account`) |
| **URL Name**      | N/A                                      |
| **View**          | `activate_account` (caso de erro)        |
| **Template**      | `tenants/users/invite_expired.html`      |
| **Template Base** | `base_public.html` (⚠️ verificar)        |
| **App**           | `tenants`                                |

### Permissões

| Tipo                 | Valor              |
| -------------------- | ------------------ |
| **Autenticação**     | ❌ Não requerida   |
| **Roles Permitidos** | 🌐 Todos (público) |

### Links da Página

| #   | Nome do Link   | URL de Destino      | URL Name | Resumo     |
| --- | -------------- | ------------------- | -------- | ---------- |
| 1   | Contatar Admin | (texto informativo) | N/A      | Orientação |

### Auditoria Design System

| Item                  | Status       | Observação       |
| --------------------- | ------------ | ---------------- |
| Template base correto | ⏳ Verificar | Deve ser público |
| Sidebar visível       | N/A          | Página pública   |
| Navegação funcional   | ⏳ Verificar | Mínimo           |
| Responsividade        | ⏳ Verificar | Layout simples   |
| Padrões visuais       | ⏳ Verificar | Mensagem de erro |

---

## API: Reenviar Convite

### Informações Básicas

| Campo            | Valor                                       |
| ---------------- | ------------------------------------------- |
| **URL**          | `/tenants/users/invite/<invite_id>/resend/` |
| **URL Name**     | `tenants:user_invite_resend`                |
| **View**         | `resend_invite`                             |
| **Método**       | POST                                        |
| **Arquivo View** | `app/tenants/views/invites.py:160-194`      |

### Permissões

| Tipo                 | Valor           |
| -------------------- | --------------- |
| **Autenticação**     | ✅ Requerida    |
| **Roles Permitidos** | `ADMIN` (Owner) |

---

## Controle de Acesso

### Matriz de Permissões

| Role        | Lista | Convidar | Permissões | Reenviar |
| ----------- | ----- | -------- | ---------- | -------- |
| Owner/Admin | ✅    | ✅       | ✅         | ✅       |
| Manager     | ❌    | ❌       | ❌         | ❌       |
| Staff       | ❌    | ❌       | ❌         | ❌       |
| Viewer      | ❌    | ❌       | ❌         | ❌       |

### Páginas Públicas

| Página           | Autenticação |
| ---------------- | ------------ |
| Ativar Conta     | ❌ Público   |
| Convite Expirado | ❌ Público   |

---

## Redirecionamentos do Módulo

| Origem            | Destino         | Condição       |
| ----------------- | --------------- | -------------- |
| Convite enviado   | Lista           | Sucesso        |
| Permissões salvas | Lista           | Sucesso        |
| Conta ativada     | Dashboard       | Sucesso        |
| Token expirado    | Página expirado | Token inválido |

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas (owner only)
- [ ] Template base auditado
- [ ] Páginas públicas identificadas
- [ ] **APROVADO PELO USUÁRIO**
