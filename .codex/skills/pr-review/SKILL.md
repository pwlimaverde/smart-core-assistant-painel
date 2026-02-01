---
name: pr-review
description: Revisa Pull Requests de forma estruturada
phases: [R, V]
---

# PR Review Skill

## Quando Usar

Use este skill quando:
- Revisando Pull Requests de outros desenvolvedores
- Fazendo auto-review antes de submeter PR
- Avaliando PRs para merge

## Instruções

### 1. Análise Inicial

```bash
# Ver mudanças do PR
gh pr diff <pr-number>

# Ver arquivos modificados
gh pr view <pr-number> --json files

# Ver commits do PR
gh pr view <pr-number> --json commits
```

### 2. Checklist de Revisão

#### Funcionalidade
- [ ] O código faz o que a descrição do PR diz?
- [ ] Casos de borda são tratados?
- [ ] Erros são tratados adequadamente?

#### Qualidade de Código
- [ ] Código é legível e bem organizado?
- [ ] Não há duplicação desnecessária?
- [ ] Funções têm responsabilidade única?
- [ ] Nomes de variáveis são descritivos?

#### Padrões do Projeto
- [ ] Type hints em todas as funções?
- [ ] Docstrings em funções públicas (Google style)?
- [ ] Segue PEP8 (79 chars por linha)?
- [ ] Conventional Commits nas mensagens?

#### Segurança
- [ ] Sem hardcode de secrets?
- [ ] Inputs são validados?
- [ ] Sem vulnerabilidades óbvias (SQL injection, XSS)?
- [ ] Multi-tenancy respeitado?

#### Testes
- [ ] Testes existentes passam?
- [ ] Novos testes adicionados (se aplicável)?
- [ ] Cobertura adequada?

#### Performance
- [ ] Sem N+1 queries?
- [ ] Queries otimizadas?
- [ ] Sem loops desnecessários?

### 3. Tipos de Feedback

#### Aprovação
```markdown
✅ LGTM! Código bem estruturado e seguindo os padrões do projeto.

**Pontos positivos:**
- Boa separação de responsabilidades
- Type hints completos
- Tratamento de erros adequado
```

#### Sugestão (não-bloqueante)
```markdown
💡 **Sugestão:** Considere extrair esta lógica para um método separado para melhorar testabilidade.

```python
# Atual
def process(data):
    # 50 linhas de código

# Sugerido
def process(data):
    validated = self._validate(data)
    return self._transform(validated)
```
```

#### Mudança Necessária (bloqueante)
```markdown
⚠️ **Mudança necessária:** Falta validação de tenant, pode causar vazamento de dados.

```python
# Problema
clientes = Cliente.objects.all()

# Correção
clientes = Cliente.objects.filter(tenant=request.user.tenant)
```
```

#### Pergunta
```markdown
❓ **Pergunta:** Qual é o comportamento esperado quando `cliente` é None? Deveria lançar exceção ou retornar valor default?
```

## Template de Review

```markdown
## Revisão do PR #XXX

### Resumo
[Breve descrição do que foi revisado]

### Aprovação
- [ ] Funcionalidade
- [ ] Qualidade de código
- [ ] Segurança
- [ ] Testes
- [ ] Performance

### Comentários

#### ✅ Pontos Positivos
- ...

#### 💡 Sugestões
- ...

#### ⚠️ Mudanças Necessárias
- ...

### Veredicto
[Aprovado / Mudanças Solicitadas / Precisa Discussão]
```

## Comandos Úteis

```bash
# Aprovar PR
gh pr review <pr-number> --approve

# Solicitar mudanças
gh pr review <pr-number> --request-changes

# Comentar sem aprovar
gh pr review <pr-number> --comment
```