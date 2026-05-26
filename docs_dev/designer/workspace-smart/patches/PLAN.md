# Plano de Refatoração — Workspace de Atendimento

Este pacote contém todos os arquivos que precisam ser criados ou modificados
no repositório [smart-core-assistant-painel](https://github.com/pwlimaverde/smart-core-assistant-painel)
para aplicar o redesign do Workspace de Atendimento.

A estrutura abaixo espelha a do seu repo. Os caminhos são relativos à raiz
do projeto Django (`src/smart_core_assistant_painel/`).

---

## Princípio de organização: separação em camadas

Pra facilitar futuros ajustes, o CSS é dividido em **dois arquivos**:

| Arquivo | Conteúdo | Quando editar |
|---|---|---|
| **`workspace-tokens.css`** | Apenas variáveis CSS (`--ws-*`) — cores, espaçamentos, raios, sombras, durações, larguras de painel. **Nada de seletores.** | Sempre que quiser mudar tema, paleta, densidade ou medidas. **É o único arquivo que muda em 90% dos casos.** |
| **`workspace.css`** | Todas as classes de componente (`.kanban-card`, `.chat-*`, `.mini-*`, `.focus-seg`, etc.) consumindo variáveis do `workspace-tokens.css`. | Só quando mudar a estrutura HTML de um componente. |

O `app.css` global do projeto **não muda** — esses arquivos novos são específicos do Workspace e ficam em `app/atendimento_unificado/static/atendimento_unificado/css/`.

### Tema dark "de graça"

Como tudo usa variáveis, o dark mode é só um bloco extra no `workspace-tokens.css` que sobrescreve as variáveis quando `<html data-theme="dark">`. Você pode plugar isso a um setting do usuário sem mexer em nenhum componente.

---

## Arquivos no pacote

### 🆕 Novos arquivos

```
app/atendimento_unificado/
├── static/atendimento_unificado/css/
│   ├── workspace-tokens.css         ← Design system (variáveis)
│   └── workspace.css                ← Componentes
└── templates/atendimento_unificado/partials/
    ├── chat_mini_bar.html           ← Mini-bar flutuante (modo Kanban)
    ├── chat_quick_actions.html      ← Strip de ações rápidas
    └── focus_segmented.html         ← Segmented control de foco
```

### ✏️ Arquivos modificados

```
app/atendimento_unificado/
├── static/atendimento_unificado/js/
│   └── workspace_alpine.js          ← + focusMode, minimize/open, atalhos
└── templates/atendimento_unificado/
    ├── base_workspace.html          ← + <link> dos CSS novos
    ├── workspace.html               ← topbar + estrutura main
    └── partials/
        ├── kanban_card.html         ← Layout mais rico
        └── chat_message.html        ← Bolhas estilo WhatsApp + waveform
```

---

## O que muda em cada arquivo

### 1. `workspace-tokens.css` (NOVO)

Centraliza todos os tokens visuais do workspace. Estruturado em 6 seções claras:

- **Cores semânticas** (`--ws-bg`, `--ws-card`, `--ws-fg-strong`, `--ws-border`, etc.) — derivadas dos `--gold-*` e `--stone-*` do seu sistema atual.
- **Cores do chat WhatsApp** (`--ws-chat-bg`, `--ws-bub-in`, `--ws-bub-out`).
- **Espaçamento/raios** (`--ws-pad-card`, `--ws-radius-card`).
- **Sombras** (`--ws-shadow-sm`, `--ws-shadow-mini`).
- **Largura de painéis** (`--ws-chat-w`, `--ws-info-w`).
- **Tema escuro** (bloco `[data-theme="dark"]` sobrescrevendo todas as cores).

Como editar:
- Quer chat mais largo? Mude `--ws-chat-w`.
- Quer paleta mais quente? Mude `--ws-bg` e `--ws-card`.
- Quer ativar dark? Adicione `data-theme="dark"` no `<html>`.

### 2. `workspace.css` (NOVO)

Todas as classes de componente do workspace, organizadas em blocos comentados:
- App shell (sidebar/topbar/main)
- Topbar (search, focus segmented, pills)
- Kanban (column, card, drag states)
- Chat panel (header, body, bubbles, audio waveform, composer)
- Mini-bar flutuante
- Info drawer
- Modos de foco (`.app__main[data-focus="board"]` etc.)

### 3. `workspace_alpine.js` (MODIFICADO)

Adições à `workspaceStore`:
- `focusMode: 'split'` — estado persistido em `localStorage`
- `setFocus(mode)`, `minimizeChat()`, `openChat()`
- Handler `_onKeydown` para atalhos (Alt+1/2/3, Esc, i)
- `init()` registra/desregistra `keydown` no `window`

### 4. `workspace.html` (MODIFICADO)

- Topbar ganha o segmented control de foco (3 botões).
- `<main>` ganha `:data-focus="focusMode"`.
- Chat e InfoDrawer ficam dentro de `<template x-if="focusMode !== 'board'">`.
- Mini-bar dentro de `<template x-if="focusMode === 'board' && activeConv">`.
- Atalhos via `@keydown.alt.1.window` etc.

### 5. `kanban_card.html` (MODIFICADO)

Adota a estrutura mais rica do protótipo: avatar circular com presença, nome + telefone, prévia de mensagem com ícone de tipo (áudio/imagem/doc), tags coloridas, SLA contextualizado, avatar do atendente, contador de não lidas.

**Importante:** usa só os campos que já vêm do `card_renderer.py`. Nenhum dado novo é inventado.

### 6. `chat_message.html` (MODIFICADO)

Bolhas com cantos quentes estilo WhatsApp, separadores de dia, status ✓/✓✓/✓✓-azul, player de áudio com waveform, card de documento com download, reply em quote.

---

## Como aplicar

```bash
# 1. Crie a branch no seu repo
cd ~/dev/smart-core-assistant-painel
git checkout dev
git pull
git checkout -b feat/workspace-redesign

# 2. Copie os arquivos deste pacote para seu repo
#    (cada arquivo está no caminho correspondente a partir de src/)

# 3. Rode local + verifique
uv run manage.py collectstatic --noinput
uv run manage.py runserver

# 4. Acesse /workspace/ — deve abrir no modo "Dividido" por padrão.
#    Teste Alt+1 / Alt+2 / Alt+3 e o segmented no topbar.

# 5. Commit + PR
git add -A
git commit -m "feat(workspace): novo layout com modos de foco e design system"
git push -u origin feat/workspace-redesign
```

---

## Riscos / pontos de atenção

1. **`workspace_alpine.js` é grande (511 linhas).** Vou preservar tudo que já funciona (drag-drop, SSE, upload, custom fields) — só adicionar os novos métodos no final, sem refatorar o resto.
2. **`chat_message.html` muda a aparência mas mantém os mesmos templates `x-if`** para image/audio/video/document/text. Não quebra dados existentes.
3. **`kanban_card.html`** depende de `card_renderer.py` ter `canal_emoji`, `prioridade`, `prioridade_label_class`, `atendente`, `sla_estourado`, `tempo_ultima_msg`. **Tudo isso já existe**, verifiquei.
4. **Tailwind 4 via CDN** já está em `base.html`. Vou usar tanto classes Tailwind quanto classes próprias (`.kanban-card`, `.chat__bub`, etc.) — a mistura é OK.
5. **Drag-and-drop (SortableJS)** mantém os mesmos seletores (`.kanban-col-body`, `.kanban-card`, `[data-etapa-id]`) — não quebra.

---

## Próximos passos sugeridos depois disso

- Persistir `focusMode` por atendente no DB (não só localStorage) para multi-device.
- Migrar para Outfit local em `static/fonts/` (offline-safe).
- Substituir os emoji de canal por SVG no kanban card.
- Adicionar lightbox de imagem no chat (clica → zoom).
