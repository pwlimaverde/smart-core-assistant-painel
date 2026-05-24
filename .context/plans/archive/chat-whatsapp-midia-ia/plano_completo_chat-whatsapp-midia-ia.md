# Plano Completo — Chat estilo WhatsApp: mídia/IA estruturada + correção de visualização

> Documentação auxiliar: `.context/plans/chat-whatsapp-midia-ia/info_aux_chat-whatsapp-midia-ia.md`
> Origem: plano elaborado na conversa (sessão atual), validado contra docs atuais (context7 + alpinejs.dev).

## Contexto

A refatoração v6.0 separou **chat** (`chat_evolution`), **kanban** (`gestao_kanban`) e o **centro de dados** (`atendimentos`); `atendimento_unificado` é só shell/ponte de UI. Após isso, ao clicar num atendimento o chat abre mas **nenhuma mensagem aparece** — bug de renderização. Objetivos:

1. **Corrigir** a visualização das mensagens (bug do Alpine `x-for`).
2. Aproximar o chat do **WhatsApp**: mensagens organizadas, preview de mídia/documento, lightbox ao clicar, botão que revela a análise da IA abaixo da mídia.
3. **Separar** a saída da IA em dois campos via Pydantic: **análise completa** (contexto interno do bot) e **resumo curto** (exibido ao atendente).

### Decisões do usuário (confirmadas)
- **Áudio**: botão exibe **transcrição completa + resumo**.
- **Mídia visual** (imagem/vídeo/documento): resumo aparece **só ao clicar** no botão.
- **Análise completa** de mídia visual **não** é exibida ao atendente (só contexto do bot). Para áudio, a transcrição é exibida (é o conteúdo útil).

> O buffer de texto **já** concatena as mensagens recebidas com `\n` (`attendance_orchestrator._compile_message_content`, linha 228). Falta apenas **renderizar** as quebras de linha no balão.

---

## FASE P1 — Correção do bug de visualização (PREVC: E · agente: backend/frontend)

**Causa raiz:** o partial `chat_evolution/partials/chat_message.html` é incluído dentro de
`<template x-for="m in enrichedMessages()" :key="m.id">` (`workspace.html:329`), mas tem **três elementos raiz** (dois `<template x-if>` + um `<div>`). Doc oficial do Alpine: `<template x-for>` **deve conter apenas um elemento raiz**; múltiplos irmãos não renderizam. Resultado: nenhuma bolha aparece (o "Nenhuma mensagem ainda." só surge com `messages.length === 0`).

**Passos:**
1. `chat_message.html`: envolver TODO o conteúdo num único `<div class="ws-msg-row">`. Os `<template x-if="m._showDateSep">` e `<template x-if="m._isFirstUnread">` passam a ficar **dentro** desse wrapper (permitido pela doc). O `:key="m.id"` já é estável.
2. `chat_alpine.js` `loadMessages` (linhas 105-114): tratar erro/HTTP não-2xx — checar `res.ok`, logar e expor estado de erro em vez de cair silenciosamente em `messages = []`.
3. `chat_evolution/views_api.py` `_can_access_atendimento`: atendimentos com `fluxo_atendimento_id = NULL` retornam 403. **Verificar no banco** se há atendimentos sem fluxo após a refatoração; se houver, liberar para owner/superuser ou atendimentos sem fluxo. (Só alterar após confirmar.)

**Arquivos:** `chat_message.html`, `chat_alpine.js`, (condicional) `views_api.py`.

---

## FASE P2 — Saída estruturada da IA (Pydantic): análise + resumo (PREVC: E · agente: backend/ml)

### P2.1 — Modelo de dados
- Adicionar `resumo_midia = models.TextField(blank=True, default="")` em `Mensagem` (`atendimentos/models.py`, junto de `analise_midia`, ~linha 1089).
- `analise_midia` = análise/transcrição completa → contexto do bot. `resumo_midia` = resumo curto → exibido.
- Migration: `uv run python manage.py makemigrations atendimentos --name mensagem_resumo_midia` → `0009_*`.

### P2.2 — Modelo Pydantic compartilhado
Em `ai_engine/utils/types.py` (ou novo `media_analysis.py`):
```python
from pydantic import BaseModel, Field

class MediaAnalysis(BaseModel):
    """Saída estruturada da análise de mídia pela IA."""
    analise: str = Field(description="Descrição/transcrição completa do conteúdo (contexto do bot)")
    resumo: str = Field(description="Resumo geral curto e amigável do que se trata a mídia")
```

### P2.3 — Datasources de IA (Result Pattern preservado)
- **`interpret_media_datasource.py`** (imagem/vídeo/documento): ajustar os 3 prompts para pedir descrição completa **e** breve resumo geral; usar `llm.with_structured_output(MediaAnalysis)` na **mesma** invocação multimodal → retorna instância (`result.analise`, `result.resumo`).
  - Validado: `ChatGoogleGenerativeAI(model="gemini-2.5-flash").with_structured_output(MediaAnalysis)` retorna instância; Gemini suporta multimodal + structured output combinados (ex. PDF inline → JSON num único `invoke`).
  - Content blocks: manter `{"type":"image_url","image_url":{"url":"data:...;base64,..."}}` (válido no 1.0 e já usado). Documento PDF pode usar `{"type":"document_url",...}`; vídeo mantém bloco `media`. Imports `langchain_core.messages` seguem válidos.
- **`transcribe_audio_datasource.py`**: `analise = transcrição`; gerar `resumo` numa 2ª chamada leve de texto (`with_structured_output` ou só o campo resumo) sobre a transcrição.
- Ajustar usecases (`interpret_media_usecase.py`, `transcribe_audio_usecase.py`) e tipos (`IMData`/retorno em `utils/types.py`/`parameters.py`) para propagar `MediaAnalysis` no `SuccessReturn`.

### P2.4 — Composição
- `features_compose.py` `converter_contexto` (linha 392) e helpers `_interpret_media`/`_transcribe_audio`: retornar `MediaAnalysis` (ou dict `{analise, resumo}`) em vez de `str`.
- Consumidores:
  - `attendance_orchestrator._convert_media_context` (linha 643): `mensagem.analise_midia = result.analise`; `mensagem.resumo_midia = result.resumo`; `metadados["contexto_convertido"] = result.analise`. Atualizar `update_fields`.
  - `features_compose.load_message_data` (linhas 567-572): usar `result.analise` no contexto (validar se o caminho ainda está ativo; se legado, manter compatível).

---

## FASE P3 — Frontend estilo WhatsApp (PREVC: E · agente: frontend)

### P3.1 — Quebras de linha do texto
No `chat_message.html`, aplicar `white-space: pre-wrap` na classe do corpo do balão (texto via `x-text` preserva `\n` com esse CSS; evita `x-html`/injeção). O texto agrupado já chega com `\n`.

### P3.2 — Serializer + botão de análise
- `chat_evolution/selectors.py` `_serialize_mensagem` (~485): adicionar `"resumo_midia": m.resumo_midia or ""`; enviar `analise_midia` **somente** quando `tipo == "audioMessage"` (não trafegar análise completa de mídia visual ao atendente).
- `chat_message.html` (toggle, linhas ~127-144): botão "Ver análise IA" revela abaixo da mídia:
  - **áudio**: `m.analise_midia` (transcrição) + `m.resumo_midia` (resumo);
  - **imagem/vídeo/documento**: apenas `m.resumo_midia`.
  - Exibir botão só quando houver conteúdo; alternar "Ver análise IA"/"Ocultar análise"; `white-space: pre-wrap` no corpo.

### P3.3 — Preview e lightbox (revisão)
Após P1, validar visualmente preview inline (imagem/áudio/vídeo/documento) e `openLightbox` (PDF em iframe; download p/ outros docs). Refinar estilos para aproximar do WhatsApp (alinhamento in/out, `_stacked`, ticks de status, separadores de data). Conferir `_extract_media` (`selectors.py:430`) entregando `src` por tipo.

---

## Arquivos críticos
- `app/chat_evolution/templates/chat_evolution/partials/chat_message.html`
- `app/atendimento_unificado/templates/atendimento_unificado/workspace.html` (x-for, l.329)
- `app/chat_evolution/static/chat_evolution/js/chat_alpine.js`
- `app/chat_evolution/selectors.py` (`_serialize_mensagem`, `_extract_media`)
- `app/chat_evolution/views_api.py` (`_can_access_atendimento` — condicional)
- `app/atendimentos/models.py` (+ migration `0009`)
- `app/atendimentos/services/attendance_orchestrator.py` (`_convert_media_context`)
- `modules/ai_engine/features/features_compose.py`
- `modules/ai_engine/features/interpret_media/datasource/interpret_media_datasource.py`
- `modules/ai_engine/features/transcribe_audio/datasource/transcribe_audio_datasource.py`
- `modules/ai_engine/features/{interpret_media,transcribe_audio}/domain/usecase/*.py`
- `modules/ai_engine/utils/types.py` / `parameters.py` (`MediaAnalysis`)

## Conformidade arquitetural
- **Result Pattern** mantido nos usecases/datasources de IA.
- **Multi-tenant**: nenhuma credencial nova em `.env`; reutilizar `SERVICEHUB`/config por tenant.
- Tokens de ML isolados via `SERVICEHUB`.

## Correções aplicadas (validação contra docs atuais)
- **Alpine `x-for`** (P1): regra de root único confirmada oficialmente (alpinejs.dev/directives/for) — wrapper validado.
- **LangChain 1.0 `with_structured_output`**: sem breaking change; classe Pydantic → instância. Multimodal + structured no mesmo `invoke` suportado (Gemini). Áudio mantém 2 passos por robustez.
- **Content blocks 1.0**: `image_url`+data-URI mantido (válido); blocos nativos (`image`/`document_url`) disponíveis; imports `langchain_core.messages` ok.
- **Sem libs novas**; `with_structured_output` já disponível.

## Verificação (end-to-end)
1. Migration: `makemigrations atendimentos` + `migrate` (validar `0009`).
2. `pyright` limpo nos arquivos alterados.
3. Bug: abrir workspace → bolhas renderizam (antes vazias); sumir o warning de `x-for` no console.
4. Texto multilinha: rajada de 2-3 mensagens → mesmo balão com quebras de linha.
5. Mídia: enviar áudio/imagem/documento/vídeo → preview + lightbox; botão revela (áudio = transcrição+resumo; visual = resumo); conferir no banco `analise_midia` e `resumo_midia` separados.
6. Confirmar que mídia visual **não** expõe a análise completa no JSON ao atendente.
