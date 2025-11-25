# Padrão de Projeto - Apps Django

Este documento define o padrão de projeto a ser seguido na criação e refatoração de aplicações Django no projeto Smart Core Assistant Painel.

## 1. Estrutura de Diretórios

### 1.1. Organização Base de um App Django

```
meu_app/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── signals.py              # Apenas se necessário
├── services/
│   ├── __init__.py        # Facade do módulo
│   ├── service_name.py    # Lógica de negócio
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   └── ...
└── migrations/
```

### 1.2. Separação de Responsabilidades

**Models (`models.py`)**
- Define apenas a estrutura de dados e relacionamentos
- Métodos devem ser relacionados ao modelo em si (validações, propriedades calculadas)
- Evite lógica de negócio complexa nos models

**Services (`services/`)**
- Contém toda a lógica de negócio
- Orquestra operações entre diferentes models
- Interage com APIs externas
- Processa dados complexos

**Signals (`signals.py`)**
- Use apenas para efeitos colaterais que devem ocorrer automaticamente
- Mantenha a lógica simples; delegue para services se necessário
- Documente claramente quando e por que o signal é disparado

**Views e URLs**
- Apps de backend/processamento NÃO devem ter views ou URLs
- Views são apenas para apps que expõem APIs REST ou interfaces
- Se o app não tem interface, remova `views.py`, `urls.py` e `serializers.py`

## 2. Princípios de Clean Code

### 2.1. Nomenclatura

**Código (Variáveis, Funções, Classes)**
- **Idioma**: Inglês
- **Variáveis e Funções**: `snake_case`
  ```python
  user_count = 0
  def calculate_total_price():
      pass
  ```
- **Classes**: `PascalCase`
  ```python
  class UserService:
      pass
  ```
- **Constantes**: `UPPER_SNAKE_CASE`
  ```python
  MAX_RETRY_ATTEMPTS = 3
  ```

**Comentários e Docstrings**
- **Idioma**: Português
- Use docstrings para documentar módulos, classes e funções públicas
- Comentários inline devem explicar o "porquê", não o "o quê"

```python
def process_message(message: str) -> dict[str, Any]:
    """Processa uma mensagem recebida do WhatsApp.
    
    Args:
        message: Conteúdo da mensagem a ser processada.
        
    Returns:
        Dicionário com o resultado do processamento.
    """
    # Normaliza o texto antes de processar para garantir consistência
    normalized = message.strip().lower()
    # ...
```

### 2.2. Type Hints

**OBRIGATÓRIO**: Todas as funções e métodos devem ter anotações de tipo completas.

```python
from typing import Optional, Any

def get_user_by_id(user_id: int) -> Optional[User]:
    """Busca um usuário pelo ID."""
    return User.objects.filter(id=user_id).first()

def process_data(data: dict[str, Any]) -> None:
    """Processa dados do payload."""
    pass
```

### 2.3. Modularidade

**Tamanho de Arquivos**
- Arquivos com mais de 300 linhas devem ser divididos em módulos menores
- Cada módulo deve ter uma responsabilidade única e bem definida

**Tamanho de Funções**
- Funções devem ter no máximo 50 linhas
- Se uma função faz mais de uma coisa, divida-a em funções menores

### 2.4. Princípio DRY (Don't Repeat Yourself)

- Evite duplicação de código
- Extraia lógica repetida para funções reutilizáveis
- Use herança e composição quando apropriado

```python
# ❌ Evite
def send_email_to_admin():
    email = "admin@example.com"
    # lógica de envio

def send_email_to_user():
    email = "user@example.com"
    # mesma lógica de envio

# ✅ Prefira
def send_email(recipient: str, subject: str, body: str) -> None:
    """Envia um email para o destinatário especificado."""
    # lógica de envio
```

## 3. Padrão de Services

### 3.1. Estrutura de um Service

```python
from typing import Any, Optional
from django.db import transaction

class MyService:
    """Serviço responsável por [descrição da responsabilidade].
    
    Este serviço gerencia [explicar o domínio].
    """
    
    def __init__(self) -> None:
        """Inicializa o serviço."""
        pass
    
    @transaction.atomic
    def create_entity(self, data: dict[str, Any]) -> MyModel:
        """Cria uma nova entidade no sistema.
        
        Args:
            data: Dados para criação da entidade.
            
        Returns:
            A entidade criada.
            
        Raises:
            ValidationError: Se os dados forem inválidos.
        """
        # Implementação
        pass
    
    def _internal_helper(self, value: str) -> str:
        """Método auxiliar interno (use prefixo _)."""
        return value.strip()
```

### 3.2. Uso do `__init__.py` como Facade

O arquivo `__init__.py` deve expor a API pública do módulo:

```python
"""
Este módulo centraliza os serviços de processamento de mensagens.
"""
from .message_processor import MessageProcessor
from .message_buffer import (
    set_buffer_contact,
    clear_buffer_contact,
    sched_response_contact,
)

__all__ = [
    "MessageProcessor",
    "set_buffer_contact",
    "clear_buffer_contact",
    "sched_response_contact",
]
```

## 4. Segurança

### 4.1. Gerenciamento de Segredos

**NUNCA** faça commit de:
- Senhas
- Tokens de API
- Chaves de acesso
- Configurações sensíveis

**Use variáveis de ambiente**:
```python
from decouple import config

API_KEY = config("EVOLUTION_API_KEY")
BASE_URL = config("EVOLUTION_API_URL")
```

**Forneça arquivo de exemplo**:
```bash
# .env.example
EVOLUTION_API_KEY=sua_chave_aqui
EVOLUTION_API_URL=http://localhost:8080
```

### 4.2. Validação de Entrada

Sempre valide dados de entrada, especialmente de fontes externas:

```python
def process_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """Processa webhook recebido."""
    # Valida campos obrigatórios
    if not payload.get("event"):
        raise ValueError("Campo 'event' é obrigatório")
    
    # Valida tipos
    instance_id = payload.get("instance")
    if not isinstance(instance_id, str):
        raise TypeError("instance_id deve ser string")
    
    # Processa...
```

## 5. Testes

### 5.1. Estrutura de Testes

**Testes de Aplicação Django** (Models, Signals, etc.):
```
src/meu_app/tests/
├── __init__.py
├── test_models.py
└── test_signals.py
```

**Testes de Lógica de Negócio** (Services):
```
tests/modules/app/meu_app/
├── __init__.py
├── test_service.py
└── test_usecase.py
```

### 5.2. Cobertura e Qualidade

- **Cobertura mínima**: 80%
- Todas as funções de teste devem ter type hints
- Use nomes descritivos para testes:
  ```python
  def test_create_user_with_valid_data_should_succeed() -> None:
      """Testa criação de usuário com dados válidos."""
      pass
  ```

### 5.3. Comando de Execução

**SEMPRE** use o comando Docker para testes:
```bash
uv run task test-docker
```

## 6. Boas Práticas Específicas do Django

### 6.1. Signals

Use signals com moderação. Prefira chamadas explícitas quando possível.

**Quando usar signals**:
- Efeitos colaterais que devem sempre ocorrer (ex: limpar cache ao deletar)
- Desacoplamento de apps
- Auditoria automática

**Exemplo adequado**:
```python
@receiver(post_save, sender=Mensagem)
def _on_message_saved(
    sender: type[Mensagem], 
    instance: Mensagem, 
    created: bool, 
    **kwargs: Any
) -> None:
    """Dispara envio de mensagem via WhatsApp quando resposta do bot é salva.
    
    Args:
        sender: Classe que enviou o sinal.
        instance: Instância da mensagem salva.
        created: True se foi criada, False se atualizada.
        **kwargs: Argumentos adicionais.
    """
    if not instance.resposta_bot or not instance.respondida:
        return
    
    # Delega para service
    WhatsAppService().send_message(instance)
```

### 6.2. Migrations

- Sempre revise migrations antes de aplicar
- Use nomes descritivos para migrations manuais
- Nunca edite migrations já aplicadas em produção

### 6.3. QuerySets e Performance

**Use `select_related` e `prefetch_related`**:
```python
# ✅ Eficiente
contacts = EvolutionContact.objects.select_related(
    "instance", "contact"
).filter(active=True)

# ❌ Ineficiente (N+1 queries)
contacts = EvolutionContact.objects.filter(active=True)
for contact in contacts:
    print(contact.instance.name)  # Query adicional para cada iteração
```

## 7. Documentação

### 7.1. Docstrings

Use o estilo **Google** para docstrings:

```python
def calculate_discount(
    price: float, 
    discount_percent: int, 
    max_discount: float
) -> float:
    """Calcula o desconto aplicado sobre um preço.
    
    Esta função aplica um percentual de desconto sobre o preço,
    respeitando um limite máximo de desconto.
    
    Args:
        price: Preço original do produto.
        discount_percent: Percentual de desconto (0-100).
        max_discount: Valor máximo de desconto permitido.
        
    Returns:
        Valor final após aplicação do desconto.
        
    Raises:
        ValueError: Se discount_percent não estiver entre 0 e 100.
        
    Examples:
        >>> calculate_discount(100.0, 10, 20.0)
        90.0
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("discount_percent deve estar entre 0 e 100")
    
    discount = price * (discount_percent / 100)
    discount = min(discount, max_discount)
    return price - discount
```

### 7.2. README do App

Cada app complexo deve ter um README.md:

```markdown
# Nome do App

Breve descrição do propósito do app.

## Responsabilidades

- Responsabilidade 1
- Responsabilidade 2

## Estrutura

Explicação da estrutura de diretórios.

## Uso

Exemplos de uso dos principais services/funcionalidades.

## Testes

Instruções para executar os testes específicos do app.
```

## 8. Checklist de Refatoração

Ao refatorar um app existente, siga este checklist:

- [ ] Organizar arquivos seguindo a estrutura padrão
- [ ] Remover views/URLs se for app de backend puro
- [ ] Mover lógica de negócio dos models para services
- [ ] Adicionar type hints em todas as funções
- [ ] Renomear variáveis/funções para inglês
- [ ] Adicionar/corrigir docstrings em português
- [ ] Implementar facade no `__init__.py` dos services
- [ ] Remover código duplicado (DRY)
- [ ] Quebrar funções grandes (>50 linhas)
- [ ] Quebrar arquivos grandes (>300 linhas)
- [ ] Adicionar testes com cobertura mínima de 80%
- [ ] Remover hardcoded values para variáveis de ambiente
- [ ] Validar todas as entradas de dados externos
- [ ] Revisar uso de signals (justificar ou substituir)
- [ ] Executar `uv run task format` (formatação)
- [ ] Executar `uv run task lint` (linting)
- [ ] Executar `uv run task type-check` (verificação de tipos)
- [ ] Executar `uv run task test-docker` (testes)

## 9. Exemplo Prático: evolution_sync

O app `evolution_sync` foi refatorado seguindo este padrão:

### Antes
```
evolution_sync/
├── utils.py  # Funções misturadas de diferentes responsabilidades
├── services/
│   └── webhook.py  # Importava de utils.py
```

### Depois
```
evolution_sync/
├── services/
│   ├── __init__.py  # Facade exportando API pública
│   ├── message_buffer.py  # Lógica de buffer isolada
│   └── webhook.py  # Importa do próprio módulo services
```

### Benefícios
- ✅ Responsabilidades claramente separadas
- ✅ API pública bem definida via `__init__.py`
- ✅ Facilita testes e manutenção
- ✅ Reduz acoplamento entre módulos

## 10. Referências

- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)
- [Clean Code: A Handbook of Agile Software Craftsmanship](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Regras específicas do projeto](.agent/rules/rules-smart-assistant.md)

---

**Última atualização**: 2025-11-19  
**Versão**: 1.0
