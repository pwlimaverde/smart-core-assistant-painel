# Plano de Reorganização e Migração (Banco do Zero)

Este documento define, de forma operacional e faseada, como reorganizar o projeto em múltiplos apps, iniciar o banco do zero, remover migrações antigas, manter apenas a 0001 para ser criada e aplicada ao final, mover a habilitação do pgvector para o app de atendimentos e remover o app `oraculo` ao término. Cada fase é independente e possui objetivos, passos, comandos e critérios de saída claros (gate).

**Status Geral: Concluído**

## Contexto de infraestrutura
- Banco hospedado em servidor local: http://192.168.3.127/
- Execução e validação via Docker (Windows), com `uv`/Taskipy
- Sem segredos no código; variáveis sensíveis via `.env` (fornecer `.env.example`)

## Arquitetura alvo (apps)
- operacional: recursos internos (departamentos, atendentes, capacidade)
- clientes: entidades externas (clientes, contatos)
- atendimentos: fluxo de conversas/atendimentos; migração pgvector residirá aqui
- treinamento: base de conhecimento, documentos, vetorização
- oraculo: será removido ao final (compatibilidade temporária durante transição)

## Diretrizes obrigatórias
- Banco do zero: não haverá migrações aplicadas até a Fase Final
- Remoção de migrações atuais: deletar agora todas as migrações existentes (manter apenas `__init__.py`); a 0001 de cada app será criada e aplicada somente na Fase Final
- pgvector: habilitação via `RunSQL("CREATE EXTENSION IF NOT EXISTS vector;")` ficará na migração 0001 do app `atendimentos` (na Fase Final)
- Remoção do `oraculo`: eliminar o app antes de criar as migrações finais; toda lógica deve estar nos novos apps
- Qualidade: manter lint, type-check e testes sempre verdes; pré-migração sem DB real; pós-migração com DB real

## Política de testes por modo
- Pré-migração (Fases 0–9):
  - uv run task lint
  - uv run task type-check
  - uv run task test (foco em lógica de negócio; usar mocks para DB/ORM)
  - Cobertura de negócio ≥ 80%
- Pós-migração (Fase Final):
  - uv run task lint
  - uv run task type-check
  - uv run task test-docker (com DB real e migrações aplicadas)
  - Cobertura global ≥ 80%

---

## Fase 0 — Preparação e limpeza de migrações
**Status: Concluído**
### Objetivo
- Baseline verde e repositório sem migrações (apenas `__init__.py` em cada `migrations/`)

---

## Fase 1 — Esqueleto dos novos apps (sem mover código)
**Status: Concluído**
### Objetivo
- Criar estrutura vazia para operacional, clientes, atendimentos e treinamento

---

## Fase 2 — Mapeamento e plano de movimentação de modelos
**Status: Concluído**
### Objetivo
- Tabelar cada entidade e seu domínio de destino com relacionamentos

---

## Fase 3 — Plano de templates/URLs/views/admin/signals
**Status: Concluído**
### Objetivo
- Planejar divisão por domínio sem mover código ainda

---

## Fase 4 — Compatibilidade temporária (reexports)
**Status: Concluído**
### Objetivo
- Planejar facades no oraculo para manter compatibilidade durante a transição

---

## Fase 5 — Movimentação de código (sem migrações)
**Status: Concluído**
### Objetivo
- Mover models, views, urls, admin, signals e templates para os novos apps mantendo o projeto compilável

---

## Fase 6 — Testes e qualidade (pré‑migração)
**Status: Concluído**
### Objetivo
- Reorganizar testes por app e consolidar cobertura sem DB

---

## Fase 7 — Observabilidade e scripts
**Status: Concluído**
### Objetivo
- Alinhar logs (loguru), tasks (Taskipy) e scripts à nova estrutura

---

## Fase 8 — Documentação e comunicação
**Status: Concluído**
### Objetivo
- Atualizar README/docs/diagramas e guias de uso

---

## Fase 9 — Remoção do app oraculo (antes das migrações)
**Status: Concluído**
### Objetivo
- Remover definitivamente o app oraculo do código e de INSTALLED_APPS

---

## Fase Final — Criação e aplicação das migrações 0001 (com pgvector)
**Status: Concluído**
### Objetivo
- Criar e aplicar as migrações 0001 de cada app e habilitar pgvector no app atendimentos

---

## Checklist resumido por fase (copie para PRs)
- Fase N
  - Lint (uv run task lint): OK
  - Type-check (uv run task type-check): OK
  - Testes (pré: uv run task test | pós: uv run task test-docker): OK
  - Cobertura (pré: negócio ≥ 80% | pós: global ≥ 80%): OK
  - Itens de passos concluídos e documentados

## Observações finais
- Não criar/aplicar migrações antes da Fase Final
- Garantir que `migrations/` contenha apenas `__init__.py` até a Fase Final
- Remover o `oraculo` antes de gerar as migrações 0001
- A migração do pgvector deve existir apenas no app `atendimentos`
