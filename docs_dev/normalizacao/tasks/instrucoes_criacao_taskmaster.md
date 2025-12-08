# Instruções para Criação de Tasks no Task Master

> **Contexto de Uso**: Este documento deve ser fornecido à IA junto com um arquivo de planejamento (ex: `plano.md`). A IA deve analisar ambos os documentos e gerar uma task completa para o Task Master.

---

## Sua Missão

Você receberá um **Plano de Implementação** em anexo. Sua tarefa é transformar esse plano em uma **Task completa e detalhada** para o Task Master, seguindo rigorosamente as instruções abaixo.

### Regra Fundamental: Captura Total

**VOCÊ DEVE ENGLOBAR 100% DO PLANEJAMENTO FORNECIDO.**

- ❌ NÃO omita dados
- ❌ NÃO resuma especificações técnicas
- ❌ NÃO ignore edge cases
- ❌ NÃO simplifique integrações
- ❌ NÃO deixe de fora regras de negócio
- ❌ NÃO reduza exemplos de código
- ✅ TRANSFIRA toda informação para os campos apropriados da task

Se uma informação existe no plano, ela DEVE existir na task gerada.

---

## Estrutura de uma Task

Cada task no Task Master segue esta estrutura JSON:

```json
{
  "id": <number>,
  "title": "<string - máx 80 chars>",
  "description": "<string - máx 250 chars>",
  "details": "<string - SEM LIMITE - campo principal>",
  "testStrategy": "<string>",
  "status": "pending",
  "dependencies": ["<task_id>", ...],
  "priority": "low | medium | high",
  "subtasks": [...]
}
```

### Estrutura de uma Subtask

```json
{
  "id": <number - sequencial: 1, 2, 3...>,
  "title": "<string>",
  "description": "<string>",
  "details": "<string - SEM LIMITE>",
  "status": "pending",
  "dependencies": [<subtask_ids>],
  "testStrategy": "<string>",
  "parentTaskId": <id_da_task_pai>
}
```

---

## Instruções de Preenchimento

### 1. Campo `title`

**Formato**: `[PREFIXO] Descrição Clara da Funcionalidade`

**Prefixos Padrão**:
| Prefixo | Uso |
|---------|-----|
| `[ATD]` | Atendimento |
| `[TRN]` | Treinamento/IA |
| `[OPS]` | Operacional/SLA |
| `[ADM]` | Administrativo |
| `[PERF]` | Performance |
| `[FIX]` | Correção de Bug |
| `[FEAT]` | Nova Feature |
| `[REFACTOR]` | Refatoração |
| `[INFRA]` | Infraestrutura |

**Limite**: 80 caracteres

---

### 2. Campo `description`

- Resumo executivo da funcionalidade (1-3 frases)
- Deve responder: O que será feito e por quê?
- **Limite**: 250 caracteres

---

### 3. Campo `details` ⚠️ CAMPO CRÍTICO

Este é o campo principal. **TODO o conteúdo técnico do plano deve estar aqui.**

**Estrutura obrigatória em Markdown**:

```markdown
## Contexto e Motivação
[Copiar/adaptar do plano: Por que essa funcionalidade é necessária?]

## Requisitos Funcionais
[Lista COMPLETA de requisitos do plano - não omitir nenhum]

## Arquitetura e Localização
[Onde o código será implementado? Estrutura de pastas/arquivos]

## Detalhes de Implementação

### [Nome do Componente 1]
- **Arquivo(s)**: `caminho/completo/arquivo.py`
- **Responsabilidade**: [Descrição detalhada]
- **Dependências**: [Módulos/serviços necessários]
- **Regras de Negócio**:
  - [Regra 1 - copiar do plano]
  - [Regra 2 - copiar do plano]
  - [... todas as regras]
- **Edge Cases**:
  - [Caso 1]
  - [Caso 2]
- **Código de Referência**:
```python
# Se houver snippets no plano, incluir aqui
```

### [Nome do Componente 2]
[Repetir estrutura para cada componente]

## Integrações
[Detalhar TODAS as integrações mencionadas no plano]

## Fluxo de Execução
[Descrever o fluxo passo a passo]

## Variáveis de Ambiente
[Listar variáveis necessárias, se houver]

## Observações e Decisões de Design
[Capturar notas, warnings, decisões do plano]

## Referências
[Códigos PRD, links, documentos relacionados]
```

---

### 4. Campo `testStrategy`

Transcrever do plano:
- Cenários de teste
- Validações manuais
- Critérios de aceitação
- Dados de teste necessários

Se o plano não tiver estratégia de teste explícita, derive dos requisitos funcionais.

---

### 5. Campo `dependencies`

- Array de IDs (strings) de tasks existentes que são pré-requisitos
- Analisar o plano para identificar dependências implícitas
- Formato: `["12", "15", "8"]`

---

### 6. Campo `priority`

Determinar baseado no plano:
- `high`: Crítico para o negócio, bloqueador de outras features
- `medium`: Importante, mas não urgente
- `low`: Nice to have, melhorias incrementais

---

## Criação de Subtasks

### Quando Criar Subtask?

Crie uma subtask para cada:
- Etapa lógica do plano que pode ser executada independentemente
- Componente/módulo distinto a ser implementado
- Fase do desenvolvimento (ex: model, service, integração)

### Preenchimento de Subtasks

Cada subtask deve ter `details` completo com:
- Arquivos específicos a modificar/criar
- Lógica detalhada a implementar
- Campos, métodos, classes a criar
- Regras de negócio específicas daquela etapa
- Código de referência se aplicável

### Dependências entre Subtasks

- Numerar IDs sequencialmente: 1, 2, 3...
- Subtask 2 depende de 1 se precisar do que 1 entrega
- Subtasks podem ser paralelas (sem dependência) se forem independentes

---

## Checklist de Validação

Antes de finalizar, verifique:

### Completude
- [ ] Todos os requisitos funcionais do plano estão na task?
- [ ] Todas as regras de negócio foram capturadas?
- [ ] Todos os edge cases foram documentados?
- [ ] Todas as integrações estão detalhadas?
- [ ] Todo código de referência foi incluído?
- [ ] Todas as variáveis de ambiente foram listadas?

### Estrutura
- [ ] O título segue o padrão de prefixo?
- [ ] O `details` usa a estrutura Markdown definida?
- [ ] Cada subtask tem detalhes suficientes para execução autônoma?
- [ ] As dependências estão corretas?
- [ ] O JSON é válido?

### Rastreabilidade
- [ ] Códigos PRD foram referenciados (se existirem)?
- [ ] Arquivos afetados estão listados?
- [ ] Decisões de design foram documentadas?

---

## Formato de Saída

Retorne o JSON completo da task, pronto para ser adicionado ao Task Master:

```json
{
  "id": <próximo_id>,
  "title": "...",
  "description": "...",
  "details": "...",
  "testStrategy": "...",
  "status": "pending",
  "dependencies": [...],
  "priority": "...",
  "subtasks": [
    {
      "id": 1,
      "title": "...",
      "description": "...",
      "details": "...",
      "status": "pending",
      "dependencies": [],
      "testStrategy": "...",
      "parentTaskId": <id_task>
    }
  ]
}
```

---

## Como Registrar a Task no Task Master

### ⭐ Método Preferencial: MCP (Model Context Protocol)

O Task Master está configurado como servidor MCP neste projeto. **Use preferencialmente as ferramentas MCP**, pois elas possuem instruções claras e integradas sobre como utilizar cada funcionalidade.

As ferramentas MCP disponíveis incluem:
- **Criar task**: Ferramenta para adicionar nova task com todos os campos
- **Atualizar task**: Ferramenta para modificar task existente
- **Listar tasks**: Ferramenta para visualizar tasks e seus status
- **Obter próxima task**: Ferramenta para identificar a próxima task a executar
- **Expandir task**: Ferramenta para gerar subtasks automaticamente
- **Atualizar status**: Ferramenta para marcar progresso

> 💡 **Dica**: Ao usar as ferramentas MCP, leia atentamente as instruções de cada ferramenta. Elas contêm orientações específicas sobre parâmetros obrigatórios, formatos aceitos e melhores práticas.

### Método Alternativo: CLI

Caso o MCP não esteja disponível, use os comandos CLI como fallback:

```bash
# Adicionar task
npx task-master-ai add-task --description "..."

# Atualizar task existente
npx task-master-ai update-task --id <ID> --description "..." --details "..."

# Listar todas as tasks
npx task-master-ai list

# Ver próxima task disponível
npx task-master-ai next

# Expandir task em subtasks
npx task-master-ai expand --id <ID>

# Marcar como concluída
npx task-master-ai set-status --id <ID> --status done
```

---

**Lembre-se**: O objetivo é que qualquer desenvolvedor consiga executar a task apenas lendo os campos `details` e `testStrategy`, sem precisar consultar o plano original. A task deve ser **autocontida e completa**.
