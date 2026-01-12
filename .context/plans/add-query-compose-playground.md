---
status: active
generated: 2026-01-12
linked-openspec: add-query-compose-playground
---

# Playground de Simulação Query Compose Plan

> Adicionar Playground de Simulação na tela verificar-query-compose para testar respostas do assistente sem enviar mensagens reais via WhatsApp.

## Task Snapshot

- **Primary goal:** Permitir testar respostas do assistente baseadas em QueryCompose sem enviar mensagens reais via WhatsApp.
- **Success signal:** Seção Playground funcional na tela `verificar-query-compose` com visualização de intent, comportamento, RAG e resposta final.
- **Key references:**
  - [Documentation Index](../docs/README.md)
  - [Agent Handbook](../agents/README.md)
  - [OpenSpec Proposal](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/openspec/changes/add-query-compose-playground/proposal.md)
  - [OpenSpec Tasks](file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/openspec/changes/add-query-compose-playground/tasks.md)

## Codebase Context

- **Total files analyzed:** 381
- **Total symbols discovered:** 605
- **Architecture layers:** Services, Repositories, Config, Controllers, Models, Components, Utils

### Componentes Relevantes

**Views Existentes:**

- `verificar_query_compose()` @ `treinamento/views.py:385` - View alvo para adicionar Playground
- `cadastrar_query_compose()` @ `treinamento/views.py:452` - View de cadastro de queries

**Módulo de IA:**

- `FeaturesCompose` @ `modules/ai_engine/features/features_compose.py` - Lógica de processamento
  - `generate_embeddings()` - Gera embeddings da mensagem
  - `analise_previa_mensagem()` - Análise prévia de intent
  - `analise_mensage()` - Análise completa e resposta

**Modelos:**

- `QueryCompose` @ `treinamento/models.py` - Modelo de intenções
  - `buscar_comportamento_similar()` - Busca comportamento por embedding
  - `build_intent_types_config()` - Configuração de tipos de intent
  - `to_embedding_text()` - Converte para texto de embedding

**Templates:**

- `verificar_query_compose.html` - Template alvo para UI do Playground

## Agent Lineup

| Agent               | Papel neste plano                         | Playbook                                                   |
| ------------------- | ----------------------------------------- | ---------------------------------------------------------- |
| Backend Specialist  | Criar endpoint AJAX e lógica de simulação | [backend-specialist.md](../agents/backend-specialist.md)   |
| Frontend Specialist | Implementar UI do Playground no template  | [frontend-specialist.md](../agents/frontend-specialist.md) |
| Security Auditor    | Validar permissões e rate limiting        | [security-auditor.md](../agents/security-auditor.md)       |
| Code Reviewer       | Revisar código final                      | [code-reviewer.md](../agents/code-reviewer.md)             |

## Mapeamento OpenSpec ↔ AI-Context

| Fase OpenSpec     | Tasks         | Agente Principal     |
| ----------------- | ------------- | -------------------- |
| Fase 1: Backend   | 1.1, 1.2, 1.3 | Backend Specialist   |
| Fase 2: Frontend  | 2.1, 2.2, 2.3 | Frontend Specialist  |
| Fase 3: Polimento | 3.1, 3.2      | Code Reviewer + Docs |

## Fluxo de Processamento (Referência)

```
Mensagem do Usuário
        ↓
[1] generate_embeddings() - Gera embedding
        ↓
[2] buscar_comportamento_similar() - Busca QueryCompose
        ↓
[3] build_intent_types_config() - Tipos de intent
        ↓
[4] analise_previa_mensagem() - Detecta intent
        ↓
[5] (opcional) buscar_documentos_similares() - RAG
        ↓
[6] analise_mensage() - Gera resposta LLM
        ↓
Resposta Simulada (sem persistência)
```

## Risk Assessment

### Identified Risks

| Risk                     | Probability | Impact | Mitigation                          |
| ------------------------ | ----------- | ------ | ----------------------------------- |
| Consumo de tokens de API | Alta        | Média  | Rate limiting e aviso ao usuário    |
| Timeout em LLM           | Média       | Média  | Timeout de 30s e tratamento de erro |
| Acesso não autorizado    | Baixa       | Alta   | Usar `_can_access_training()`       |

### Dependencies

- **Internal:** `FeaturesCompose`, `QueryCompose`, sistema de permissões
- **External:** OpenAI/Groq API para embeddings e LLM

## Working Phases

### Phase 1 — Backend (Tasks 1.1, 1.2, 1.3)

**Steps:**

1. Criar rota `playground-query-compose/` em `urls.py`
2. Implementar view `playground_query_compose()` com AJAX
3. Integrar com `FeaturesCompose` para simulação
4. Implementar tratamento de erros e timeout

**Commit Checkpoint:** `feat(treinamento): add playground backend endpoint`

### Phase 2 — Frontend (Tasks 2.1, 2.2, 2.3)

**Steps:**

1. Adicionar seção Playground no template
2. Implementar JavaScript para chamada AJAX
3. Renderizar resultados (intent, comportamento, RAG, resposta)

**Commit Checkpoint:** `feat(treinamento): add playground frontend UI`

### Phase 3 — Polimento (Tasks 3.1, 3.2)

**Steps:**

1. Adicionar animações e feedback visual
2. Atualizar documentação

**Commit Checkpoint:** `docs(treinamento): document playground feature`

## Verificação

### Testes Manuais

1. Acessar `/treinamento/verificar-query-compose/`
2. Localizar seção "Playground - Simular Atendimento"
3. Digitar mensagem de teste (ex: "Qual é o preço do produto X?")
4. Clicar em "Simular Resposta"
5. Verificar:
   - Intent detectado aparece
   - Comportamento ativado exibido
   - Resposta final renderizada
   - Tempo de processamento mostrado

### Validação de Permissões

1. Acessar como usuário sem permissão `treinamento`
2. Verificar que endpoint retorna 403

## Evidence & Follow-up

- [ ] Endpoint funcional e seguro
- [ ] UI integrada e responsiva
- [ ] Nenhum dado persistido
- [ ] Erros tratados graciosamente
- [ ] Código formatado (`uv run task format`)
- [ ] Tipos verificados (`uv run task type-check`)
