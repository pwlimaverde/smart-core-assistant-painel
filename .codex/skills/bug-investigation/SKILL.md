---
name: bug-investigation
description: Fluxo estruturado de debugging
phases: [P, E]
---

# Bug Investigation Skill

## Quando Usar

Use este skill quando:
- Investigando bugs reportados
- Diagnosticando comportamento inesperado
- Analisando erros em produção

## Instruções

### 1. Coleta de Informações

**Perguntas a responder:**
- O que deveria acontecer?
- O que está acontecendo?
- Como reproduzir?
- Quando começou?
- Quem/o que é afetado?

**Dados a coletar:**
```bash
# Stack trace completo
# Logs relevantes
tail -f logs/django.log

# Ambiente
python --version
uv run pip list

# Estado do banco
uv run python manage.py shell
```

### 2. Reprodução

Crie script em `teste_debug/`:

```python
# teste_debug/reproduce_bug_xxx.py
"""Script para reproduzir bug #XXX."""

import django
django.setup()

from app.ui.atendimentos.models import Atendimento

def reproduce():
    """Reproduz o bug."""
    # Setup
    atendimento = Atendimento.objects.first()

    # Ação que causa o bug
    result = atendimento.process()

    # Verificação
    print(f"Result: {result}")
    print(f"Status: {atendimento.status}")

if __name__ == "__main__":
    reproduce()
```

### 3. Investigação

**Técnicas de debug:**

```python
# 1. Logging estratégico
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Estado: {variable=}")

# 2. Breakpoint
breakpoint()  # Para no debugger

# 3. Print temporário (remover depois!)
print(f"DEBUG: {variable}")

# 4. Assertions
assert condition, f"Esperado X, obteve {variable}"
```

**Ferramentas:**
```bash
# Django shell para investigar
uv run python manage.py shell

# Ver queries SQL
uv run python manage.py shell_plus --print-sql

# Logs do Celery
celery -A app.ui.core inspect active
```

### 4. Diagnóstico

**Categorizar o bug:**

| Categoria | Exemplo |
|-----------|---------|
| Lógica | Condição errada, off-by-one |
| Dados | Dados inválidos, null inesperado |
| Race Condition | Ordem de execução |
| Integração | API externa falha |
| Configuração | Env var errada |
| Performance | Timeout, memory |

**Template de diagnóstico:**
```markdown
## Bug #XXX - [Título]

### Descrição
[O que está acontecendo]

### Reprodução
1. Passo 1
2. Passo 2
3. Erro ocorre

### Causa Raiz
[Explicação técnica do problema]

### Impacto
- Afeta: [usuários/features]
- Severidade: [Alta/Média/Baixa]

### Solução Proposta
[Como corrigir]
```

### 5. Correção

```python
# Antes (bug)
def get_atendimento(pk):
    return Atendimento.objects.get(pk=pk)  # Pode lançar DoesNotExist

# Depois (corrigido)
def get_atendimento(pk):
    try:
        return Atendimento.objects.get(pk=pk)
    except Atendimento.DoesNotExist:
        logger.warning(f"Atendimento {pk} não encontrado")
        return None
```

### 6. Validação

```bash
# Bug não reproduz mais
python teste_debug/reproduce_bug_xxx.py

# Testes passam
uv run task test-docker

# Sem regressões
uv run task test-docker -- -k "atendimento"
```

### 7. Prevenção

Após corrigir:
- [ ] Adicionar teste de regressão
- [ ] Atualizar documentação
- [ ] Considerar logging adicional

## Checklist

- [ ] Bug reproduzido localmente
- [ ] Causa raiz identificada
- [ ] Correção implementada
- [ ] Código de debug removido
- [ ] Testes passam
- [ ] Teste de regressão adicionado
- [ ] Commit: `fix(module): descrição`