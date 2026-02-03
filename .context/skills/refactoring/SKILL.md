---
name: refactoring
description: Refatoração segura de código
phases: [E, V]
---

# Refactoring Skill

## Quando Usar

Use este skill quando:
- Melhorando estrutura de código existente
- Removendo duplicação
- Simplificando lógica complexa
- Extraindo métodos/classes

## Instruções

### 1. Pré-requisitos

Antes de refatorar:
- [ ] Testes existentes passam
- [ ] Entendo o comportamento atual
- [ ] Escopo definido e limitado

### 2. Técnicas de Refatoração

#### Extract Method
```python
# Antes
def process(data):
    # validação
    if not data.get("field1"):
        raise ValueError("field1 required")
    if not data.get("field2"):
        raise ValueError("field2 required")
    # processamento
    result = transform(data)
    return result

# Depois
def process(data):
    self._validate(data)
    return transform(data)

def _validate(self, data):
    required = ["field1", "field2"]
    for field in required:
        if not data.get(field):
            raise ValueError(f"{field} required")
```

#### Extract Class
```python
# Antes: classe com múltiplas responsabilidades
class UserService:
    def create_user(self, data): ...
    def send_email(self, user, template): ...
    def generate_report(self, users): ...

# Depois: responsabilidades separadas
class UserService:
    def create_user(self, data): ...

class EmailService:
    def send_email(self, user, template): ...

class ReportService:
    def generate_report(self, users): ...
```

#### Replace Conditional with Polymorphism
```python
# Antes
def calculate(type, value):
    if type == "A":
        return value * 1.0
    elif type == "B":
        return value * 1.5
    elif type == "C":
        return value * 2.0

# Depois
class Calculator(Protocol):
    def calculate(self, value: float) -> float: ...

class CalculatorA:
    def calculate(self, value: float) -> float:
        return value * 1.0

CALCULATORS = {"A": CalculatorA(), "B": CalculatorB(), "C": CalculatorC()}

def calculate(type: str, value: float) -> float:
    return CALCULATORS[type].calculate(value)
```

#### Simplify Conditionals
```python
# Antes
def can_access(user, resource):
    if user.is_admin:
        return True
    else:
        if user.is_active:
            if resource.is_public:
                return True
            else:
                if user.has_permission(resource):
                    return True
    return False

# Depois
def can_access(user, resource):
    if user.is_admin:
        return True
    if not user.is_active:
        return False
    if resource.is_public:
        return True
    return user.has_permission(resource)
```

### 3. Code Smells a Resolver

| Smell | Solução |
|-------|---------|
| Long Method (>30 linhas) | Extract Method |
| Large Class | Extract Class |
| Duplicated Code | Extract Method/Class |
| Feature Envy | Move Method |
| Data Clumps | Create Value Object |
| Primitive Obsession | Create Data Class |
| Switch Statements | Polymorphism |

### 4. Processo Seguro

1. **Garanta testes**
   ```bash
   uv run task test-docker
   ```

2. **Faça mudanças incrementais**
   - Uma refatoração por commit
   - Teste após cada mudança

3. **Verifique comportamento**
   ```bash
   # Testes passam
   uv run task test-docker

   # Tipos corretos
   uv run task type-check

   # Estilo ok
   uv run task lint
   ```

4. **Commit atômico**
   ```bash
   git commit -m "refactor(module): extract validation to separate method"
   ```

## Checklist

- [ ] Testes passam antes
- [ ] Mudança incremental
- [ ] Testes passam depois
- [ ] Comportamento inalterado
- [ ] Código mais legível
- [ ] Commit atômico
