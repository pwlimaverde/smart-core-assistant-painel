# Workspace Redesign — Pacote de Aplicação

Este pacote contém todos os arquivos novos e modificados para aplicar o
redesign do Workspace de Atendimento no repositório
`smart-core-assistant-painel`.

📖 **Leia primeiro:** [`PLAN.md`](./PLAN.md) — visão geral, princípio de
organização do design system e checklist de aplicação.

---

## Estrutura

A pasta `app/` espelha exatamente a estrutura do seu repo a partir de
`src/smart_core_assistant_painel/`. Você pode copiar arquivo por arquivo
ou usar `rsync`/`cp -r` direto.

```
patches/
├── README.md                              ← este arquivo
├── PLAN.md                                ← plano detalhado
└── app/
    └── atendimento_unificado/
        ├── static/atendimento_unificado/
        │   ├── css/
        │   │   ├── workspace-tokens.css   🆕 design system (variáveis)
        │   │   └── workspace.css          🆕 componentes
        │   └── js/
        │       └── workspace_alpine.js    ✏️ + focusMode, atalhos, mini-bar
        └── templates/atendimento_unificado/
            ├── base_workspace.html        ✏️ carrega CSS + handlers de teclado
            ├── workspace.html             ✏️ topbar + main com focus modes
            └── partials/
                ├── kanban_card.html       ✏️ layout mais rico
                ├── chat_message.html      ✏️ bolhas WhatsApp + tokens
                ├── chat_mini_bar.html     🆕 mini-bar flutuante
                └── focus_segmented.html   🆕 segmented control de foco
```

(Outros partials como `kanban_column.html`, `detail_panel.html`,
`chat_drawer.html`, `conversation_item.html`, `custom_fields_panel.html`
**não foram tocados** — continuam usando o template original.)

---

## Aplicação

```bash
cd ~/dev/smart-core-assistant-painel

# 1. Branch nova a partir de dev
git checkout dev && git pull
git checkout -b feat/workspace-redesign

# 2. Copie os arquivos (ajuste o caminho do pacote)
PKG=~/baixados/patches  # caminho onde você baixou este pacote
rsync -av "$PKG/app/" src/smart_core_assistant_painel/app/

# 3. Colete os estáticos novos
uv run manage.py collectstatic --noinput

# 4. Rode e teste
uv run manage.py runserver

#    Abra /workspace/ e teste:
#    - Layout dividido (padrão) com os 3 painéis
#    - Botões "Kanban / Dividido / Atendimento" no topo
#    - Atalhos Alt+1 / Alt+2 / Alt+3
#    - Esc para reduzir o foco gradualmente
#    - "i" para abrir o drawer de detalhes
#    - No modo Kanban: mini-bar aparece no canto inferior direito

# 5. Commit
git add -A
git commit -m "feat(workspace): novo layout com modos de foco e design system"
git push -u origin feat/workspace-redesign
```

---

## Como ajustar depois

### Mudar uma cor / paleta

Edite **só** `workspace-tokens.css`. Por exemplo, pra fundo do board mais
quente:

```css
--ws-bg: #f5efe7;   /* gold-50 em vez de stone-100 */
```

### Ativar dark mode globalmente

No `<html>` ou body, adicione `data-theme="dark"`. Todos os componentes
trocam de tom automaticamente — nenhum CSS extra necessário.

```html
<html data-theme="dark">
```

Pra deixar persistido por usuário, você já tem `theme` no store
(`workspaceStore`). É só plugar num setting do tenant ou em
`localStorage` (já vem com fallback).

### Mudar largura do chat

```css
--ws-chat-w: 520px;    /* era 460px */
--ws-chat-w-max: 700px;
```

### Mudar densidade dos cards

Por usuário, mude `data-ws-density` no `<html>` (`compact` / `normal` /
`confortable`).

```html
<html data-ws-density="compact">
```

### Mudar a cor de marca

```css
--ws-accent:        #2563eb;   /* azul */
--ws-accent-hover:  #1d4ed8;
--ws-accent-soft:   rgba(37, 99, 235, 0.10);
--ws-accent-ring:   rgba(37, 99, 235, 0.20);
```

Todos os botões primários, badges ativos, focus rings, mini-bar e estados
ativos do kanban trocam de cor em cascata.

---

## Detalhes técnicos

### O que **não** muda no projeto

- `base.html` (Tailwind + Outfit + app.css globais)
- `app.css` global do core
- `views.py`, `selectors.py`, `services/*`, todos os modelos
- Endpoints da API (`views_api.py`)
- SSE (`views_sse.py`)
- Drag-and-drop (SortableJS) — seletores `.kanban-card`,
  `.kanban-col-body`, `[data-etapa-id]` preservados.

### O que **muda** no comportamento

- Layout padrão passa de "kanban + chat à direita fixo" para 3 modos.
- Estado `focusMode` persistido em `localStorage` (chave
  `workspace.focusMode`).
- Tema e densidade também em localStorage (`workspace.theme`,
  `workspace.density`).
- Atalhos `Alt+1/2/3`, `Esc`, `i` registrados em `base_workspace.html`
  via `@keydown.window`.

### Como o focusMode afeta o layout

O atributo `:data-focus="focusMode"` na `<main class="ws-main">` é tudo
que o CSS precisa. Os modos:

| focusMode | Comportamento |
|---|---|
| `board` | `.ws-chat` e `.ws-info` ficam `display: none`. Mini-bar aparece (`x-show` no template). |
| `split` | Comportamento normal — kanban + chat lado a lado. |
| `chat`  | `.ws-board` reduz para 88px e vira trilha vertical de avatares. Chat e info ficam grandes. |

Tudo em CSS puro — sem JS recalculando largura.

---

## Riscos conhecidos

1. **`card_renderer.py`**: kanban_card.html novo usa `card.nao_lidos`,
   `card.canal_emoji`, `card.prioridade`, `card.status`, `card.status_emoji`,
   `card.preview_msg`, `card.preview_remetente`, `card.atendente.nome`,
   `card.sla_estourado`, `card.tempo_ultima_msg`. Confirme que o
   `card_renderer.py` está expondo `nao_lidos` no payload (se não, adicione).

2. **Sem `data-comment-anchor`**: O design não preserva comment anchors
   porque nenhum existia no template original.

3. **Tailwind 4 + CSS custom**: estamos misturando classes Tailwind
   (`flex`, `text-stone-100`, etc.) com classes próprias (`.ws-*`). Isso
   funciona, mas em revisões futuras vale considerar mover tudo pra um
   ou outro estilo.

---

## Próximos passos sugeridos

1. **Persistir `focusMode` no DB** por atendente (`UserPreference` ou
   campo no `Atendente`) — hoje é só localStorage.
2. **Lightbox de imagem** no chat (clica → modal com zoom + navegação).
3. **Waveform real no áudio** — substituir `<audio controls>` por um
   componente Alpine com waveform.js / wavesurfer.js.
4. **Substituir emoji** de canal por SVG no kanban card.
5. **Tweaks panel** real (não só localStorage) — uma página de
   configurações pessoais do atendente.
