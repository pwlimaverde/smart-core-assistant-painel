---
trigger: model_decision
description: Fluxo completo para transformar planos de features em tasks estruturadas no Task Master
globs: "**/*"
---

# Guia Completo: Do Plano à Implementação com Task Master

Este documento define o fluxo **obrigatório** para transformar um plano de feature em tasks estruturadas e executá-las até a conclusão.

---

## Fase 1: Transformar o Plano em Mini-PRD

### 1.1 Criar o Arquivo do Mini-PRD

Para cada nova feature, crie um arquivo em:
```
.taskmaster/docs/feature_<nome_da_feature>.txt
```

### 1.2 Estrutura do Mini-PRD

Use a estrutura abaixo (baseada no template RPG). O conteúdo deve estar em **PORTUGUÊS**.

```text
<overview>
## Problema
[Descreva o problema ou necessidade em 2-3 linhas]

## Usuários Alvo
[Quem vai usar esta funcionalidade]

## Métricas de Sucesso
[Como saber se a feature foi bem-sucedida]
</overview>

<functional-decomposition>
## Árvore de Capacidades

### Capacidade: [Nome da Capacidade Principal]
[Descrição breve do que esta capacidade cobre]

#### Feature: [Nome da Feature]
- **Descrição**: [O que faz em uma frase]
- **Entradas**: [O que precisa receber]
- **Saídas**: [O que produz]
- **Comportamento**: [Lógica principal]

#### Feature: [Nome da Feature 2]
- **Descrição**: 
- **Entradas**: 
- **Saídas**: 
- **Comportamento**: 
</functional-decomposition>

<structural-decomposition>
## Estrutura de Arquivos

### Módulo: [Nome do Módulo]
- **Mapeia para capacidade**: [Capacidade do item anterior]
- **Responsabilidade**: [Propósito único e claro]
- **Arquivos**:
  - `arquivo1.py` - [Feature que implementa]
  - `arquivo2.py` - [Feature que implementa]
</structural-decomposition>

<dependency-graph>
## Cadeia de Dependências

### Camada Fundação (Fase 0)
- **[Módulo Base]**: Sem dependências. [O que fornece]

### Camada Core (Fase 1)
- **[Módulo Core]**: Depende de [[módulo-fase-0]]. [O que fornece]

### Camada Aplicação (Fase 2)
- **[Módulo App]**: Depende de [[módulo-fase-1], [módulo-fase-0]]. [O que fornece]
</dependency-graph>

<implementation-roadmap>
## Fases de Desenvolvimento

### Fase 0: Fundação
**Objetivo**: [O que esta fase estabelece]

**Tasks**:
- [ ] [Nome da task] (depende de: nenhuma)
  - Critério de aceite: [Como saber que está pronto]
  - Estratégia de teste: [Como testar]

**Entrega**: [O que funciona após esta fase]

---

### Fase 1: Core
**Objetivo**: [O que esta fase estabelece]

**Entry Criteria**: Fase 0 completa

**Tasks**:
- [ ] [Nome da task] (depende de: [tasks-da-fase-0])
- [ ] [Nome da task] (depende de: [tasks-da-fase-0])

**Entrega**: [O que funciona após esta fase]
</implementation-roadmap>

<test-strategy>
## Estratégia de Testes

### [Nome do Módulo/Feature]
**Caminho feliz**:
- [Cenário de sucesso]
- Esperado: [Resultado]

**Casos de borda**:
- [Cenário de limite]
- Esperado: [Resultado]

**Casos de erro**:
- [Cenário de falha]
- Esperado: [Como o sistema trata]
</test-strategy>
```

---

## Fase 2: Gerar Tasks a partir do Mini-PRD

### 2.1 Comando Principal

```bash
task-master parse-prd --input=".taskmaster/docs/feature_<nome>.txt"
```

### 2.2 Opções Úteis

```bash
# Usar IA de pesquisa para melhor geração
task-master parse-prd --input=".taskmaster/docs/feature_<nome>.txt" --research

# Definir número de tasks a gerar
task-master parse-prd --input=".taskmaster/docs/feature_<nome>.txt" --num-tasks=10
```

### 2.3 Verificar Tasks Geradas

```bash
# Listar todas as tasks
task-master list --with-subtasks

# Ver detalhes de uma task específica
task-master show <ID>
```

### 2.4 Refinar se Necessário

```bash
# Expandir uma task em subtasks
task-master expand --id=<ID> --prompt="Contexto adicional em português"

# Atualizar uma task com mais informações
task-master update-task --id=<ID> --prompt="Adicionar detalhes sobre..."

# Adicionar dependência entre tasks
task-master add-dependency --id=<ID> --depends-on=<ID_ANTERIOR>
```

---

## Fase 3: Executar as Tasks

### 3.1 Iniciar o Trabalho

```bash
# Ver próxima task a trabalhar (respeita dependências)
task-master next

# Marcar como em progresso
task-master set-status --id=<ID> --status=in-progress
```

### 3.2 Durante a Implementação

Para cada task/subtask:

1. **Marcar início**:
   ```bash
   task-master set-status --id=<ID> --status=in-progress
   ```

2. **Implementar** o código conforme especificado na task

3. **Marcar conclusão**:
   ```bash
   task-master set-status --id=<ID> --status=done
   ```

### 3.3 Fluxo de Subtasks

```bash
# Marcar subtasks conforme avança
task-master set-status --id=25.1 --status=done
task-master set-status --id=25.2 --status=done
task-master set-status --id=25.3 --status=done

# Quando todas subtasks estiverem prontas, marcar task principal
task-master set-status --id=25 --status=done
```

### 3.4 Se Encontrar Bloqueios

```bash
# Marcar como pendente/bloqueado
task-master set-status --id=<ID> --status=deferred

# Atualizar com motivo do bloqueio
task-master update-task --id=<ID> --prompt="Bloqueado por: [motivo]. Requer: [o que precisa]"
```

---

## Fase 4: Conferência Final

### 4.1 Verificar Status Geral

```bash
# Listar todas as tasks para conferir status
task-master list --with-subtasks

# Verificar se há tasks pendentes
task-master list --status=pending
```

### 4.2 Checklist de Validação

Antes de considerar a feature completa, verifique:

- [ ] **Todas as tasks estão `done`?**
  ```bash
  task-master list --status=in-progress  # Deve retornar vazio
  task-master list --status=pending      # Deve retornar vazio (para esta feature)
  ```

- [ ] **Código implementado conforme especificado?**
  - Comparar implementação com o Mini-PRD original

- [ ] **Testes passando?**
  - Executar suite de testes do projeto
  - Verificar se cenários do `<test-strategy>` foram cobertos

- [ ] **Documentação atualizada?**
  - README atualizado se necessário
  - Docstrings em novas funções/classes

### 4.3 Relatório de Conclusão

Ao finalizar, criar registro no `implementation_plan.md` ou `walkthrough.md`:

```markdown
## Feature: [Nome]
- **Data de conclusão**: [data]
- **Tasks concluídas**: [lista de IDs]
- **Arquivos modificados**: [lista]
- **Testes adicionados**: [lista]
- **Observações**: [notas importantes]
```

---

## Resumo do Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PLANEJAR                                                    │
│     └─ Criar Mini-PRD em .taskmaster/docs/feature_<nome>.txt    │
├─────────────────────────────────────────────────────────────────┤
│  2. GERAR                                                       │
│     └─ task-master parse-prd --input="<arquivo>"                │
│     └─ task-master expand --id=<ID> (se necessário)             │
├─────────────────────────────────────────────────────────────────┤
│  3. EXECUTAR                                                    │
│     └─ task-master next                                         │
│     └─ task-master set-status --id=<ID> --status=in-progress    │
│     └─ [IMPLEMENTAR]                                            │
│     └─ task-master set-status --id=<ID> --status=done           │
│     └─ [REPETIR para cada task/subtask]                         │
├─────────────────────────────────────────────────────────────────┤
│  4. CONFERIR                                                    │
│     └─ task-master list --status=pending (deve estar vazio)     │
│     └─ Validar implementação vs PRD                             │
│     └─ Verificar testes                                         │
│     └─ Documentar conclusão                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Comandos de Referência Rápida

| Ação | Comando |
|------|---------|
| Gerar tasks do PRD | `task-master parse-prd --input="<arquivo>"` |
| Ver próxima task | `task-master next` |
| Iniciar task | `task-master set-status --id=<ID> --status=in-progress` |
| Concluir task | `task-master set-status --id=<ID> --status=done` |
| Ver detalhes | `task-master show <ID>` |
| Listar todas | `task-master list --with-subtasks` |
| Expandir em subtasks | `task-master expand --id=<ID>` |
| Atualizar task | `task-master update-task --id=<ID> --prompt="..."` |
| Adicionar dependência | `task-master add-dependency --id=<ID> --depends-on=<ID>` |