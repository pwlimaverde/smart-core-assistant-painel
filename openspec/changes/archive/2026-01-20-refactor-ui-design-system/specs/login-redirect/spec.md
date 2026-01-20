## ADDED Requirements

### Requirement: Superusuário Redirecionado para Django Admin
Após login bem-sucedido, usuários com `is_superuser=True` SHALL ser redirecionados para o Django Admin (`/admin/`), pois sua função é gerenciar tenants e configurações macro.

#### Scenario: Superusuário faz login
- **WHEN** usuário com is_superuser=True faz login com credenciais válidas
- **THEN** sistema redireciona para "/admin/" e usuário NÃO vê sidebar de tenant

---

### Requirement: Usuário de Tenant Redirecionado para Dashboard
Após login bem-sucedido, usuários que não são superusuários e pertencem a um tenant SHALL ser redirecionados para o dashboard do tenant.

#### Scenario: Owner de tenant faz login
- **WHEN** usuário que é owner de pelo menos um tenant e não é superusuário faz login
- **THEN** sistema redireciona para "/tenants/dashboard/"

#### Scenario: Funcionário de tenant faz login
- **WHEN** usuário que é TenantUser ativo e não é superusuário nem owner faz login
- **THEN** sistema redireciona para "/tenants/dashboard/"

---

### Requirement: Usuário Sem Tenant Redirecionado para Onboarding
Após login bem-sucedido, usuários que não são superusuários e não pertencem a nenhum tenant SHALL ser redirecionados para o onboarding.

#### Scenario: Usuário sem tenant faz login
- **WHEN** usuário sem tenants associados (não é owner nem TenantUser) e não é superusuário faz login
- **THEN** sistema redireciona para "/tenants/onboarding/" ou exibe mensagem informando que não tem acesso

---

## MODIFIED Requirements

### Requirement: Rota Dashboard Redireciona para Tenant Dashboard
A rota `/dashboard/` (em core/urls.py) SHALL redirecionar para `/tenants/dashboard/` para evitar confusão de navegação.

#### Scenario: Acesso a dashboard redireciona
- **WHEN** usuário autenticado acessa "/dashboard/"
- **THEN** sistema redireciona (HTTP 302) para "/tenants/dashboard/"
