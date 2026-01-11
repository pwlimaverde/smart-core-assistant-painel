## ADDED Requirements

### Requirement: Seção Gestão Visível Apenas para Admins
A seção "Gestão" contendo o link "Usuários" SHALL ser visível apenas para usuários com role "admin" ou que sejam owner do tenant.

#### Scenario: Admin visualiza seção Gestão
- **WHEN** usuário autenticado com role "admin" no tenant visualiza a sidebar
- **THEN** seção "Gestão" com link "Usuários" está visível

#### Scenario: Funcionário não visualiza seção Gestão
- **WHEN** usuário autenticado com role "staff" no tenant visualiza a sidebar
- **THEN** seção "Gestão" NÃO está visível

#### Scenario: Owner visualiza seção Gestão
- **WHEN** usuário que é owner do tenant visualiza a sidebar
- **THEN** seção "Gestão" com link "Usuários" está visível

---

### Requirement: Seção Configurações Baseada em Permissões de Módulo
A seção "Configurações" SHALL ser visível apenas para usuários que tenham permissão no módulo "configuracoes" ou role "admin".

#### Scenario: Admin visualiza seção Configurações
- **WHEN** usuário autenticado com role "admin" no tenant visualiza a sidebar
- **THEN** seção "Configurações" está visível com todos os links

#### Scenario: Usuário com permissão visualiza seção Configurações
- **WHEN** usuário com module_permissions contendo "configuracoes.view=true" visualiza a sidebar
- **THEN** seção "Configurações" está visível

#### Scenario: Usuário sem permissão não visualiza seção Configurações
- **WHEN** usuário com module_permissions vazio e role diferente de "admin" visualiza a sidebar
- **THEN** seção "Configurações" NÃO está visível

---

### Requirement: Link Painel Admin Apenas para Staff
O link "Painel Admin" que direciona para `/tenant-admin/` SHALL ser visível apenas para usuários com `is_staff=True`.

#### Scenario: Staff visualiza link Painel Admin
- **WHEN** usuário autenticado com is_staff=True visualiza a sidebar
- **THEN** link "Painel Admin" está visível

#### Scenario: Usuário comum não visualiza link Painel Admin
- **WHEN** usuário autenticado com is_staff=False visualiza a sidebar
- **THEN** link "Painel Admin" NÃO está visível

---

## MODIFIED Requirements

### Requirement: Link Dashboard Direciona Corretamente
O link "Dashboard" na sidebar SHALL direcionar para a página principal do tenant (`/tenants/dashboard/`).

#### Scenario: Clique em Dashboard direciona corretamente
- **WHEN** usuário autenticado clica no link "Dashboard" na sidebar
- **THEN** navegador direciona para "/tenants/dashboard/" e NÃO para "/dashboard/"
