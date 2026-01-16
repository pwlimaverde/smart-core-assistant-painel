# Módulo 8 - Treinamento IA

> 📋 **Status**: ⏳ Pendente Implementação
> 📅 **Data**: 2026-01-15
> 🔗 **Índice**: [00_indice.md](./00_indice.md)

---

## Resumo do Módulo

| Métrica              | Valor                                    |
| -------------------- | ---------------------------------------- |
| **Total de Páginas** | 5                                        |
| **Template Base**    | `base_dashboard.html` (via Tenant Admin) |
| **Autenticação**     | ✅ Requerida                             |
| **Permissão**        | `TREINAMENTO` ou `ADMIN`/`MANAGER`       |
| **App**              | `ui.treinamento`                         |

---

## Página 1: Treinar IA

### Informações Básicas

| Campo             | Valor                                |
| ----------------- | ------------------------------------ |
| **Nome**          | Treinar IA                           |
| **URL**           | `/treinamento/treinar-ia/`           |
| **URL Name**      | `treinamento:treinar_ia`             |
| **View**          | `treinar_ia` (Function-Based)        |
| **Template**      | `treinamento/treinar_ia.html`        |
| **Template Base** | ⚠️ A verificar                       |
| **App**           | `ui.treinamento`                     |
| **Arquivo View**  | `app/ui/treinamento/views.py:69-110` |

### Permissões

| Tipo                 | Valor                                               |
| -------------------- | --------------------------------------------------- |
| **Autenticação**     | ✅ Requerida                                        |
| **Roles Permitidos** | `ADMIN`, `MANAGER`, ou permissão `TREINAMENTO`      |
| **Módulo**           | `TREINAMENTO`                                       |
| **Decorator/Mixin**  | Verificação customizada em `_can_access_training()` |

### Verificação de Acesso (`_can_access_training`)

Retorna `True` se:

- Usuário é `superuser`, OU
- Usuário é Owner de tenant ATIVO, OU
- Usuário tem role `Admin`/`Manager`, OU
- Usuário tem permissão de treinamento

### Formulário

| Campo   | Nome      | Tipo     | Descrição             |
| ------- | --------- | -------- | --------------------- |
| Arquivo | `arquivo` | file     | PDF, TXT, DOCX        |
| Texto   | `texto`   | textarea | Texto livre           |
| Título  | `titulo`  | text     | Título do treinamento |

### Links da Página

| #   | Nome do Link           | URL de Destino                          | URL Name                                         | Resumo                |
| --- | ---------------------- | --------------------------------------- | ------------------------------------------------ | --------------------- |
| 1   | Verificar Treinamentos | `/treinamento/verificar-treinamentos/`  | `treinamento:verificar_treinamentos_vetorizados` | Lista de treinamentos |
| 2   | Query Compose          | `/treinamento/cadastrar-query-compose/` | `treinamento:cadastrar_query_compose`            | Cadastrar intents     |
| 3   | Dashboard              | `/tenants/dashboard/`                   | `tenants:dashboard`                              | Voltar                |

### Auditoria Design System

| Item                  | Status       | Observação           |
| --------------------- | ------------ | -------------------- |
| Template base correto | ⏳ Verificar | Tenant Admin styling |
| Sidebar visível       | ⏳ Verificar | Navegação            |
| Navegação funcional   | ⏳ Verificar | Links                |
| Responsividade        | ⏳ Verificar | Upload, textarea     |
| Padrões visuais       | ⏳ Verificar | Form, botões         |

---

## Página 2: Pré-processamento

### Informações Básicas

| Campo             | Valor                                  |
| ----------------- | -------------------------------------- |
| **Nome**          | Pré-processamento                      |
| **URL**           | `/treinamento/pre-processamento/<id>/` |
| **URL Name**      | `treinamento:pre_processamento`        |
| **View**          | `pre_processamento` (Function-Based)   |
| **Template**      | `treinamento/pre_processamento.html`   |
| **Template Base** | ⚠️ A verificar                         |
| **App**           | `ui.treinamento`                       |
| **Arquivo View**  | `app/ui/treinamento/views.py:197-211`  |

### Parâmetros de URL

| Parâmetro | Tipo | Descrição         |
| --------- | ---- | ----------------- |
| `id`      | int  | ID do Treinamento |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ✅ Requerida                               |
| **Roles Permitidos** | Mesma verificação `_can_access_training()` |
| **Módulo**           | `TREINAMENTO`                              |

### Ações Disponíveis

| Ação     | Resultado                         |
| -------- | --------------------------------- |
| Aceitar  | Aplica melhorias de IA e finaliza |
| Editar   | Permite ajustes no conteúdo       |
| Rejeitar | Descarta o treinamento            |

### Links da Página

| #   | Nome do Link | URL de Destino             | URL Name                 | Resumo          |
| --- | ------------ | -------------------------- | ------------------------ | --------------- |
| 1   | Voltar       | `/treinamento/treinar-ia/` | `treinamento:treinar_ia` | Lista principal |

### Auditoria Design System

| Item                  | Status       | Observação       |
| --------------------- | ------------ | ---------------- |
| Template base correto | ⏳ Verificar | A verificar      |
| Sidebar visível       | ⏳ Verificar | Navegação        |
| Navegação funcional   | ⏳ Verificar | Ações            |
| Responsividade        | ⏳ Verificar | Preview de texto |
| Padrões visuais       | ⏳ Verificar | Botões de ação   |

---

## Página 3: Verificar Treinamentos

### Informações Básicas

| Campo             | Valor                                                 |
| ----------------- | ----------------------------------------------------- |
| **Nome**          | Verificar Treinamentos Vetorizados                    |
| **URL**           | `/treinamento/verificar-treinamentos/`                |
| **URL Name**      | `treinamento:verificar_treinamentos_vetorizados`      |
| **View**          | `verificar_treinamentos_vetorizados` (Function-Based) |
| **Template**      | `treinamento/verificar_treinamentos.html`             |
| **Template Base** | ⚠️ A verificar                                        |
| **App**           | `ui.treinamento`                                      |
| **Arquivo View**  | `app/ui/treinamento/views.py:315-381`                 |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ✅ Requerida                               |
| **Roles Permitidos** | Mesma verificação `_can_access_training()` |
| **Módulo**           | `TREINAMENTO`                              |

### Dados Exibidos

- Lista de treinamentos com sucesso (vetorizados)
- Lista de treinamentos com erro
- Ações de exclusão

### Links da Página

| #   | Nome do Link     | URL de Destino             | URL Name                 | Resumo    |
| --- | ---------------- | -------------------------- | ------------------------ | --------- |
| 1   | Novo Treinamento | `/treinamento/treinar-ia/` | `treinamento:treinar_ia` | Adicionar |
| 2   | Dashboard        | `/tenants/dashboard/`      | `tenants:dashboard`      | Voltar    |

### Auditoria Design System

| Item                  | Status       | Observação       |
| --------------------- | ------------ | ---------------- |
| Template base correto | ⏳ Verificar | A verificar      |
| Sidebar visível       | ⏳ Verificar | Navegação        |
| Navegação funcional   | ⏳ Verificar | Tabela com ações |
| Responsividade        | ⏳ Verificar | Tabelas          |
| Padrões visuais       | ⏳ Verificar | Status badges    |

---

## Página 4: Cadastrar Query Compose

### Informações Básicas

| Campo             | Valor                                      |
| ----------------- | ------------------------------------------ |
| **Nome**          | Cadastrar Intenção (Query Compose)         |
| **URL**           | `/treinamento/cadastrar-query-compose/`    |
| **URL Name**      | `treinamento:cadastrar_query_compose`      |
| **View**          | `cadastrar_query_compose` (Function-Based) |
| **Template**      | `treinamento/cadastrar_query_compose.html` |
| **Template Base** | ⚠️ A verificar                             |
| **App**           | `ui.treinamento`                           |
| **Arquivo View**  | `app/ui/treinamento/views.py:452-593`      |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ✅ Requerida                               |
| **Roles Permitidos** | Mesma verificação `_can_access_training()` |
| **Módulo**           | `TREINAMENTO`                              |

### Formulário

| Campo         | Nome            | Tipo     | Descrição                |
| ------------- | --------------- | -------- | ------------------------ |
| Tag           | `tag`           | text     | Identificador único      |
| Grupo         | `grupo`         | text     | Agrupamento              |
| Descrição     | `description`   | textarea | Descrição da intenção    |
| Comportamento | `comportamento` | textarea | Como a IA deve responder |

### Comportamento

- Suporta modo de edição (dados em sessão)
- Embedding gerado assíncrono via signal

### Links da Página

| #   | Nome do Link      | URL de Destino                          | URL Name                              | Resumo           |
| --- | ----------------- | --------------------------------------- | ------------------------------------- | ---------------- |
| 1   | Verificar Intents | `/treinamento/verificar-query-compose/` | `treinamento:verificar_query_compose` | Lista de intents |
| 2   | Dashboard         | `/tenants/dashboard/`                   | `tenants:dashboard`                   | Voltar           |

### Auditoria Design System

| Item                  | Status       | Observação   |
| --------------------- | ------------ | ------------ |
| Template base correto | ⏳ Verificar | A verificar  |
| Sidebar visível       | ⏳ Verificar | Navegação    |
| Navegação funcional   | ⏳ Verificar | Formulário   |
| Responsividade        | ⏳ Verificar | Campos       |
| Padrões visuais       | ⏳ Verificar | Form styling |

---

## Página 5: Verificar Query Compose

### Informações Básicas

| Campo             | Valor                                      |
| ----------------- | ------------------------------------------ |
| **Nome**          | Verificar Intenções                        |
| **URL**           | `/treinamento/verificar-query-compose/`    |
| **URL Name**      | `treinamento:verificar_query_compose`      |
| **View**          | `verificar_query_compose` (Function-Based) |
| **Template**      | `treinamento/verificar_query_compose.html` |
| **Template Base** | ⚠️ A verificar                             |
| **App**           | `ui.treinamento`                           |
| **Arquivo View**  | `app/ui/treinamento/views.py:385-449`      |

### Permissões

| Tipo                 | Valor                                      |
| -------------------- | ------------------------------------------ |
| **Autenticação**     | ✅ Requerida                               |
| **Roles Permitidos** | Mesma verificação `_can_access_training()` |
| **Módulo**           | `TREINAMENTO`                              |

### Dados Exibidos

- Intents com sucesso (embedding preenchido)
- Intents com erro (embedding nulo)
- Ações: editar, excluir

### Ações

| Ação    | Resultado                                 |
| ------- | ----------------------------------------- |
| editar  | Popula sessão e redireciona para cadastro |
| excluir | Remove o registro                         |

### Links da Página

| #   | Nome do Link  | URL de Destino                          | URL Name                              | Resumo    |
| --- | ------------- | --------------------------------------- | ------------------------------------- | --------- |
| 1   | Nova Intenção | `/treinamento/cadastrar-query-compose/` | `treinamento:cadastrar_query_compose` | Adicionar |
| 2   | Dashboard     | `/tenants/dashboard/`                   | `tenants:dashboard`                   | Voltar    |

### Auditoria Design System

| Item                  | Status       | Observação       |
| --------------------- | ------------ | ---------------- |
| Template base correto | ⏳ Verificar | A verificar      |
| Sidebar visível       | ⏳ Verificar | Navegação        |
| Navegação funcional   | ⏳ Verificar | Tabela com ações |
| Responsividade        | ⏳ Verificar | Tabelas          |
| Padrões visuais       | ⏳ Verificar | Status badges    |

---

## URL Legado

| URL                        | Alvo         | Descrição                              |
| -------------------------- | ------------ | -------------------------------------- |
| `/treinamento/treinar_ia/` | `treinar_ia` | Alias com underscore (compatibilidade) |

---

## Controle de Acesso

### Matriz de Permissões

| Role                | Treinar | Pré-proc | Verificar | Query Compose |
| ------------------- | ------- | -------- | --------- | ------------- |
| Owner Tenant Ativo  | ✅      | ✅       | ✅        | ✅            |
| Admin               | ✅      | ✅       | ✅        | ✅            |
| Manager             | ✅      | ✅       | ✅        | ✅            |
| Staff + Permissão   | ✅      | ✅       | ✅        | ✅            |
| Staff sem Permissão | ❌      | ❌       | ❌        | ❌            |
| Viewer              | ❌      | ❌       | ❌        | ❌            |

---

## Redirecionamentos do Módulo

| Origem             | Destino            | Condição           |
| ------------------ | ------------------ | ------------------ |
| Treinamento criado | Pré-processamento  | Novo upload        |
| Pré-proc aceito    | Lista treinamentos | Sucesso            |
| Query criada       | Lista intents      | Sucesso            |
| Sem permissão      | 403                | `PermissionDenied` |

---

## Checklist de Validação do Módulo

- [ ] Todas as páginas documentadas
- [ ] Todos os links mapeados
- [ ] Permissões verificadas (`_can_access_training`)
- [ ] Template base auditado
- [ ] URL legado documentado
- [ ] **APROVADO PELO USUÁRIO**
