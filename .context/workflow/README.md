# Workflow PREVC

Este diretório gerencia o workflow de desenvolvimento estruturado usando o sistema PREVC (Planning, Review, Execution, Validation, Confirmation).

## Estrutura

```
workflow/
├── README.md           # Este arquivo
├── status.yaml         # Estado atual do workflow
└── docs/               # Outputs de cada fase
    ├── prd.md          # Product Requirements (P)
    ├── technical-spec.md # Especificação técnica (P)
    ├── architecture.md # Decisões de arquitetura (R)
    ├── adr/            # Architecture Decision Records (R)
    ├── test-report.md  # Relatório de testes (V)
    └── changelog.md    # Changelog da release (C)
```

## Fases PREVC

### P - Planning (Planejamento)

**Objetivo:** Definir o que construir

**Atividades:**
- Levantar requisitos
- Escrever especificações
- Identificar escopo
- Definir critérios de aceite

**Outputs:**
- PRD (Product Requirements Document)
- Technical Specification

**Roles:** Product Owner, Architect

### R - Review (Revisão)

**Objetivo:** Validar o approach

**Atividades:**
- Revisão de arquitetura
- Design técnico
- Avaliação de riscos
- Decisões arquiteturais (ADRs)

**Outputs:**
- Architecture Document
- ADRs
- Risk Assessment

**Roles:** Architect, Tech Lead

### E - Execution (Execução)

**Objetivo:** Construir o que foi planejado

**Atividades:**
- Implementar código
- Seguir specs aprovadas
- Escrever testes unitários
- Code review entre pares

**Outputs:**
- Código implementado
- Testes unitários

**Roles:** Developer, AI Agent

### V - Validation (Validação)

**Objetivo:** Verificar que funciona

**Atividades:**
- Executar testes
- QA manual
- Code review contra specs
- Verificar critérios de aceite

**Outputs:**
- Test Report
- Approval

**Roles:** QA, Code Reviewer

### C - Confirmation (Confirmação)

**Objetivo:** Entregar e documentar

**Atividades:**
- Atualizar documentação
- Gerar changelog
- Deploy (se aplicável)
- Handoff para stakeholders

**Outputs:**
- Documentation updates
- Changelog
- Release notes

**Roles:** Developer, DevOps

## Comandos

```bash
# Iniciar workflow interativo
npx @ai-coders/context workflow

# Ver status atual
cat .context/workflow/status.yaml

# Criar novo plano
npx @ai-coders/context plan "nome-da-feature"
```

## Escalas de Projeto

| Escala | Fases Incluídas | Exemplo |
|--------|-----------------|---------|
| TRIVIAL | E, C | Typo fix |
| SMALL | E, V, C | Bug fix simples |
| MEDIUM | P, E, V, C | Feature pequena |
| LARGE | P, R, E, V, C | Feature complexa |
| ENTERPRISE | P, R, E, V, C (expandido) | Projeto grande |

## Transições de Fase

```
P (Planning)
    ↓ specs aprovadas
R (Review)
    ↓ design aprovado
E (Execution)
    ↓ código completo
V (Validation)
    ↓ testes passam
C (Confirmation)
    ↓ documentado
[Completo]
```

## Integração com Skills

Cada fase tem skills associados:

| Fase | Skills |
|------|--------|
| P | feature-breakdown, api-design |
| R | code-review, security-audit |
| E | commit-message, refactoring, documentation |
| V | test-generation, pr-review, code-review |
| C | documentation, commit-message |
