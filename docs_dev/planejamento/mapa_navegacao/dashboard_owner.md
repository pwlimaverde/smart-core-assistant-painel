# Dashboard do Tenant - Itens exibidos (Checklist)

> Documento de referencia para validar o que aparece em `/tenants/dashboard/`.
> Baseado em `tenants/dashboard.html` e `base_dashboard.html`.

---

## Contexto

| Campo | Valor |
| --- | --- |
| URL | `/tenants/dashboard/` |
| Template | `tenants/dashboard.html` |
| Template base | `base_dashboard.html` |
| App | `tenants` |
| Publico | Usuarios autenticados com tenant (visibilidade varia por permissoes de modulo) |

---

## Checklist - Area principal do dashboard

- [x] Cabecalho com **nome do tenant**
  - Fonte: `tenant.name`
  - Objetivo: identificar a empresa atual
- [x] Cabecalho com **slug do tenant**
  - Fonte: `tenant.slug`
  - Objetivo: confirmar o subdominio/identificador
- [x] Badge do **plano**
  - Fonte: `subscription.plan.name` (fallback: "Sem Plano")
  - Objetivo: indicar o plano ativo
- [x] Badge de **status do tenant**
  - Fonte: `tenant.active` (Ativo/Inativo)
  - Objetivo: sinalizar se o tenant esta habilitado
- [x] **Visibilidade dos cards de configuracao**
  - Regra: apenas **owner** ou modulo **configuracoes**
  - Sem permissao: exibir mensagem "Sem acesso as configuracoes"
- [x] **Acesso limitado**
  - Regra: usuario sem nenhum modulo marcado
  - Exibir mensagem "Acesso limitado"

---

## Checklist - Cards de configuracao/integacao

- [x] **Banco de Dados (PostgreSQL)**
  - Status: `database.connection_valid`
  - CTA: `/tenants/config/database/`
  - Objetivo: configurar e validar conexao do banco
- [x] **Evolution API (WhatsApp)**
  - Status: `evolution.connection_valid`
  - CTA: `/tenants/config/evolution/`
  - Objetivo: configurar conexao do WhatsApp
- [x] **Trello**
  - Status: `trello.api_key`
  - CTA: `/tenants/config/trello/`
  - Objetivo: integrar quadros do Trello
- [x] **Inteligencia Artificial**
  - Status: texto informativo (sem status tecnico)
  - CTA: `/tenants/config/ai/`
  - Objetivo: configurar prompts e LLM
- [x] **Debug de Configuracoes**
  - Status: texto informativo (ferramenta dev)
  - CTA: `/tenants/config/debug/`
  - Objetivo: inspecionar configuracoes carregadas

---

## Checklist - Navegacao lateral (menu do tenant)

> Regra: evitar duplicar atalhos que ja estao dentro de uma tela principal.

### Geral

- [x] **Dashboard**
  - Link: `/tenants/dashboard/`
  - Observacao: visivel apenas para **owner** ou modulo **configuracoes**

### Configuracoes

- [x] **Banco de Dados** — `/tenants/config/database/`
- [x] **Evolution** — `/tenants/config/evolution/`
- [x] **Trello** — `/tenants/config/trello/`
- [x] **IA** — `/tenants/config/ai/`
- [x] **Debug** — `/tenants/config/debug/`
  - Observacao: visivel apenas para **owner** ou modulo **configuracoes**

### Operacoes (modulos core do tenant)

- [x] **Painel Admin** — `/tenant-admin/`
  - Observacao: visivel para **owner** ou modulo **painel_admin**
  - Dentro do painel: acesso aos modulos **Clientes**, **Operacional** e **Atendimentos**

### Treinamento IA

- [x] **Treinar IA** — `/treinamento/treinar-ia/`
  - Observacao: requer modulo **treinamento** (edicao)
- [x] **Verificar Treinamentos** — `/treinamento/verificar-treinamentos/`
  - Observacao: liberado para todos os usuarios do tenant (somente leitura)
- [x] **Cadastrar Query Compose** — `/treinamento/cadastrar-query-compose/`
  - Observacao: requer modulo **treinamento** (edicao)
- [x] **Verificar Query Compose** — `/treinamento/verificar-query-compose/`
  - Observacao: liberado para todos os usuarios do tenant (somente leitura)

### Gestao

- [x] **Usuarios** — `/tenants/users/`
  - Observacao: visivel para **owner** ou modulo **usuarios**

### Perfil do usuario (rodape da sidebar)

- [x] Avatar: iniciais de `request.user.username`
- [x] Nome: `request.user.first_name` ou `request.user.username`
- [x] Link sair: `/usuarios/logout/`

---

## Checklist - Barra superior (topbar)

- [x] Exibir email do usuario logado
  - Fonte: `request.user.email`

---

## Pendencias conhecidas

- Nenhuma pendencia no momento (menu definido).
