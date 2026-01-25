# Agentes Especializados

Este diretório contém playbooks para agentes especializados que auxiliam em diferentes aspectos do desenvolvimento do Smart Core Assistant Painel.

---

## Índice de Agentes

### Desenvolvimento de Código

| Agente | Arquivo | Descrição |
|--------|---------|-----------|
| Feature Developer | [feature-developer.md](feature-developer.md) | Desenvolve novas funcionalidades |
| Bug Fixer | [bug-fixer.md](bug-fixer.md) | Investiga e corrige bugs |
| Refactoring Specialist | [refactoring-specialist.md](refactoring-specialist.md) | Refatora código existente |
| Code Reviewer | [code-reviewer.md](code-reviewer.md) | Revisa código e sugere melhorias |

### Especialistas de Domínio

| Agente | Arquivo | Descrição |
|--------|---------|-----------|
| Backend Specialist | [backend-specialist.md](backend-specialist.md) | Django, APIs, integrações |
| Frontend Specialist | [frontend-specialist.md](frontend-specialist.md) | Templates, CSS, JavaScript |
| Database Specialist | [database-specialist.md](database-specialist.md) | PostgreSQL, migrações, queries |
| AI/ML Specialist | [ai-specialist.md](ai-specialist.md) | LangChain, embeddings, prompts |

### Qualidade e Operações

| Agente | Arquivo | Descrição |
|--------|---------|-----------|
| Test Writer | [test-writer.md](test-writer.md) | Cria testes automatizados |
| Documentation Writer | [documentation-writer.md](documentation-writer.md) | Documenta código e APIs |
| Performance Optimizer | [performance-optimizer.md](performance-optimizer.md) | Otimiza performance |
| Security Auditor | [security-auditor.md](security-auditor.md) | Audita segurança |

### Arquitetura e DevOps

| Agente | Arquivo | Descrição |
|--------|---------|-----------|
| Architect Specialist | [architect-specialist.md](architect-specialist.md) | Decisões arquiteturais |
| DevOps Specialist | [devops-specialist.md](devops-specialist.md) | CI/CD, Docker, infraestrutura |

---

## Como Usar os Agentes

### 1. Selecione o Agente Apropriado

Escolha o agente que melhor se alinha com a tarefa:

- **Nova feature?** → Feature Developer
- **Bug para corrigir?** → Bug Fixer
- **Código legado para limpar?** → Refactoring Specialist
- **Otimização de performance?** → Performance Optimizer

### 2. Consulte o Playbook

Cada playbook contém:

- **Contexto**: Área de atuação do agente
- **Habilidades**: O que o agente sabe fazer
- **Workflow**: Passos recomendados
- **Ferramentas**: Tools e comandos utilizados
- **Exemplos**: Casos de uso típicos

### 3. Forneça Contexto Adequado

Ao invocar um agente, forneça:

- Descrição clara da tarefa
- Arquivos relevantes (se conhecidos)
- Requisitos e restrições
- Resultado esperado

---

## Estrutura de um Playbook

```markdown
# Nome do Agente

## Contexto
Breve descrição do papel e área de atuação.

## Habilidades
- Habilidade 1
- Habilidade 2

## Workflow
1. Passo 1
2. Passo 2

## Ferramentas
- Ferramenta 1
- Ferramenta 2

## Exemplos
### Exemplo 1: Título
Descrição do caso de uso.

## Restrições
- O que o agente NÃO deve fazer
```

---

## Combinação de Agentes

Algumas tarefas requerem múltiplos agentes trabalhando em sequência:

### Nova Feature Complexa

1. **Architect Specialist**: Define design
2. **Feature Developer**: Implementa código
3. **Test Writer**: Cria testes
4. **Code Reviewer**: Revisa resultado

### Correção de Bug em Produção

1. **Bug Fixer**: Investiga e corrige
2. **Security Auditor**: Verifica vulnerabilidades
3. **Test Writer**: Adiciona teste de regressão

### Refatoração de Módulo

1. **Refactoring Specialist**: Planeja e executa
2. **Performance Optimizer**: Verifica performance
3. **Documentation Writer**: Atualiza docs

---

## Criando Novos Agentes

Para criar um novo agente:

1. Crie arquivo `nome-do-agente.md` neste diretório
2. Siga a estrutura de playbook acima
3. Adicione à tabela no README.md
4. Teste com tarefas reais

---

## Notas Importantes

- Agentes devem seguir os padrões do projeto definidos em `CLAUDE.md`
- Comunicação sempre em Português
- Código em Inglês (variáveis, funções, classes)
- Type hints obrigatórios
- Conventional Commits para git
