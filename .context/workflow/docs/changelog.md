# Changelog

## [v1.1.0] - 2026-05-22

### Adicionado
- **Consolidação dos models de informação no centro `atendimentos`** (arquitetura v6.0): `CampoPersonalizado`, `ValorCampoAtendimento`, `Etiqueta`, `EtiquetaAtendimento`, `Nota` movidos do shell para `atendimentos` via migrations `SeparateDatabaseAndState` (tabelas `atu_*` preservadas). `atendimento_unificado` passa a ser apenas a ponte/UI. Apps periféricos leem via selectors e atualizam por signals.
- **Build de produção Tailwind v4 (sem Node):** `core.build.css` purgado, gerado por `uv run task build-css` via `pytailwindcss` (binário standalone). Substitui o CDN `@tailwindcss/browser` (dev-only) no `base.html`. Tasks `build-css`/`watch-css` no `pyproject.toml`.
- **Gate de Final Review (PREVC fase C):** skill `prevc-final-review` + comando `/final-review` que audita planejado vs. implementado via subagente Opus, corrige desvios automaticamente e bloqueia o arquivamento de planos incompletos.
- Novos apps modulares `chat_evolution` e `gestao_kanban` criados para desacoplar as funcionalidades de chat e painel do monolito.
- Arquivos de selectors, signals e views reestruturados e otimizados dentro de cada respectivo app.
- Configuração do canal SSE para eventos específicos (`chat_evolution/signals.py` e `gestao_kanban/signals.py`) com isolamento multi-tenant.

### Removido
- `LeituraAtendimento` (audit log de leitura por atendente) — eliminado; não-lidos usam `Mensagem.lido` (fonte da verdade, sem multiatendente). Tabela `atu_leitura_atendimento` dropada.

### Modificado
- Integrado o shell `workspace.html` para consumir as rotas isoladas dos novos apps.
- Resolvidos os erros estáticos e warnings de Pyright (como o do `TipoRemetente.BOT` e importações não utilizadas de `signals`).
- Atualizado o inicializador `apps.py` de ambos os aplicativos para carregar dinamicamente seus respectivos brokers de sinais com as anotações do Pyright adequadas.

### Removido
- Removidos e esvaziados os módulos obsoletos do monolito antigo `atendimento_unificado` (`selectors.py`, `signals.py`, `views_api.py` deletados e `api_urls.py` esvaziado).

### Workflow
- Workflow PREVC do plano `refatoracao-modular-atendimento` finalizado e arquivado.

---

## [v1.0.3] - 2026-02-12

### Adicionado
- Feature `transcribe_audio` no `ai_engine` para transcrição de áudios via WhatsApp.
- Nova configuração de transcrição no runtime (`transcription_provider`, `transcription_model`), com suporte a override por tenant.
- Integração da transcrição no orquestrador de atendimento antes da análise de mensagem.
- Novos parâmetros/tipos/erros da feature de transcrição e exports no módulo `ai_engine`.

### Corrigido
- Correção do fluxo de webhook para evitar descarte silencioso de `audioMessage`.
- Propagação de metadados de áudio (`url`, `mimetype`, `seconds`, `ptt`) no pipeline de atendimento.

### Alterado
- Persistência do texto transcrito no conteúdo da mensagem para alimentar `analise_previa_mensagem` e `analise_mensage`.
- Campos de configuração de transcrição adicionados ao domínio de tenant e admin.
- Migração aplicada para `TenantConfig` (`0005_tenantconfig_transcription_model_and_more.py`).

### Workflow
- Workflow PREVC do plano `feature-transcribe-audio` finalizado no MCP (`P`, `R`, `E`, `V` concluídas; `C` não exigida para escala `MEDIUM`).
- Documentação de release atualizada para publicação da versão `v1.0.3`.

---

## [2026-02-06] - Whitelist UI + Teste de Treinamento

### Adicionado

#### Feature 3: Whitelist UI no Painel de Configurações
- Painel de configurações acessível no dashboard (`/configuracoes/`)
- CRUD completo de whitelist (`/configuracoes/whitelist/`)
  - Listar números com busca por nome/telefone
  - Adicionar número com validação de formato brasileiro
  - Editar nome e telefone
  - Excluir com página de confirmação
  - Toggle ativo/inativo inline via AJAX
- Validação de variações de telefone (com/sem 9o dígito brasileiro)
- Link "Whitelist" na sidebar do dashboard (seção Configurações)
- Arquivos criados:
  - `app/settings_manager/forms.py` - WhiteListForm
  - `app/settings_manager/urls.py` - Rotas de configurações
  - `app/settings_manager/views.py` - Views CRUD
  - `app/settings_manager/templates/configuracoes/index.html`
  - `app/settings_manager/templates/configuracoes/whitelist.html`
  - `app/settings_manager/templates/configuracoes/whitelist_form.html`
  - `app/settings_manager/templates/configuracoes/whitelist_confirm.html`

#### Feature 1: Teste de Treinamento (Chat Interativo)
- Página "Testar Respostas" (`/treinamento/testar-query/`)
- Chat interativo para enviar mensagens simuladas ao bot
- Painel de detalhes mostrando:
  - Score de confiabilidade (barra visual)
  - Flag de transferência de atendimento
  - Entidades extraídas (badges)
  - Intents detectados (badges)
  - Documentos RAG utilizados
  - QueryCompose match
- Sistema de avaliação (bom/ruim) com correção
- Model `QueryTestFeedback` para armazenar feedbacks
- Endpoint AJAX `testar-resposta/` para análise de mensagem
- Endpoint AJAX `feedback-resposta/` para registrar avaliação
- Botão "Testar Respostas" na página Verificar Query Compose
- Link "Testar Respostas" na sidebar (seção Treinamento IA)
- Migration `0002_create_query_test_feedback`

### Modificado
- `app/core/urls.py` - Include de rotas `/configuracoes/`
- `app/core/templates/base_dashboard.html` - Links Whitelist e Testar Respostas na sidebar
- `app/treinamento/views.py` - Views testar_query_page, testar_resposta_query, feedback_resposta_query
- `app/treinamento/urls.py` - URLs de teste
- `app/treinamento/models.py` - Model QueryTestFeedback
- `app/treinamento/templates/treinamento/verificar_query_compose.html` - Botão "Testar Respostas"

### Não Incluído (Adiado)
- Feature 2: Refatoração de Apps Django (alto risco, sprint futuro)
- Testes automatizados (teste manual pós-implementação)
