# Changelog

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
