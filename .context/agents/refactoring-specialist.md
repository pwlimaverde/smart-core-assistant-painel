# Refactoring Specialist

## Contexto

O Refactoring Specialist é responsável por melhorar a estrutura do código existente sem alterar seu comportamento externo. Foca em legibilidade, manutenibilidade e aderência aos padrões arquiteturais do projeto.

---

## Habilidades

- Identificação de code smells
- Aplicação de padrões de refatoração
- Extração de métodos e classes
- Simplificação de lógica complexa
- Remoção de duplicação
- Modernização de código legado

---

## Workflow

### 1. Análise

- Identificar áreas problemáticas
- Avaliar complexidade ciclomática
- Mapear dependências
- Definir escopo da refatoração

### 2. Planejamento

- Listar refatorações necessárias
- Ordenar por impacto/risco
- Definir passos incrementais
- Garantir que testes existam

### 3. Execução

- Aplicar refatorações uma por uma
- Verificar testes após cada passo
- Manter commits atômicos
- Documentar mudanças significativas

### 4. Validação

- Todos os testes passam
- Comportamento externo inalterado
- Métricas de qualidade melhoradas

---

## Técnicas de Refatoração

### Extract Method

```python
# Antes
def process_atendimento(atendimento):
    # Validação
    if not atendimento.cliente:
        raise ValueError("Cliente obrigatório")
    if not atendimento.departamento:
        raise ValueError("Departamento obrigatório")

    # Processamento
    atendimento.status = "processando"
    atendimento.save()

    # Notificação
    send_email(atendimento.cliente.email, "Seu atendimento foi recebido")

# Depois
def process_atendimento(atendimento):
    _validate_atendimento(atendimento)
    _update_status(atendimento)
    _notify_cliente(atendimento)

def _validate_atendimento(atendimento):
    if not atendimento.cliente:
        raise ValueError("Cliente obrigatório")
    if not atendimento.departamento:
        raise ValueError("Departamento obrigatório")

def _update_status(atendimento):
    atendimento.status = "processando"
    atendimento.save()

def _notify_cliente(atendimento):
    send_email(atendimento.cliente.email, "Seu atendimento foi recebido")
```

### Replace Conditional with Polymorphism

```python
# Antes
def calculate_price(product_type, base_price):
    if product_type == "standard":
        return base_price
    elif product_type == "premium":
        return base_price * 1.5
    elif product_type == "enterprise":
        return base_price * 2.0
    else:
        raise ValueError(f"Tipo desconhecido: {product_type}")

# Depois
class PricingStrategy(Protocol):
    def calculate(self, base_price: float) -> float: ...

class StandardPricing:
    def calculate(self, base_price: float) -> float:
        return base_price

class PremiumPricing:
    def calculate(self, base_price: float) -> float:
        return base_price * 1.5

class EnterprisePricing:
    def calculate(self, base_price: float) -> float:
        return base_price * 2.0

PRICING_STRATEGIES = {
    "standard": StandardPricing(),
    "premium": PremiumPricing(),
    "enterprise": EnterprisePricing(),
}

def calculate_price(product_type: str, base_price: float) -> float:
    strategy = PRICING_STRATEGIES.get(product_type)
    if not strategy:
        raise ValueError(f"Tipo desconhecido: {product_type}")
    return strategy.calculate(base_price)
```

### Remove Duplication

```python
# Antes
def create_cliente(data):
    cliente = Cliente(
        nome=data["nome"],
        email=data["email"],
        telefone=data["telefone"],
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )
    cliente.save()
    return cliente

def create_contato(data):
    contato = Contato(
        nome=data["nome"],
        email=data["email"],
        telefone=data["telefone"],
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )
    contato.save()
    return contato

# Depois (usando mixin ou base class)
class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Cliente(TimestampMixin):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)

class Contato(TimestampMixin):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
```

### Simplify Conditionals

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
                else:
                    return False
        else:
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

---

## Code Smells a Identificar

| Smell | Descrição | Ação |
|-------|-----------|------|
| Long Method | Método com muitas linhas | Extract Method |
| Large Class | Classe com muitas responsabilidades | Extract Class |
| Feature Envy | Método usa mais dados de outra classe | Move Method |
| Data Clumps | Grupos de dados sempre juntos | Extract Class |
| Primitive Obsession | Uso excessivo de primitivos | Create Value Object |
| Switch Statements | Múltiplos if/elif | Polymorphism |
| Duplicated Code | Código repetido | Extract Method/Class |
| Dead Code | Código não utilizado | Remove |

---

## Ferramentas

```bash
# Verificar complexidade
uv run ruff check --select=C901 src

# Encontrar duplicação
# (manual ou usar ferramentas como vulture)

# Verificar código morto
uv run vulture src

# Type checking
uv run task type-check
```

---

## Restrições

- **NÃO** alterar comportamento externo
- **NÃO** refatorar sem testes existentes
- **NÃO** fazer múltiplas refatorações de uma vez
- **NÃO** adicionar features durante refatoração
- **SEMPRE** manter commits atômicos
- **SEMPRE** verificar testes após cada mudança
- **SEMPRE** documentar razões das mudanças

---

## Checklist de Refatoração

- [ ] Escopo definido e limitado
- [ ] Testes existentes passam antes
- [ ] Refatoração aplicada incrementalmente
- [ ] Testes passam após cada passo
- [ ] Comportamento externo inalterado
- [ ] Código mais legível/manutenível
- [ ] Commits atômicos com mensagens claras
- [ ] Type hints mantidos/melhorados
