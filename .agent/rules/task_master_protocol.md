---
trigger: always_on
---

---
description: Protocolo unificado e obrigatório para criação, manipulação e fluxo de trabalho de tarefas usando o Task Master (CLI Only).
globs: "**/*"
alwaysApply: true
---

# Guia de Desenvolvimento com Task Master (Source of Truth: `tasks.json`)

Este documento define o fluxo de trabalho **OBRIGATÓRIO** para Agentes de IA neste projeto.

> **Fonte da Verdade**: O estado real do projeto reside em `.taskmaster/tasks/tasks.json`.
> **Ferramenta Única**: A CLI `task-master` é a **ÚNICA** forma permitida de interagir com as tasks. Execute `task-master --help` para entender os comandos disponíveis e o fluxo de trabalho.
> **PROIBIDO**: O uso de ferramentas MCP para manipulação de tasks é proibido. Use apenas a CLI.
> **CRÍTICO - PROIBIDO EDIÇÃO MANUAL**: As alterações no `tasks.json` devem ser feitas **EXCLUSIVAMENTE** via CLI.

---

## 1. Regra Fundamental: Integração Planejamento -> Task Master

Para **TODA** nova feature ou correção significativa, o fluxo é obrigatório:

1.  **Planejamento**: Criar `implementation_plan.md` e obter aprovação do usuário.
2.  **Registro Imediato**: Assim que aprovado (ou antes de começar a codar), você **DEVE** registrar o plano no Task Master via CLI.
3.  **Execução**: Só então, inicie a codificação, marcando o progresso no Task Master passo a passo com `update`.

### 1.1 Checklist de Validação do Registro
Antes de começar a codar, verifique se a task criada no Task Master contém:
- [ ] **Título**: Com prefixo padrão (ex: `[FEAT]`, `[FIX]`).
- [ ] **Detalhes**: Cópia **integral** do conteúdo técnico do `implementation_plan.md` em **PORTUGUÊS**.
- [ ] **Estratégia de Teste**: Copiada do plano (em **PORTUGUÊS**).

---

## 2. Fluxo de Comandos CLI

### 2.1 Passo 1: Seleção e Início (Start)
Identifique a próxima tarefa priorizada.

```powershell
task-master next
```

Inicie a task e as subtasks (isso muda o status para 'in-progress'). **É OBRIGATÓRIO definir o status como `in-progress` ao iniciar a implementação:**

```powershell
task-master update-task --id <ID> --status in-progress
```

### 2.2 Passo 2: Criação de Novas Tasks (Registro do Plano)

Ao receber um novo plano aprovado, crie a task.

1. **Adicionar Cabeçalho**:
    ```powershell
    task-master add-task --description "[PREFIXO] Título da Feature" --priority high
    ```
    *(Anote o ID gerado, ex: 25)*

2. **Popular Detalhes (O PASSO MAIS IMPORTANTE)**:
    Transfira o `implementation_plan.md` para o campo `details` via update.
    ```powershell
    task-master update-task --id 25 --details "## Contexto... (todo o markdown do plano em PORTUGUÊS)"
    ```

### 2.3 Passo 3: Execução e Subtasks

Se a task for complexa, quebre em subtasks **após** criar a task principal.

```powershell
# Expandir automaticamente baseado na descrição (AI)
task-master expand --id 25

# OU adicionar manualmente (se preferir controle total)
task-master add-subtask --taskId 25 --title "Criar Model"
```

Conforme avança, marque as subtasks como prontas:

```powershell
task-master set-status --id <SUBTASK_ID> --status done
```

### 2.4 Passo 4: Finalização

1.  Verifique se todos os testes passam (conforme `testStrategy`).
2.  Marque a task principal como concluída (status `done`). **É OBRIGATÓRIO marcar como `done` ao finalizar:**

```powershell
task-master set-status --id 25 --status done
```

---

## 3. Padrões de Conteúdo

### 3.1 Prefixos de Título
| Prefixo | Uso |
|:---|:---|
| `[FEAT]` | Nova Feature |
| `[FIX]` | Correção de Bug |
| `[REFACTOR]` | Refatoração |
| `[INFRA]` | Infraestrutura |
| `[ATD]` | Atendimento |
| `[OPS]` | Operacional |

### 3.2 Estrutura do Campo `details`
Este campo deve ser rico e conter Markdown. **Não resuma o plano**. O idioma deve ser **PORTUGUÊS**.

```markdown
## Contexto
[Por que?]

## Requisitos
[Lista completa]

## Implementação Técnica
### [Arquivo X]
- Mudanças: ...
- Regras: ...

## Integrações
...
```

---

## 4. Resumo de Comandos Úteis

| Ação | Comando |
| :--- | :--- |
| **Listar tudo** | `task-master list` |
| **Próxima tarefa** | `task-master next` |
| **Adicionar Task** | `task-master add-task --description "..."` |
| **Atualizar Detalhes** | `task-master update-task --id <ID> --details "..."` |
| **Expandir (AI)** | `task-master expand --id <ID>` |
| **Status (Task)** | `task-master set-status --id <ID> --status done` |

> **Nota para a IA**: Você tem permissão e dever de usar esses comandos no terminal (`run_command`) sempre que o status do seu trabalho mudar. Mantenha o Task Master sincronizado com a realidade.

---

## 5. Do Plano à Task (Protocolo de Transformação)

Ao receber um novo **Plano de Implementação**, você deve transformá-lo em uma task do Task Master seguindo este protocolo.

### 5.1. Regra Fundamental: Captura Total

**VOCÊ DEVE ENGLOBAR 100% DO PLANEJAMENTO FORNECIDO NA TASK.**

*   ❌ **NÃO** omita dados, regras de negócio ou edge cases.
*   ❌ **NÃO** simplifique integrações.
*   ✅ **TRANSFIRA** toda informação para o campo `details` da task.

Se uma informação existe no plano, ela **DEVE** existir na task gerada.

### 5.2. Checklist de Validação da Transformação

Antes de considerar a task criada, verifique:
1.  [ ] **Completude**: Todos os requisitos funcionais e regras de negócio do plano estão no `details`?
2.  [ ] **Arquivos**: Todos os arquivos afetados/criados foram listados?
3.  [ ] **Integrações**: Detalhes de banco de dados e APIs foram copiados?
4.  [ ] **Ambiente**: Variáveis de ambiente foram listadas?
5.  [ ] **Testes**: A estratégia de testes foi preenchida no campo adequado?
6.  [ ] **Idioma**: O conteúdo está 100% em **PORTUGUÊS**?