# Guia de Desenvolvimento com Task Master (Source of Truth: `tasks.json`)

Este documento define o fluxo de trabalho **OBRIGATÓRIO** para Agentes de IA neste projeto.

> **Fonte da Verdade**: O estado real do projeto reside em `.taskmaster/tasks/tasks.json`.
> **Ferramenta de Leitura e Escrita**: A CLI `task-master` deve ser usada para visualização rápida e seleção e registro de tarefas.
---

## 1. Localização e Estrutura

*   **Arquivo Mestre**: `c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/.taskmaster/tasks/tasks.json`
*   **Estrutura do JSON**:
    ```json
    {
      "master": {
        "tasks": [
          {
            "id": 12,
            "status": "pending", // Valores: "pending", "in-progress", "done"
            "subtasks": [
              { "id": 1, "status": "pending", ... }
            ]
            ...
          }
        ]
      }
    }
    ```

---

## 2. Fluxo de Trabalho Passo-a-Passo

### Passo 1: Seleção e Início (Start)

1.  **Identifique a Tarefa**:
    Use a CLI para encontrar a próxima prioridade.
    ```powershell
    task-master next
    ```
    *Saída*: `[ID: 24] [High] Investigação de Desempenho...`

2.  **Inicie a Tarefa**:
    *   **Ação**: Use o comando de update com prompt em linguagem natural.
    *   **Comando**:
        ```powershell
        task-master update -p "Mark task 24 as in-progress"
        ```
    *   **Nota**: A IA do Task Master interpretará seu pedido e atualizará o JSON.

### Passo 2: Execução Detalhada (Execution)

Para cada sub-tarefa (definida no `subtasks` do JSON):

1.  **Analise o Detalhe**: Leia `details` e `testStrategy` via `task-master list --with-subtasks`.
2.  **Implemente**: Crie o código necessário.
3.  **Atualize a Subtask**:
    *   **Ação**: Use a CLI para marcar a subtask como concluída.
    *   **Comando**:
        ```powershell
        task-master update -p "Mark subtask 1 of task 24 as done"
        ```
    *   *Nota*: Seja específico com IDs ou descrições para evitar ambiguidade.

> **Uso do `task.md` (Artifact)**: Mantenha seu `task.md` atualizado para controle granular, mas a **oficialização** é sempre via CLI.

### Passo 3: Finalização (Finish)

Quando todas as subtasks estiverem concluídas:

1.  **Verificação Final**: Garanta que os testes passaram.
2.  **Conclusão**:
    *   **Comando**:
        ```powershell
        task-master update -p "Mark task 24 as done"
        ```
3.  **Validação**:
    ```powershell
    task-master list --status done
    ```

---

## Resumo de Comandos e Ações

| Etapa | Ferramenta | Ação / Comando |
| :--- | :--- | :--- |
| **O que fazer agora?** | CLI | `task-master next` |
| **Ver contexto geral** | CLI | `task-master list --with-subtasks` |
| **Iniciar/Atualizar** | CLI | `task-master update -p "Instrução em linguagem natural"` |
| **Finalizar Tarefa** | CLI | `task-master update -p "Mark task X as done"` |

---

## Dicas para a IA (Você)

*   **Seja Cirúrgico**: Ao editar o `tasks.json`, altere **apenas** os campos de status. Não reescreva descrições ou delete tarefas a menos que explicitamente solicitado.
*   **Use `grep` ou `find`**: Para localizar rapidamente a tarefa no JSON antes de editar, se o arquivo for muito grande.
*   **Consistência**: Se você notar que o `tasks.json` está desatualizado em relação ao código, pergunte ao usuário antes de fazer alterações em massa.
