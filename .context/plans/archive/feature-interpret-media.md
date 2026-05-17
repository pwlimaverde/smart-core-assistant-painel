---
status: archived
generated: 2026-04-09
completed: 2026-05-14
agents:
  - type: "feature-developer"
    role: "Implementar a feature interpret_media seguindo o padrão transcribe_audio"
  - type: "backend-specialist"
    role: "Configurar integração com Gemini via langchain-google-genai e ajustar ServiceHub"
  - type: "database-specialist"
    role: "Criar migração Django para novos campos no TenantConfig"
  - type: "code-reviewer"
    role: "Revisar qualidade, type hints e aderência aos padrões do projeto"
  - type: "security-auditor"
    role: "Auditar tratamento de API keys e dados sensíveis (base64 de mídia)"
docs:
  - "architecture.md"
  - "data-flow.md"
  - "security.md"
  - "development-workflow.md"
phases:
  - id: "phase-1"
    name: "Planejamento e Configuração"
    prevc: "P"
    agent: "backend-specialist"
    steps:
      - "Adicionar dependência langchain-google-genai ao pyproject.toml"
      - "Criar campos vision_provider, vision_model e google_api_key no RuntimeConfig"
      - "Atualizar ServiceHub com novas properties e suporte a ChatGoogleGenerativeAI"
      - "Atualizar ConfigLoader para merge das novas configurações"
      - "Adicionar campos vision_provider e vision_model ao TenantConfig (Django)"
      - "Atualizar TenantConfigInline no admin"
      - "Adicionar entradas no coresettings.json"
      - "Atualizar bootstrap_core_settings.py com env mappings"
  - id: "phase-2"
    name: "Implementação da Feature"
    prevc: "E"
    agent: "feature-developer"
    steps:
      - "Criar classe InterpretMediaError em utils/erros.py"
      - "Criar dataclass InterpretMediaParameters em utils/parameters.py"
      - "Criar type aliases IMData e IMUsecase em utils/types.py"
      - "Criar estrutura de diretórios features/interpret_media/"
      - "Implementar InterpretMediaDatasource com lógica Gemini Vision"
      - "Implementar InterpretMediaUseCase com validações"
      - "Implementar método _interpret_media no FeaturesCompose"
      - "Atualizar converter_contexto() com handlers para image/video/document"
      - "Atualizar exportações no __init__.py do ai_engine"
      - "Gerar migração Django com makemigrations"
  - id: "phase-3"
    name: "Validação e Revisão"
    prevc: "V"
    agent: "code-reviewer"
    steps:
      - "Executar ruff format e ruff check (lint)"
      - "Executar pyright em modo strict (type-check)"
      - "Verificar que makemigrations gera migração corretamente"
      - "Revisar aderência ao padrão arquitetural do transcribe_audio"
      - "Verificar tratamento seguro de API keys (sem logs sensíveis)"
---

# Implementação de Interpretação de Mídias (Imagem, Vídeo e Documento)

> Implementar o processamento de `imageMessage`, `videoMessage` e `documentMessage` no `FeaturesCompose.converter_contexto` usando **Gemini 2.5 Flash** como modelo multimodal unificado via `langchain-google-genai`.

## Task Snapshot
- **Primary goal:** Remover os 3 TODOs das linhas 411-413 do `features_compose.py`, permitindo que o bot interprete mídias visuais e documentos recebidos via WhatsApp.
- **Success signal:** O método `converter_contexto()` despacha corretamente para `imageMessage`, `videoMessage` e `documentMessage`, retornando texto descritivo gerado pelo Gemini. Código passa em lint + type-check.
- **Key references:**
  - [Padrão de referência: transcribe_audio](../docs/architecture.md)
  - [Fluxo de dados](../docs/data-flow.md)
  - [Segurança](../docs/security.md)

## Codebase Context

### Arquivos Centrais
| Arquivo | Papel |
|---------|-------|
| `modules/ai_engine/features/features_compose.py` | Facade — método `converter_contexto()` onde ficam os TODOs |
| `modules/ai_engine/features/transcribe_audio/` | Feature de referência para o padrão arquitetural |
| `modules/ai_engine/utils/parameters.py` | Dataclasses de parâmetros |
| `modules/ai_engine/utils/erros.py` | Classes de erro customizadas |
| `modules/ai_engine/utils/types.py` | Type aliases |
| `modules/services/config/context.py` | `RuntimeConfig` — configurações em runtime |
| `modules/services/features/service_hub.py` | `ServiceHub` — acesso centralizado a configs |
| `app/tenants/services/config_loader.py` | `ConfigLoader` — merge config por tenant |
| `app/tenants/models.py` | `TenantConfig` — overrides por tenant |

### Modelo Multimodal Escolhido

**Gemini 2.5 Flash** — único modelo que suporta vídeo completo nativamente:
- Interpreta frames visuais + áudio simultaneamente
- Suporta imagens, vídeos e PDFs inline (base64 < 20MB)
- Custo: $0.30/1M tokens input, $2.50/1M tokens output
- Integração via `langchain-google-genai` → `ChatGoogleGenerativeAI`

### Fluxo Alvo

```
WhatsApp → Evolution API → webhook → MessageData (tipo + metadados com base64/URL)
→ AttendanceOrchestrator._convert_media_context()
→ FeaturesCompose.converter_contexto()
→ _interpret_media() → InterpretMediaUseCase → InterpretMediaDatasource
→ ChatGoogleGenerativeAI (Gemini 2.5 Flash) → texto descritivo
→ Mensagem.conteudo = texto_convertido
```

## Agent Lineup
| Agent | Papel neste plano | Playbook |
| --- | --- | --- |
| Feature Developer | Implementar feature interpret_media + integrar na facade | [Feature Developer](../agents/feature-developer.md) |
| Backend Specialist | Configurar Gemini, ServiceHub, ConfigLoader e dependências | [Backend Specialist](../agents/backend-specialist.md) |
| Database Specialist | Migração Django para TenantConfig | [Database Specialist](../agents/database-specialist.md) |
| Code Reviewer | Validar qualidade, type hints e padrões | [Code Reviewer](../agents/code-reviewer.md) |
| Security Auditor | Auditar tratamento de API keys e dados sensíveis | [Security Auditor](../agents/security-auditor.md) |

## Risk Assessment

### Identified Risks
| Risco | Probabilidade | Impacto | Mitigação | Owner |
| --- | --- | --- | --- | --- |
| Limite de 20MB inline do Gemini | Baixa | Médio | Vídeos WhatsApp são < 16MB; log warning para arquivos grandes | `feature-developer` |
| Chave de API Google não configurada | Média | Alto | Fallback gracioso com log + mensagem placeholder | `backend-specialist` |
| Latência do Gemini em vídeos longos | Baixa | Médio | Timeout configurável, processamento assíncrono via Celery | `feature-developer` |
| Custo inesperado de tokens (vídeos) | Baixa | Baixo | Limite de tamanho no datasource (_MAX_MEDIA_SIZE_BYTES) | `feature-developer` |

### Dependências
- **Interna:** Padrão arquitetural do `transcribe_audio` (já estável e validado)
- **Externa:** API do Google AI (Gemini) — requer chave configurada em `CoreSettings`
- **Técnica:** Nova dependência `langchain-google-genai` no `pyproject.toml`

### Novas Configurações Necessárias
| Chave CoreSettings | Valor Padrão | Descrição |
|---|---|---|
| `vision_provider` | `google` | Provedor de interpretação visual |
| `vision_model` | `gemini-2.5-flash` | Modelo multimodal |
| `google_api_key` | _(encrypted)_ | Chave API Google AI |

## Working Phases

### Phase 1 — Planejamento e Configuração (PREVC: P)
> **Primary Agent:** `backend-specialist` - [Playbook](../agents/backend-specialist.md)

**Objetivo:** Preparar toda a infraestrutura de configuração para a nova feature.

**Tasks**

| # | Task | Agent | Status | Entregável |
|---|------|-------|--------|------------|
| 1.1 | Adicionar `langchain-google-genai>=2.1.0` ao `pyproject.toml` | `backend-specialist` | pending | pyproject.toml atualizado |
| 1.2 | Adicionar campos `vision_provider`, `vision_model`, `google_api_key` ao `RuntimeConfig` | `backend-specialist` | pending | context.py atualizado |
| 1.3 | Adicionar 3 properties + `ChatGoogleGenerativeAI` no `ServiceHub._resolve_llm_class` | `backend-specialist` | pending | service_hub.py atualizado |
| 1.4 | Atualizar `ConfigLoader` para merge de vision configs | `backend-specialist` | pending | config_loader.py atualizado |
| 1.5 | Adicionar campos `vision_provider` e `vision_model` ao `TenantConfig` | `database-specialist` | pending | models.py atualizado |
| 1.6 | Adicionar campos ao `TenantConfigInline` no admin | `backend-specialist` | pending | admin.py atualizado |
| 1.7 | Adicionar 3 entradas no `coresettings.json` | `backend-specialist` | pending | coresettings.json atualizado |
| 1.8 | Adicionar 3 env mappings no `bootstrap_core_settings.py` | `backend-specialist` | pending | bootstrap_core_settings.py atualizado |

**Commit Checkpoint:** `feat(config): adicionar configurações de interpretação de mídia via Gemini`

---

### Phase 2 — Implementação da Feature (PREVC: E)
> **Primary Agent:** `feature-developer` - [Playbook](../agents/feature-developer.md)

**Objetivo:** Implementar a feature `interpret_media` seguindo o padrão do `transcribe_audio`.

**Tasks**

| # | Task | Agent | Status | Entregável |
|---|------|-------|--------|------------|
| 2.1 | Criar `InterpretMediaError` em `utils/erros.py` | `feature-developer` | pending | Classe de erro |
| 2.2 | Criar `InterpretMediaParameters` em `utils/parameters.py` | `feature-developer` | pending | Dataclass de parâmetros |
| 2.3 | Criar aliases `IMData` e `IMUsecase` em `utils/types.py` | `feature-developer` | pending | Type aliases |
| 2.4 | Criar estrutura de diretórios `features/interpret_media/` com `__init__.py` | `feature-developer` | pending | 5 arquivos `__init__.py` |
| 2.5 | Implementar `InterpretMediaDatasource` com lógica Gemini | `feature-developer` | pending | Datasource funcional |
| 2.6 | Implementar `InterpretMediaUseCase` com validações | `feature-developer` | pending | Usecase funcional |
| 2.7 | Implementar `_interpret_media()` no `FeaturesCompose` | `feature-developer` | pending | Método privado |
| 2.8 | Atualizar `converter_contexto()` — substituir 3 TODOs | `feature-developer` | pending | Handlers implementados |
| 2.9 | Atualizar exportações no `modules/ai_engine/__init__.py` | `feature-developer` | pending | `__all__` atualizado |
| 2.10 | Gerar migração Django (`uv run task makemigrations`) | `database-specialist` | pending | Arquivo de migração |

**Commit Checkpoint:** `feat(ai-engine): implementar interpretação de mídias via Gemini 2.5 Flash`

---

### Phase 3 — Validação e Revisão (PREVC: V)
> **Primary Agent:** `code-reviewer` - [Playbook](../agents/code-reviewer.md)

**Objetivo:** Validar qualidade, types e aderência aos padrões do projeto.

**Tasks**

| # | Task | Agent | Status | Entregável |
|---|------|-------|--------|------------|
| 3.1 | Executar `uv run task format` | `code-reviewer` | pending | Código formatado |
| 3.2 | Executar `uv run task lint` sem erros | `code-reviewer` | pending | Lint limpo |
| 3.3 | Executar `uv run task type-check` sem erros | `code-reviewer` | pending | Types validados |
| 3.4 | Verificar migração Django gera corretamente | `database-specialist` | pending | Migração válida |
| 3.5 | Revisar aderência ao padrão do `transcribe_audio` | `code-reviewer` | pending | Relatório de revisão |
| 3.6 | Auditar tratamento seguro de `google_api_key` | `security-auditor` | pending | Sem keys em logs |

**Commit Checkpoint:** `chore(validate): validação de lint, types e segurança da feature interpret_media`

## Arquivos Impactados

### Novos (7 arquivos)
```
features/interpret_media/__init__.py
features/interpret_media/datasource/__init__.py
features/interpret_media/datasource/interpret_media_datasource.py
features/interpret_media/domain/__init__.py
features/interpret_media/domain/usecase/__init__.py
features/interpret_media/domain/usecase/interpret_media_usecase.py
app/tenants/migrations/XXXX_add_vision_fields.py  (auto-gerado)
```

### Modificados (10 arquivos)
```
pyproject.toml
modules/ai_engine/utils/erros.py
modules/ai_engine/utils/parameters.py
modules/ai_engine/utils/types.py
modules/ai_engine/features/features_compose.py
modules/ai_engine/__init__.py
modules/services/config/context.py
modules/services/features/service_hub.py
app/tenants/services/config_loader.py
app/tenants/models.py
app/tenants/admin.py
scripts/config_global/coresettings.json
app/settings_manager/management/commands/bootstrap_core_settings.py
```

## Rollback Plan

### Triggers de Rollback
- Falha na integração com Gemini API (chave inválida, modelo indisponível)
- Erros de type-check irresolúveis
- Conflitos de migração Django

### Procedimento
1. **Phase 1:** Reverter commits de configuração, remover dependência
2. **Phase 2:** Reverter commits de implementação, manter TODOs originais
3. **Migração:** `python manage.py migrate tenants XXXX_anterior` para reverter campos

## Evidence & Follow-up

### Artifacts
- Logs de `uv run task lint` e `uv run task type-check` limpos
- Migração Django gerada com sucesso
- Configurações carregando via `SERVICEHUB`

### Success Metrics
- `converter_contexto()` retorna texto para `imageMessage`, `videoMessage`, `documentMessage`
- Código passa em ruff + pyright strict
- Migração aplica sem erros
