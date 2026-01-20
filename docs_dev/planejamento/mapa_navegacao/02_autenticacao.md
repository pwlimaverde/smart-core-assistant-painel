# Módulo 2 - Autenticação

> 📋 **Status**: [/] Em Andamento
> 📅 **Data**: 2026-01-20
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
| **Template Base** | `base_public.html` (Override)     |
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
| 1   | Crie sua conta    | `/tenants/onboarding/` | `tenants:onboarding_step_1` | Ação principal (Footer)         |
| 2   | Esqueceu a senha? | `#` (não implementado) | N/A                         | Recuperação de senha (pendente) |
| 3   | Voltar (Logo)     | `/`                    | `landing`                   | Retorna para Home               |

### Formulário

| Campo      | Nome          | Tipo        | Obrigatório |
| ---------- | ------------- | ----------- | ----------- |
| Usuário    | `username`    | text        | ✅          |
| Senha      | `senha`       | password    | ✅          |
| Lembrar-me | `remember-me` | checkbox    | ❌          |
| Mostrar    | (JS Toggle)   | button/icon | N/A         |

### Auditoria Design System

| Item                  | Status | Observação                            |
| --------------------- | ------ | ------------------------------------- |
| Template base correto | ✅ OK  | Usa `base_public.html` com override   |
| Sidebar visível       | N/A    | Página pública com Navbar Minimalista |
| Navegação funcional   | ✅ OK  | Links de cadastro e home funcionando  |
| Responsividade        | ✅ OK  | Mobile-first com Tailwind             |
| Padrões visuais       | ✅ OK  | Design Premium (Vidro, Gradientes)    |
| UX/UI Melhorado       | ✅ OK  | Toggle de senha e animação de entrada |

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

| Condição              | Ação                                |
| --------------------- | ----------------------------------- |
| Cadastro bem-sucedido | Redireciona para `/usuarios/login/` |
| Senhas não coincidem  | Exibe mensagem de erro              |
| Usuário já existe     | Exibe mensagem de erro              |

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

| Item                  | Status | Observação                            |
| --------------------- | ------ | ------------------------------------- |
| Template base correto | ✅ OK  | Usa `base_public.html` com override   |
| Sidebar visível       | N/A    | Página pública com Navbar Minimalista |
| Navegação funcional   | ✅ OK  | Link para login funcionando           |
| Responsividade        | ✅ OK  | Mobile-first com Tailwind             |
| Padrões visuais       | ✅ OK  | Design Premium (Vidro, Gradientes)    |
| UX/UI Melhorado       | ✅ OK  | Inputs estilizados e animações        |

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
| Cadastro (POST sucesso) | `/usuarios/login/`  | Cadastro OK        | `cadastro`    |
| Logout                  | `/`                 | Sempre             | `logout_view` |

---

## Pontos de Atenção Identificados

### 🟡 Melhorias Sugeridas

1. **Recuperação de Senha** - Link "Esqueceu a senha?" aponta para `#` (não implementado)
2. **Validação de Email** - Não há campo de email no cadastro (item de regra de negócio)

---

## Checklist de Validação do Módulo

- [x] Login validado e aprovado com novo design
- [x] Cadastro validado com novo design
- [ ] Logout validado
- [x] Template base auditado
- [ ] Redirecionamentos documentados
