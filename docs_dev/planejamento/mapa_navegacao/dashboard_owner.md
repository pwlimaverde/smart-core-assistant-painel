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
| Publico | Usuarios autenticados com tenant (owner/admin/manager/staff/viewer) |

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
  - Observacao: item fixo para retorno

### Configuracoes

- [x] **Banco de Dados** — `/tenants/config/database/`
- [x] **Evolution** — `/tenants/config/evolution/`
- [x] **Trello** — `/tenants/config/trello/`
- [x] **IA** — `/tenants/config/ai/`
- [x] **Debug** — `/tenants/config/debug/`
  - Observacao: visibilidade condicional por modulo

### Operacoes (modulos core do tenant)

- [x] **Painel Admin** — `/tenant-admin/`
  - Observacao: acesso centralizado para Atendimentos, Clientes e Operacional

### Treinamento IA

- [x] **Treinar IA** — `/treinamento/treinar-ia/`
- [x] **Verificar Treinamentos** — `/treinamento/verificar-treinamentos/`
- [x] **Cadastrar Query Compose** — `/treinamento/cadastrar-query-compose/`
- [x] **Verificar Query Compose** — `/treinamento/verificar-query-compose/`
  - Observacao: estes atalhos sao opcionais se a tela "Treinar IA" ja centraliza os acessos.

### Gestao

- [x] **Usuarios** — `/tenants/users/`
  - Observacao: edicao de permissoes e convite ja ficam dentro de Usuarios

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
