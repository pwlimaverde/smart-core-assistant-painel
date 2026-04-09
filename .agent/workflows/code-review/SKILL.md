---
name: code-review
description: Verifica qualidade de código contra padrões
phases: [R, V]
---

# Code Review Skill

## Quando Usar

Use este skill quando:
- Verificando qualidade de código implementado
- Validando aderência aos padrões do projeto
- Fazendo review de arquivos específicos

## Instruções

### 1. Verificações Automatizadas

```bash
# Linting
uv run task lint

# Type checking
uv run task type-check

# Testes
uv run task test-docker
```

### 2. Checklist de Qualidade

#### Estilo e Formatação
- [ ] Código formatado (ruff format)
- [ ] Linhas com máximo 79 caracteres
- [ ] Imports organizados (stdlib, third-party, local)
- [ ] Naming conventions: `snake_case` funções, `PascalCase` classes

#### Type Hints
- [ ] Todas as funções têm type hints
- [ ] Tipos Union tratados com isinstance
- [ ] Pyright passa sem erros

#### Documentação
- [ ] Docstrings em funções públicas (Google style)
- [ ] Comentários onde lógica não é óbvia
- [ ] Sem TODOs esquecidos

#### Estrutura
- [ ] Funções com responsabilidade única
- [ ] Classes coesas
- [ ] Sem duplicação de código
- [ ] Sem código morto

#### Segurança
- [ ] Sem hardcode de secrets
- [ ] Inputs validados
- [ ] Queries parametrizadas
- [ ] Multi-tenancy respeitado

#### Performance
- [ ] Sem N+1 queries
- [ ] select_related/prefetch_related usado
- [ ] Sem loops desnecessários

### 3. Padrões do Projeto

#### Models Django
```python
# ✅ Correto
class Atendimento(TenantAwareModel):
    """Model de atendimento."""

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="atendimentos",
    )
    status = models.CharField(max_length=20, choices=Status.choices)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"Atendimento #{self.pk}"
```

#### Usecases
```python
# ✅ Correto
class AnaliseMensageUsecase:
    """Analisa mensagem usando LLM."""

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    def execute(self, message: str) -> Result[AnaliseResult, Exception]:
        """Executa análise da mensagem."""
        if not message.strip():
            return Failure(ValueError("Mensagem vazia"))
        # ...
```

#### Views
```python
# ✅ Correto
def atendimento_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Exibe detalhes do atendimento."""
    atendimento = get_object_or_404(
        Atendimento,
        pk=pk,
        tenant=request.user.tenant,
    )
    return render(request, "detail.html", {"atendimento": atendimento})
```

### 4. Code Smells a Detectar

| Smell | Exemplo | Ação |
|-------|---------|------|
| Long Method | Função > 30 linhas | Extract Method |
| Large Class | Classe > 200 linhas | Extract Class |
| Feature Envy | Usa muito dados de outra classe | Move Method |
| Data Clumps | Dados sempre juntos | Create Value Object |
| Primitive Obsession | Dict em vez de classe | Create Data Class |

### 5. Feedback Estruturado

```markdown
## Code Review: [arquivo/módulo]

### Qualidade Geral: [A/B/C/D]

### ✅ Pontos Positivos
- Type hints completos
- Boa separação de responsabilidades

### ⚠️ Problemas Encontrados

#### 1. [Categoria]: [Descrição]
**Arquivo:** `path/to/file.py:42`
**Severidade:** Alta/Média/Baixa

```python
# Problema
código problemático

# Solução
código corrigido
```

### 📊 Métricas
- Linhas de código: X
- Complexidade ciclomática: Y
- Cobertura de testes: Z%
```