---
name: prevc-execution
trigger: auto
description: Fase E (Execution) do workflow PREVC - Construir o que foi planejado
phases: [E]
skills: [commit-message, refactoring, documentation]
---

# PREVC - Execution (Fase E)

Workflow para a fase de execução do sistema PREVC.

## Objetivo

Implementar o código seguindo as especificações aprovadas.

## Quando Ativar

- Após conclusão da fase R (Review)
- Design e arquitetura aprovados
- Pronto para implementar

## Skills Associados

- [commit-message](../../.context/skills/commit-message/SKILL.md) - Mensagens de commit
- [refactoring](../../.context/skills/refactoring/SKILL.md) - Refatoração segura
- [documentation](../../.context/skills/documentation/SKILL.md) - Documentação

## Etapas

### 1. Preparar Ambiente

```bash
# Verificar branch
git checkout -b feature/[nome-da-feature]

# Atualizar dependências
uv sync --dev
```

### 2. Implementar Tarefa

Para cada tarefa em `tasks.md`:

```
1. Leia a spec da tarefa
2. Implemente seguindo padrões:
   - PEP8 (79 caracteres)
   - Type hints (pyright strict)
   - Docstrings Google style
3. Mantenha código em Inglês
4. Comentários em Português
```

### 3. Verificar Qualidade

```bash
# Formatar
uv run task format

# Lint
uv run task lint

# Type check
uv run task type-check
```

### 4. Commit

Use o skill `commit-message`:

```bash
git add [arquivos]
git commit -m "feat(modulo): descrição

Detalhes da implementação.

Refs: #issue"
```

### 5. Atualizar Progresso

Marque tarefas concluídas em `tasks.md`:

```markdown
- [x] Tarefa 1 - Concluída
- [ ] Tarefa 2 - Em progresso
- [ ] Tarefa 3 - Pendente
```

## Padrões de Código

### Estrutura de Arquivos

```python
"""
Docstring do módulo em Português.
"""
from typing import Any

from django.db import models

# Constantes
MAX_LENGTH = 100

# Classes e funções
class MinhaClasse:
    """Docstring da classe."""

    def meu_metodo(self, param: str) -> None:
        """Docstring do método."""
        pass
```

### Imports em `__init__.py`

```python
"""Descrição do módulo."""
from .feature import FeatureClass

__all__ = ["FeatureClass"]
```

## Outputs

- Código implementado
- Commits seguindo Conventional Commits
- `tasks.md` atualizado

## Gate para Próxima Fase

Antes de ir para Validation (V):

- [ ] Todas as tarefas implementadas
- [ ] Código formatado e linted
- [ ] Type check passando
- [ ] Commits organizados

## Atualizar Status

```yaml
# .context/workflow/status.yaml
phases:
  E:
    status: completed
```

## Próxima Fase

→ [prevc-validation](prevc-validation.md)
