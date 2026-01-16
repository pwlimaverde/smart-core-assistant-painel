## ADDED Requirements

### Requirement: Auditoria de Design System por Página

Todas as páginas navegáveis do sistema MUST passar por auditoria de conformidade com o Design System estabelecido.

#### Scenario: Verificação de Template Base

- **Given**: Uma página navegável do sistema
- **When**: A página é renderizada
- **Then**: A página MUST estender o template base correto (`base_public.html` para públicas, `base_dashboard.html` ou `base_tenants.html` para autenticadas)

#### Scenario: Verificação de Sidebar

- **Given**: Uma página na área autenticada
- **When**: A página é renderizada para um usuário autenticado
- **Then**: A sidebar de navegação MUST estar visível e funcional

---

### Requirement: Mapeamento de Links por Página

Todas as páginas MUST ter seus links documentados com nome, destino e resumo.

#### Scenario: Documentação de Links

- **Given**: Uma página do sistema
- **When**: O mapa de navegação é consultado
- **Then**: Todos os links da página MUST estar documentados com nome, URL de destino, URL name Django e resumo

#### Scenario: Validação de Links Funcionais

- **Given**: Uma página renderizada
- **When**: Qualquer link é clicado
- **Then**: O sistema MUST redirecionar para o destino correto sem erro 404

---

### Requirement: Auditoria de Permissões por Página

Cada página MUST ter suas permissões documentadas e validadas por role.

#### Scenario: Documentação de Permissões

- **Given**: Uma página do sistema
- **When**: O mapa de navegação é consultado
- **Then**: O documento MUST constar se autenticação é requerida, quais roles são permitidos, qual módulo relacionado e quais decorators/mixins são usados

#### Scenario: Bloqueio de Acesso Não Autorizado

- **Given**: Uma página protegida
- **When**: Um usuário sem permissão tenta acessar
- **Then**: O sistema MUST retornar erro 403 ou redirecionar para login

---

### Requirement: Validação Sequencial por Módulo

A implementação MUST ser validada módulo a módulo, com aprovação explícita antes de avançar.

#### Scenario: Aprovação de Módulo

- **Given**: Um módulo completamente auditado
- **When**: O usuário revisa as alterações
- **Then**: O usuário MUST aprovar explicitamente antes do próximo módulo ser iniciado

#### Scenario: Bloqueio de Avanço sem Aprovação

- **Given**: Um módulo em implementação
- **When**: Há páginas não aprovadas
- **Then**: O próximo módulo MUST NOT ser iniciado

---

## MODIFIED Requirements

### Requirement: Padronização de Templates de Erro

As páginas de erro (403, 404, 500) MUST usar template base consistente.

#### Scenario: Template de Erro 403

- **Given**: Um usuário tenta acessar página sem permissão
- **When**: O erro 403 é disparado
- **Then**: A página MUST renderizar usando `base_public.html` com estilo consistente

#### Scenario: Template de Erro 404

- **Given**: Um usuário acessa URL inexistente
- **When**: O erro 404 é disparado
- **Then**: A página MUST renderizar usando `base_public.html` com estilo consistente

#### Scenario: Template de Erro 500

- **Given**: Um erro interno ocorre
- **When**: O erro 500 é disparado
- **Then**: A página MUST renderizar usando template mínimo que não depende de contexto Django
