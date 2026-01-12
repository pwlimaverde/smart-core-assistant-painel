# Tasks: Refactor UI Design System (Screen-Based)

Este documento lista as tarefas para a refatoração do UI Design System, organizado por telas.

**Protocolos de Execução**:

1. Nenhuma task deve ser marcada como concluída sem validação manual explícita.
2. **Documentação Incremental**: Ao concluir cada módulo, atualizar imediatamente o `UI_MAP.md` com as telas auditadas. Isso evita perda de contexto.

---

## Módulo 1: Páginas Públicas e de Erro

### 1.1 Landing Page (`/`)

- [ ] **Análise Funcional**: Página inicial pública da aplicação.
- [ ] **Padronização Visual**: Verificar se usa `base_public.html` ou equivalente.
- [ ] **Auditoria de Links**:
  - [ ] [Login] -> `/usuarios/login/`.
  - [ ] [Cadastre-se/Experimente] -> `/tenants/signup/` ou `/tenants/onboarding/`.
- [ ] **Validação Manual**: Acessar como anônimo.

### 1.2 Páginas de Erro (403, 404, 500)

- [ ] **Análise Funcional**: Páginas de erro customizadas.
- [ ] **Padronização Visual**:
  - [ ] Mensagem clara e amigável.
  - [ ] Botão "Voltar ao Início" ou "Dashboard".
- [ ] **Validação Manual**: Forçar cada erro e verificar layout.

### 1.3 Subscription Expired

- [ ] **Análise Funcional**: Aviso de assinatura expirada.
- [ ] **Padronização Visual**: Call-to-action para renovar.
- [ ] **Validação Manual**: Verificar exibição quando subscription.is_active() == False.

### 1.4 Tenant Not Found

- [ ] **Análise Funcional**: Erro ao acessar slug inválido.
- [ ] **Padronização Visual**: Mensagem clara.
- [ ] **Validação Manual**: Acessar URL com slug inexistente.

### 1.5 📝 Atualizar UI_MAP.md

- [ ] Documentar todas as telas do Módulo 1 no `UI_MAP.md`.

---

## Módulo 2: Backoffice (Super Admin)

### 2.1 Dashboard Backoffice (`/tenants/bo/`)

- [ ] **Análise Funcional**: Visão geral de todos os tenants.
- [ ] **Padronização Visual**: Tabela de tenants com status.
- [ ] **Auditoria de Permissões**: ESTRITAMENTE Superuser.
- [ ] **Validação Manual**: Listar e filtrar tenants.

### 2.2 Registrar Pagamento (`/tenants/bo/tenant/<pk>/register-payment/`)

- [ ] **Análise Funcional**: Formulário para registro manual de pagamento.
- [ ] **Padronização Visual**: Campos claros (Valor, Método, Período).
- [ ] **Auditoria de Permissões**: ESTRITAMENTE Superuser.
- [ ] **Validação Manual**: Registrar pagamento e verificar atualização de subscription.

### 2.3 📝 Atualizar UI_MAP.md

- [ ] Documentar todas as telas do Módulo 2 no `UI_MAP.md`.

---

## Módulo 3: Autenticação & Onboarding

### 3.1 Tela de Login (`/usuarios/login/`)

- [ ] **Análise Funcional**: Garantir fluxo de entrada e redirecionamento.
- [ ] **Padronização Visual**:
  - [ ] Verificar layout centralizado ou split-screen padrão.
  - [ ] Inputs e botões com estilos do Design System.
  - [ ] Feedback de erro visualmente consistente.
- [ ] **Auditoria de Links**:
  - [ ] [Esqueci minha senha] -> Fluxo de recuperação (Verificar se existe/funciona).
  - [ ] [Cadastre-se] -> `/tenants/signup/`.
- [ ] **Auditoria de Permissões**: Simular login como Admin e Staff.
- [ ] **Validação Manual**: Redirecionamento correto para Dashboard ou Admin após login.

### 3.2 Tela de Signup (`/tenants/signup/`)

- [ ] **Análise Funcional**: Criação de nova conta/tenant.
- [ ] **Padronização Visual**: Consistência com tela de login.
- [ ] **Auditoria de Links**:
  - [ ] [Login] -> `/usuarios/login/`.
  - [ ] [Submit] -> Processa form e redireciona.
- [ ] **Validação Manual**: Criar um tenant de teste.

### 3.3 Cadastro de Usuário (`/usuarios/cadastro/`)

- [ ] **Análise Funcional**: Verificar propósito (possível legado ou alternativa ao signup).
- [ ] **Padronização Visual**: Consistência com Login/Signup.
- [ ] **Decisão**: Deprecar se redundante com `/tenants/signup/`.

### 3.4 Fluxo de Onboarding (`/tenants/onboarding/`)

- [ ] **Análise Funcional**: Wizard de configuração inicial (Steps 1-4).
- [ ] **Padronização Visual**:
  - [ ] Stepper visual no topo/lateral.
  - [ ] Formulários consistentes.
- [ ] **Auditoria de Permissões**: Apenas Owner deve acessar. Tentar acessar com outro user.
- [ ] **Validação Manual**: Completar o wizard do início ao fim.

### 3.5 📝 Atualizar UI_MAP.md

- [ ] Documentar todas as telas do Módulo 3 no `UI_MAP.md`.

---

## Módulo 4: Dashboards Principais

### 4.1 Tenant Dashboard (`/tenants/dashboard/`)

- [ ] **Análise Funcional**: Visão geral do tenant.
- [ ] **Padronização Visual**:
  - [ ] **Sidebar**: Deve estar presente e funcional.
  - [ ] **Header**: Breadcrumbs e Menu de Usuário.
  - [ ] **Cards**: Altura padronizada (`h-full`), ícones e tipografia corretos.
- [ ] **Auditoria de Links**:
  - [ ] [Card Treinamentos] -> `/treinamento/verificar-treinamentos/`.
  - [ ] [Card Queries] -> `/treinamento/cadastrar-query-compose/`.
  - [ ] [Sidebar Links]: Testar todos.
- [ ] **Auditoria de Permissões**:
  - [ ] Admin: Vê tudo.
  - [ ] Staff (sem permissão): Cards restritos devem sumir ou desabilitar.
- [ ] **Validação Manual**: Testar layout em Desktop.

### 4.2 Dashboard Gerente (`/usuarios/dashboard-gerente/`)

- [ ] **Análise Funcional**: Verificar propósito (provável legado ou view específica).
- [ ] **Padronização Visual**: Aplicar `base_dashboard.html` se ainda não usar.
- [ ] **Auditoria de Links**: Validar ações disponíveis.
- [ ] **Auditoria de Permissões**: Apenas Role 'manager' ou 'admin'.
- [ ] **Validação Manual**: Acesso negado para 'staff'.

### 4.3 📝 Atualizar UI_MAP.md

- [ ] Documentar todas as telas do Módulo 4 no `UI_MAP.md`.

---

## Módulo 5: Configurações do Tenant

### 5.1 Configuração Database (`/tenants/config/database/`)

- [ ] **Análise Funcional**: Conexão com banco de dados do cliente.
- [ ] **Padronização Visual**: Exibição segura de status (conectado/desconectado).
- [ ] **Auditoria de Links**:
  - [ ] [Testar Conexão] -> Feedback imediato.
  - [ ] [Salvar] -> Feedback de sucesso.
- [ ] **Auditoria de Permissões**: Apenas Admin/Manager (permissão `configuracoes`).
- [ ] **Validação Manual**: Testar conexão dummy e real.

### 5.2 Configuração Evolution (`/tenants/config/evolution/`)

- [ ] **Análise Funcional**: Conexão WhatsApp.
- [ ] **Padronização Visual**: QR Code (se houver) ou status da instância.
- [ ] **Auditoria de Permissões**: Apenas Admin/Manager (permissão `configuracoes`).

### 5.3 Configuração Trello (`/tenants/config/trello/`)

- [ ] **Análise Funcional**: Integração com Trello.
- [ ] **Padronização Visual**: Status de webhook.
- [ ] **Auditoria de Permissões**: Apenas Admin/Manager (permissão `configuracoes`).

### 5.4 Configuração AI (`/tenants/config/ai/`)

- [ ] **Análise Funcional**: Personalização de persona e prompts.
- [ ] **Padronização Visual**: Formulário de texto extenso bem formatado.
- [ ] **Auditoria de Permissões**: Apenas Admin/Manager (permissão `configuracoes`).

### 5.5 Configuração Debug (`/tenants/config/debug/`)

- [ ] **Análise Funcional**: Diagnóstico técnico.
- [ ] **Padronização Visual**: Informações técnicas de forma legível.
- [ ] **Auditoria de Permissões**: Apenas Admin (verificar se deve ser restrito a superuser).

### 5.6 📝 Atualizar UI_MAP.md

- [ ] Documentar todas as telas do Módulo 5 no `UI_MAP.md`.

---

## Módulo 6: Treinamento (IA)

### 6.1 Treinar IA (`/treinamento/treinar-ia/`)

- [ ] **Análise Funcional**: Upload e processamento de arquivos.
- [ ] **Padronização Visual**:
  - [ ] Corrigir herança (`base_dashboard.html`).
  - [ ] Sidebar visível.
- [ ] **Auditoria de Links**:
  - [ ] [Upload/Processar] -> Feedback visual de carregamento.
- [ ] **Auditoria de Permissões**: Requer permissão `treinamento`.
- [ ] **Validação Manual**: Realizar um treino simples.

### 6.2 Pre-processamento (`/treinamento/pre-processamento/<id>/`)

- [ ] **Análise Funcional**: Visualização/edição de documento antes de treinar.
- [ ] **Padronização Visual**: Sidebar presente, preview de texto.
- [ ] **Auditoria de Permissões**: Requer permissão `treinamento`.
- [ ] **Validação Manual**: Acessar documento existente.

### 6.3 Verificar Treinamentos (`/treinamento/verificar-treinamentos/`)

- [ ] **Análise Funcional**: Listagem de conteúdos vetorizados.
- [ ] **Padronização Visual**: Tabela de dados (DataGrid/Table) padronizada.
- [ ] **Auditoria de Links**:
  - [ ] [Detalhes/Editar] -> Abre modal ou nova tela?
  - [ ] [Paginação] -> Funciona?
- [ ] **Auditoria de Permissões**: Requer permissão `treinamento`.
- [ ] **Validação Manual**: Navegar entre páginas da tabela.

### 6.4 Cadastrar Query Compose (`/treinamento/cadastrar-query-compose/`)

- [ ] **Análise Funcional**: Cadastro de queries manuais.
- [ ] **Padronização Visual**: Formulários alinhados e sidebar presente.
- [ ] **Auditoria de Permissões**: Requer permissão `treinamento`.
- [ ] **Validação Manual**: Cadastrar uma query de teste.

### 6.5 Verificar Query Compose (`/treinamento/verificar-query-compose/`)

- [ ] **Análise Funcional**: Listagem de queries cadastradas.
- [ ] **Padronização Visual**: Tabela/cards consistentes.
- [ ] **Auditoria de Permissões**: Requer permissão `treinamento`.
- [ ] **Validação Manual**: Navegar e editar uma query.

### 6.6 📝 Atualizar UI_MAP.md

- [ ] Documentar todas as telas do Módulo 6 no `UI_MAP.md`.

---

## Módulo 7: Gestão de Usuários

### 7.1 Lista de Usuários (`/tenants/users/`)

- [ ] **Análise Funcional**: Listagem e gestão de membros da equipe.
- [ ] **Padronização Visual**: Tabela de usuários. Botão "Convidar" destacado.
- [ ] **Auditoria de Links**:
  - [ ] [Convidar] -> Modal ou tela `/users/invite/`.
  - [ ] [Editar Permissões] -> `/users/<id>/permissions/`.
- [ ] **Auditoria de Permissões**:
  - [ ] Admin: Vê e edita tudo.
  - [ ] Manager: Pode ver/editar staff (rever regra de negócio).
  - [ ] Staff: Apenas vê ou acesso negado (verificar regra atual).
- [ ] **Validação Manual**: Convidar um usuário e editar permissões.

### 7.2 Edição de Permissões (`/tenants/users/<id>/permissions/`)

- [ ] **Análise Funcional**: Checkboxes de permissões modulares.
- [ ] **Padronização Visual**: Clareza no que está sendo concedido.
- [ ] **Validação Manual**: Alterar permissão e verificar efeito imediato.

### 7.3 Convite de Usuário (`/tenants/users/invite/`)

- [ ] **Análise Funcional**: Formulário para convidar novo membro.
- [ ] **Padronização Visual**: Campos claros (Email, Nome, Role).
- [ ] **Auditoria de Permissões**: Apenas Admin/Manager.
- [ ] **Validação Manual**: Enviar convite e verificar e-mail.

### 7.4 Ativação de Conta (`/tenants/activate/<token>/`)

- [ ] **Análise Funcional**: Tela para definir senha após convite.
- [ ] **Padronização Visual**: Consistência com Login/Signup.
- [ ] **Auditoria de Links**: Verificar redirecionamento pós-ativação.
- [ ] **Validação Manual**: Testar com token válido e expirado.

### 7.5 Convite Expirado

- [ ] **Análise Funcional**: Tela de erro para token expirado.
- [ ] **Padronização Visual**: Mensagem clara e link para solicitar novo convite (se aplicável).

### 7.6 📝 Atualizar UI_MAP.md

- [ ] Documentar todas as telas do Módulo 7 no `UI_MAP.md`.

---

## Finalização

### F.1 Revisão Final do UI_MAP.md

- [ ] **Revisar `UI_MAP.md`**: Consolidar todas as entradas, garantir consistência de formato e completude.

### F.2 Cleanup

- [ ] **Templates obsoletos**: Identificar e remover templates não utilizados.
  - Candidatos: `base_tenants.html`, `config_form.html` (verificar uso).
