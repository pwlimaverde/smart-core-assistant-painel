---
trigger: model_decision
description: Protocolo unificado e obrigatório para criação, manipulação e fluxo de trabalho de tarefas usando o Task Master (CLI Only).
globs: "**/*"
---

# Referência Completa de Comandos CLI - Task Master

> **IMPORTANTE**: Os comandos abaixo são a **ÚNICA** forma permitida de manipular tasks neste projeto.
> **NUNCA** edite o arquivo `tasks.json` manualmente. Use exclusivamente a CLI.

---

## 1. Navegação e Visualização

### `task-master list`
Lista todas as tasks do projeto.

```bash
# Listar todas as tasks
task-master list

# Listar tasks com um status específico
task-master list --status=pending

# Listar incluindo subtasks
task-master list --with-subtasks

# Combinação de filtros
task-master list --status=in-progress --with-subtasks
```

### `task-master show <id>`
Exibe detalhes completos de uma task específica.

```bash
# Ver detalhes de uma task
task-master show 5

# Ver uma subtask específica (subtask 2 da task 5)
task-master show 5.2
```

### `task-master next`
Mostra a próxima task a ser trabalhada com base em dependências e prioridade.

```bash
task-master next
```

---

## 2. Criação de Tasks

### `task-master add-task`
Adiciona uma nova task usando IA para gerar detalhes a partir de um prompt em linguagem natural.

```bash
# Criar uma nova task com descrição
task-master add-task --prompt="Descrição detalhada da nova funcionalidade"

# Criar com dependências de outras tasks
task-master add-task --prompt="Descrição" --dependencies=1,2,3

# Criar com prioridade definida
task-master add-task --prompt="Descrição" --priority=high
```

**Parâmetros:**
| Parâmetro | Descrição |
|-----------|-----------|
| `--prompt` | (Obrigatório) Texto descrevendo a task a ser criada |
| `--dependencies` | (Opcional) IDs das tasks das quais esta depende, separados por vírgula |
| `--priority` | (Opcional) Prioridade: `low`, `medium`, `high` |

---

## 3. Atualização de Tasks

### `task-master update-task`
Atualiza uma task existente com novas informações. A IA processa o prompt e modifica os campos relevantes.

```bash
# Atualizar uma task com novas informações
task-master update-task --id=5 --prompt="Adicionar suporte a PostgreSQL ao invés de SQLite"

# Usar pesquisa (Perplexity AI) para embasar a atualização
task-master update-task --id=5 --prompt="Pesquisar melhores práticas" --research

# Atualizar uma subtask específica
task-master update-task --id=5.2 --prompt="Adicionar rate limiting de 100 req/min"
```

**⚠️ CRÍTICO**: O comando `update-task` usa `--prompt`, **NÃO** `--details`. A IA interpreta o prompt e atualiza os campos `title`, `description`, `details` e `testStrategy` conforme apropriado.

**Parâmetros:**
| Parâmetro | Descrição |
|-----------|-----------|
| `--id` | (Obrigatório) ID da task ou subtask (ex: `5` ou `5.2`) |
| `--prompt` | (Obrigatório) Texto com as instruções de atualização |
| `--research` | (Opcional) Usar Perplexity AI para pesquisa |

---

## 4. Controle de Status

### `task-master set-status`
Altera o status de uma task ou subtask.

```bash
# Marcar task como em progresso
task-master set-status --id=5 --status=in-progress

# Marcar task como concluída
task-master set-status --id=5 --status=done

# Marcar subtask como concluída
task-master set-status --id=5.2 --status=done
```

**Status disponíveis:**
| Status | Descrição |
|--------|-----------|
| `pending` | Aguardando início |
| `in-progress` | Em andamento |
| `done` | Concluída |
| `review` | Em revisão |
| `deferred` | Adiada |
| `cancelled` | Cancelada |

---

## 5. Subtasks

### `task-master expand`
Expande uma task em subtasks usando IA.

```bash
# Expandir uma task específica em subtasks
task-master expand --id=5

# Expandir com número específico de subtasks
task-master expand --id=5 --num=5

# Expandir com contexto adicional
task-master expand --id=5 --prompt="Focar em testes unitários"

# Expandir todas as tasks pendentes
task-master expand --all

# Forçar regeneração de subtasks existentes
task-master expand --all --force

# Usar pesquisa para embasar a expansão
task-master expand --id=5 --research
```

### `task-master add-subtask`
Adiciona uma subtask manualmente a uma task existente.

```bash
# Adicionar subtask com título
task-master add-subtask --parent=5 --title="Criar migrations do banco"

# Adicionar subtask com título e descrição
task-master add-subtask --parent=5 --title="Criar migrations" --description="Descrição detalhada"

# Converter uma task existente em subtask
task-master add-subtask --parent=5 --task-id=10
```

### `task-master remove-subtask`
Remove uma subtask de uma task.

```bash
# Remover subtask
task-master remove-subtask --id=5.2

# Remover e converter para task standalone
task-master remove-subtask --id=5.2 --convert
```

### `task-master clear-subtasks`
Remove todas as subtasks de uma task.

```bash
# Limpar subtasks de uma task específica
task-master clear-subtasks --id=5

# Limpar subtasks de todas as tasks
task-master clear-subtasks --all
```

---

## 6. Remoção de Tasks

### `task-master remove-task`
Remove permanentemente uma task.

```bash
# Remover task com confirmação
task-master remove-task --id=5

# Remover sem pedir confirmação
task-master remove-task --id=5 -y
```

---

## 7. Dependências

### `task-master add-dependency`
Adiciona uma dependência a uma task.

```bash
task-master add-dependency --id=5 --depends-on=3
```

### `task-master remove-dependency`
Remove uma dependência de uma task.

```bash
task-master remove-dependency --id=5 --depends-on=3
```

### `task-master validate-dependencies`
Identifica dependências inválidas.

```bash
task-master validate-dependencies
```

### `task-master fix-dependencies`
Corrige automaticamente dependências inválidas.

```bash
task-master fix-dependencies
```

---

## 8. Análise e Pesquisa

### `task-master analyze-complexity`
Analisa a complexidade das tasks e gera recomendações de expansão.

```bash
# Analisar complexidade
task-master analyze-complexity

# Usar pesquisa para análise
task-master analyze-complexity --research

# Definir threshold de complexidade
task-master analyze-complexity --threshold=5
```

### `task-master complexity-report`
Exibe o relatório de análise de complexidade.

```bash
task-master complexity-report
```

### `task-master research`
Realiza pesquisa com IA sobre um tópico.

```bash
# Pesquisar um tópico
task-master research "Como implementar autenticação JWT em Django"

# Pesquisar com contexto de tasks específicas
task-master research "autenticação" -i=5,6

# Salvar resultado em arquivo
task-master research "tópico" -s=resultado.md
```

---

## 9. Configuração

### `task-master models`
Gerencia configuração de modelos de IA.

```bash
# Ver configuração atual
task-master models

# Configurar modelos interativamente
task-master models --setup

# Definir modelo principal
task-master models --set-main=gpt-4

# Definir modelo de pesquisa
task-master models --set-research=perplexity
```

---

## Resumo de Erros Comuns

| ❌ Erro Comum | ✅ Comando Correto |
|--------------|-------------------|
| `update-task --id=5 --details="..."` | `update-task --id=5 --prompt="..."` |
| `add-task --description="..."` | `add-task --prompt="..."` |
| `set-status 5 done` | `set-status --id=5 --status=done` |
| Editar `tasks.json` manualmente | Usar sempre a CLI |

---

# Guia de Desenvolvimento com Task Master (Source of Truth: `tasks.json`)

Este documento define o fluxo de trabalho **OBRIGATÓRIO** para Agentes de IA neste projeto.

> **Fonte da Verdade**: O estado real do projeto reside em `.taskmaster/tasks/tasks.json`.
> **Ferramenta Única**: A CLI `task-master` é a **ÚNICA** forma permitida de interagir com as tasks.
> **PROIBIDO**: O uso de ferramentas MCP para manipulação de tasks é proibido. Use apenas a CLI.
> **CRÍTICO - PROIBIDO EDIÇÃO MANUAL**: As alterações no `tasks.json` devem ser feitas **EXCLUSIVAMENTE** via CLI.

---

## 1. Regra Fundamental: Integração Planejamento -> Task Master

Para **TODA** nova feature ou correção significativa, o fluxo é obrigatório:

1.  **Planejamento**: Criar `implementation_plan.md` e obter aprovação do usuário.
2.  **Registro Imediato**: Assim que aprovado, você **DEVE** registrar o plano no Task Master via CLI.
3.  **Execução**: Só então, inicie a codificação, marcando o progresso no Task Master.

### 1.1 Checklist de Validação do Registro
Antes de começar a codar, verifique se a task criada no Task Master contém:
- [ ] **Título**: Com prefixo padrão (ex: `[FEAT]`, `[FIX]`).
- [ ] **Detalhes**: Cópia **integral** do conteúdo técnico do `implementation_plan.md` em **PORTUGUÊS**.
- [ ] **Estratégia de Teste**: Copiada do plano (em **PORTUGUÊS**).

---

## 2. Fluxo de Comandos CLI

### 2.1 Passo 1: Seleção e Início
Identifique a próxima tarefa priorizada:

```bash
task-master next
```

Inicie a implementação marcando status como `in-progress`:

```bash
task-master set-status --id=<ID> --status=in-progress
```

### 2.2 Passo 2: Criação de Novas Tasks

Ao receber um novo plano aprovado, crie a task:

```bash
# 1. Criar a task com prompt descritivo
task-master add-task --prompt="[FEAT] Título da Feature. Contexto: descrever o que será implementado, arquivos afetados, requisitos técnicos, estratégia de teste." --priority=high

# 2. Expandir em subtasks se necessário
task-master expand --id=<ID_GERADO> --prompt="Contexto adicional do plano"
```

### 2.3 Passo 3: Atualização de Tasks Existentes

Se precisar adicionar mais informações a uma task:

```bash
# Atualizar com instruções claras para a IA
task-master update-task --id=25 --prompt="Adicionar ao campo details: ## Implementação Técnica... (conteúdo completo)"
```

### 2.4 Passo 4: Execução e Subtasks

Conforme avança, marque as subtasks como prontas:

```bash
task-master set-status --id=25.1 --status=done
task-master set-status --id=25.2 --status=done
```

### 2.5 Passo 5: Finalização

Marque a task principal como concluída:

```bash
task-master set-status --id=25 --status=done
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

---

## 4. Do Plano à Task (Protocolo de Transformação)

### 4.1. Regra Fundamental: Captura Total

**VOCÊ DEVE ENGLOBAR 100% DO PLANEJAMENTO FORNECIDO NA TASK.**

*   ❌ **NÃO** omita dados, regras de negócio ou edge cases.
*   ❌ **NÃO** simplifique integrações.
*   ✅ **TRANSFIRA** toda informação via `--prompt` no `add-task` ou `update-task`.

### 4.2. Checklist de Validação

Antes de considerar a task criada, verifique:
1.  [ ] **Completude**: Todos os requisitos estão na task?
2.  [ ] **Arquivos**: Todos os arquivos afetados foram mencionados?
3.  [ ] **Integrações**: Detalhes de APIs e banco foram incluídos?
4.  [ ] **Testes**: A estratégia de testes foi informada?
5.  [ ] **Idioma**: O conteúdo está 100% em **PORTUGUÊS**?