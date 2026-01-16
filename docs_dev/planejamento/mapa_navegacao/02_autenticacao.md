# Módulo 2 - Autenticação

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                            |
| -------------------- | -------------------------------- |
| **Total de Páginas** | 3                                |
| **Template Base**    | `base_public.html`               |
| **Autenticação**     | ❌ Não requerida (exceto logout) |
| **App**              | `ui.usuarios`                    |

---

## Página 1: Login

### Informações Básicas

| Campo             | Valor                             |
| ----------------- | --------------------------------- |
| **Nome**          | Login                             |
| **URL**           | `/usuarios/login/`                |
| **URL Name**      | `login`                           |
| **View**          | `login` (Function-Based)          |
| **Template**      | `login.html`                      |
| **Template Base** | `base_public.html`                |
| **App**           | `ui.usuarios`                     |
| **Arquivo View**  | `app/ui/usuarios/views.py:76-131` |

### Comportamento Especial

| Condição                                 | Ação                                    |
| ---------------------------------------- | --------------------------------------- |
| Login bem-sucedido + Atendente associado | Redireciona para Kanban do departamento |
| Login bem-sucedido + Sem atendente       | Redireciona para `tenants:dashboard`    |
| Parâmetro `?next=` presente              | Redireciona para URL especificada       |

### Permissões

| Tipo                 | Valor              |
| -------------------- | ------------------ |
| **Autenticação**     | ❌ Não requerida   |
| **Roles Permitidos** | 🌐 Todos (público) |
| **Módulo**           | N/A                |
| **Decorator/Mixin**  | Nenhum             |

### Links da Página

| #   | Nome do Link      | URL de Destino         | URL Name                    | Resumo                          |
| --- | ----------------- | ---------------------- | --------------------------- | ------------------------------- |
| 1   | Crie sua conta    | `/tenants/onboarding/` | `tenants:onboarding_step_1` | Wizard de onboarding            |
| 2   | Esqueceu a senha? | `#` (não implementado) | N/A                         | Recuperação de senha (pendente) |

### Formulário

| Campo      | Nome          | Tipo     | Obrigatório |
| ---------- | ------------- | -------- | ----------- |
| Usuário    | `username`    | text     | ✅          |
| Senha      | `senha`       | password | ✅          |
| Lembrar-me | `remember-me` | checkbox | ❌          |

### Auditoria Design System

| Item                  | Status       | Observação                 |
| --------------------- | ------------ | -------------------------- |
| Template base correto | ✅ OK        | Usa `base_public.html`     |
| Sidebar visível       | N/A          | Página pública             |
| Navegação funcional   | ⏳ Verificar | 2 links                    |
| Responsividade        | ⏳ Verificar | Classes Tailwind presentes |
| Padrões visuais       | ⏳ Verificar | Cores `#a98f71`            |

---

## Página 2: Cadastro

### Informações Básicas

| Campo             | Valor                            |
| ----------------- | -------------------------------- |
| **Nome**          | Cadastro                         |
| **URL**           | `/usuarios/cadastro/`            |
| **URL Name**      | `cadastro`                       |
| **View**          | `cadastro` (Function-Based)      |
| **Template**      | `cadastro.html`                  |
| **Template Base** | `base_public.html`               |
| **App**           | `ui.usuarios`                    |
| **Arquivo View**  | `app/ui/usuarios/views.py:27-73` |

### Comportamento Especial

| Condição              | Ação                                                  |
| --------------------- | ----------------------------------------------------- |
| Cadastro bem-sucedido | Loga o usuário e redireciona para `tenants:dashboard` |
| Senhas não coincidem  | Exibe mensagem de erro                                |
| Usuário já existe     | Exibe mensagem de erro                                |

### Permissões

| Tipo                 | Valor              |
| -------------------- | ------------------ |
| **Autenticação**     | ❌ Não requerida   |
| **Roles Permitidos** | 🌐 Todos (público) |
| **Módulo**           | N/A                |
| **Decorator/Mixin**  | Nenhum             |

### Links da Página

| #   | Nome do Link     | URL de Destino     | URL Name | Resumo          |
| --- | ---------------- | ------------------ | -------- | --------------- |
| 1   | Faça login agora | `/usuarios/login/` | `login`  | Página de login |

### Formulário

| Campo           | Nome              | Tipo     | Obrigatório |
| --------------- | ----------------- | -------- | ----------- |
| Usuário         | `username`        | text     | ✅          |
| Senha           | `senha`           | password | ✅          |
| Confirmar Senha | `confirmar_senha` | password | ✅          |

### Auditoria Design System

| Item                  | Status       | Observação                 |
| --------------------- | ------------ | -------------------------- |
| Template base correto | ✅ OK        | Usa `base_public.html`     |
| Sidebar visível       | N/A          | Página pública             |
| Navegação funcional   | ⏳ Verificar | 1 link                     |
| Responsividade        | ⏳ Verificar | Classes Tailwind presentes |
| Padrões visuais       | ⏳ Verificar | Cores `#a98f71`            |

---

## Página 3: Logout

### Informações Básicas

| Campo             | Valor                              |
| ----------------- | ---------------------------------- |
| **Nome**          | Logout                             |
| **URL**           | `/usuarios/logout/`                |
| **URL Name**      | `logout`                           |
| **View**          | `logout_view` (Function-Based)     |
| **Template**      | N/A (apenas redirecionamento)      |
| **Template Base** | N/A                                |
| **App**           | `ui.usuarios`                      |
| **Arquivo View**  | `app/ui/usuarios/views.py:134-140` |

### Comportamento

| Ação             | Destino                        |
| ---------------- | ------------------------------ |
| Logout executado | Redireciona para `/` (landing) |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ✅ Implícita (só faz sentido para logados) |
| **Roles Permitidos** | 🌐 Todos os autenticados                   |
| **Módulo**           | N/A                                        |
| **Decorator/Mixin**  | Nenhum                                     |

### Links da Página

> N/A - Página apenas executa ação e redireciona

### Auditoria Design System

| Item                  | Status | Observação       |
| --------------------- | ------ | ---------------- |
| Template base correto | N/A    | Sem template     |
| Sidebar visível       | N/A    | Redirecionamento |
| Navegação funcional   | N/A    | Redirecionamento |
| Responsividade        | N/A    | Redirecionamento |
| Padrões visuais       | N/A    | Redirecionamento |

---

## Redirecionamentos do Módulo

| Origem                  | Destino             | Condição           | View          |
| ----------------------- | ------------------- | ------------------ | ------------- |
| Login (POST sucesso)    | Kanban departamento | Tem atendente      | `login`       |
| Login (POST sucesso)    | `tenants:dashboard` | Sem atendente      | `login`       |
| Login (POST sucesso)    | URL em `?next=`     | Parâmetro presente | `login`       |
| Cadastro (POST sucesso) | `tenants:dashboard` | Cadastro OK        | `cadastro`    |
| Logout                  | `/`                 | Sempre             | `logout_view` |

---

## Pontos de Atenção Identificados

### 🟡 Melhorias Sugeridas

1. **Recuperação de Senha** - Link "Esqueceu a senha?" aponta para `#` (não implementado)
2. **Validação de Email** - Não há campo de email no cadastro

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas
- [ ] Template base auditado
- [ ] Redirecionamentos documentados
- [ ] **APROVADO PELO USUÁRIO**
