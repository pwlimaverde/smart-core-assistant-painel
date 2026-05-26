---
status: filled
generated: 2026-05-24
agents:
  - type: "bug-fixer"
    role: "Investigar e corrigir o bug de renderização das mensagens (x-for Alpine)"
  - type: "backend-specialist"
    role: "Saída estruturada da IA (Pydantic), modelo de dados e datasources"
  - type: "frontend-specialist"
    role: "UX estilo WhatsApp: preview de mídia, lightbox, botão de análise, quebras de linha"
docs:
  - "architecture.md"
  - "data-flow.md"
phases:
  - id: "phase-1"
    name: "Correção do bug de visualização (x-for Alpine)"
    prevc: "E"
    agent: "bug-fixer"
    status: "completed"
  - id: "phase-2"
    name: "Saída estruturada da IA: análise + resumo (Pydantic)"
    prevc: "E"
    agent: "backend-specialist"
    status: "completed"
  - id: "phase-3"
    name: "Frontend estilo WhatsApp (preview, lightbox, análise, quebras de linha)"
    prevc: "E"
    agent: "frontend-specialist"
    status: "completed"
---

# Chat estilo WhatsApp: mídia/IA estruturada + correção de visualização

> Corrigir o bug de renderização das mensagens (`x-for` do Alpine com múltiplos roots),
> separar a saída da IA em **análise** (contexto do bot) e **resumo** (exibido ao atendente)
> via Pydantic, e aproximar a UX do chat do WhatsApp (preview de mídia, lightbox, botão de
> análise, quebras de linha).

## Artefatos detalhados (fonte da verdade técnica)
- **Plano completo:** [`chat-whatsapp-midia-ia/plano_completo_chat-whatsapp-midia-ia.md`](./chat-whatsapp-midia-ia/plano_completo_chat-whatsapp-midia-ia.md)
- **Documentação auxiliar (libs + validações):** [`chat-whatsapp-midia-ia/info_aux_chat-whatsapp-midia-ia.md`](./chat-whatsapp-midia-ia/info_aux_chat-whatsapp-midia-ia.md)

## Task Snapshot
- **Primary goal:** chat fluido estilo WhatsApp, com mensagens renderizando corretamente,
  preview/lightbox de mídia e análise da IA (resumo) sob demanda.
- **Success signal:** ao abrir um atendimento as bolhas aparecem; mídias têm preview e
  botão "Ver análise IA"; `analise_midia` (contexto bot) e `resumo_midia` (exibido) salvos
  separadamente; texto multilinha renderiza com quebras de linha.
- **Key references:** [.context/docs/architecture.md](../docs/architecture.md) · Multi-Tenant + Result Pattern.

## Fases (PREVC: E — Execução)

### Phase 1 — Correção do bug de visualização (`bug-fixer`)
Causa raiz: partial `chat_message.html` com 3 elementos raiz dentro de `<template x-for>`
(Alpine exige root único — validado em alpinejs.dev/directives/for).
- 1.1 Envolver o partial num único `<div>` wrapper (separadores `x-if` ficam dentro).
- 1.2 `chat_alpine.js` `loadMessages`: tratar erro/HTTP não-2xx (sem falha silenciosa).
- 1.3 (condicional) `views_api.py` `_can_access_atendimento`: 403 p/ atendimentos sem fluxo — verificar no banco antes de alterar.

### Phase 2 — Saída estruturada da IA: análise + resumo (`backend-specialist`)
- 2.1 Campo `Mensagem.resumo_midia` (TextField) + migration `0009`.
- 2.2 Modelo Pydantic `MediaAnalysis {analise, resumo}` (`ai_engine/utils/types.py`).
- 2.3 Datasources: `interpret_media` (multimodal + `with_structured_output`, 1 chamada) e
  `transcribe_audio` (transcrição + resumo em 2 passos). Result Pattern preservado.
- 2.4 Composição: `converter_contexto`/`_convert_media_context` salvam `analise_midia` (bot) e `resumo_midia` (exibido).

### Phase 3 — Frontend estilo WhatsApp (`frontend-specialist`)
- 3.1 `white-space: pre-wrap` no corpo do balão (renderiza `\n`).
- 3.2 Serializer envia `resumo_midia` (e `analise_midia` só p/ áudio); botão "Ver análise IA"
  revela: áudio = transcrição+resumo; visual = resumo.
- 3.3 Revisar preview inline + lightbox (PDF iframe), refinar estilos WhatsApp.

## Conformidade
- Result Pattern nos usecases/datasources de IA; Multi-Tenant via `SERVICEHUB`/config por tenant; nenhuma credencial nova em `.env`; nenhuma lib nova.

## Verificação
Migration aplicada; `pyright` limpo; bolhas renderizam; rajada de texto com quebras de linha;
mídias com preview/lightbox e botão de análise; `analise_midia`/`resumo_midia` separados no banco;
mídia visual não expõe análise completa ao atendente.
