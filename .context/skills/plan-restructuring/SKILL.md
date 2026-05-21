---
name: plan-restructuring
description: Etapa final de qualquer planejamento. Levanta as libs do plano, carrega a documentação atual via MCP context7 (subagente barato) e reestrutura o plano corrigindo APIs/sintaxe/padrões desatualizados (subagente caro).
phases: [P]
skills: [feature-breakdown]
---

# Plan Restructuring Skill

## Quando Usar

Use **sempre como etapa FINAL** de qualquer planejamento, depois que o plano
inicial já existe (ex.: gerado pelo `/plan` em `.context/plans/`). O objetivo é
validar e corrigir o plano contra a documentação **atual** das bibliotecas,
evitando que a implementação seja baseada em APIs, sintaxe ou padrões
desatualizados que estejam no conhecimento de treino do modelo.

NÃO é para criar o plano do zero — para isso use `/plan` / `feature-breakdown`.

## Pré-requisitos

- [ ] Existe um plano inicial (arquivo em `.context/plans/{feature}.md` ou plano
      acabado de elaborar na conversa).
- [ ] O MCP context7 está disponível (ferramentas `resolve-library-id` e
      `query-docs`).

## Estratégia de Modelos (automática via subagentes)

A skill **não** troca o modelo da sua sessão. Em vez disso, delega cada etapa a
um subagente com modelo fixo, via ferramenta `Agent` (parâmetro `model`):

| Etapa | Trabalho | Executor | Modelo |
|-------|----------|----------|--------|
| 1. Levantamento de libs | Leitura leve do plano | Sessão principal | (atual) |
| 2. Coleta de documentação | Coleta/sumarização (barato) | Subagente | `haiku` |
| 3. Reestruturação do plano | Raciocínio (caro) | Subagente | `opus` |

Assim a coleta context7 economiza token (modelo barato + contexto isolado) e a
reestruturação usa o modelo mais capaz, independentemente do modelo da sessão.

## Etapas

### 1. Levantamento de Libs (sessão principal)

A partir do plano, liste **todas** as bibliotecas/frameworks/SDKs que a
implementação vai tocar. Para cada uma, capture a **versão** quando disponível,
cruzando com os manifests do projeto:

```bash
# Versões fixadas do projeto
cat pyproject.toml
cat uv.lock 2>/dev/null | grep -A2 'name = '
```

Produza uma lista objetiva, ex.:

```
- django (5.x)        -> ORM, signals, async views
- langchain (0.3.x)   -> chains, runnables
- pydantic (2.x)      -> validators, model_config
```

Para cada lib, anote **quais recursos/APIs específicos** o plano usa — isso foca
a consulta ao context7 e evita puxar documentação irrelevante.

### 2. Coleta de Documentação Atual (subagente `haiku`)

Para cada lib (ou grupo de libs independentes, **em paralelo**), dispare um
subagente barato. Faça as chamadas paralelas em uma única mensagem com vários
blocos `Agent`.

```
Agent({
  description: "Docs atuais de <lib>",
  subagent_type: "general-purpose",
  model: "haiku",
  prompt: `
    Use o MCP context7 para coletar a documentação ATUAL da biblioteca <lib>
    (versão <versão>), focando APENAS nestes recursos: <lista de APIs/recursos>.

    Passos:
    1. Chame resolve-library-id com o nome oficial da lib para obter o library ID
       (formato /org/project). Se a versão for conhecida, prefira /org/project/versão.
    2. Chame query-docs com esse library ID e uma query específica por recurso.
    3. NÃO despeje a documentação inteira. Retorne um resumo objetivo contendo:
       - Assinaturas/sintaxe ATUAIS dos recursos pedidos (com mini-exemplo).
       - APIs depreciadas ou removidas relevantes ao plano.
       - Mudanças de padrão/breaking changes que afetem a implementação.
       - O library ID usado (para rastreabilidade).
    Seja conciso. Relatório em Português.
  `
})
```

Colete os relatórios de todos os subagentes antes de seguir.

### 3. Reestruturação do Plano (subagente `opus`)

Dispare **um** subagente caro, passando o plano original + os relatórios de
documentação coletados. Ele cruza os dois e devolve o plano reestruturado.

```
Agent({
  description: "Reestruturar plano com docs atuais",
  subagent_type: "general-purpose",
  model: "opus",
  prompt: `
    Você vai REESTRUTURAR um plano de implementação usando a documentação ATUAL
    das libs envolvidas. Comunique-se em Português.

    Plano original:
    <conteúdo do plano OU caminho .context/plans/{feature}.md>

    Documentação atual coletada (context7):
    <relatórios da etapa 2>

    Tarefas:
    1. Compare cada passo do plano com a documentação atual.
    2. Corrija erros: APIs depreciadas/removidas, assinaturas erradas, imports
       obsoletos, padrões que mudaram de versão.
    3. Detalhe as implementações já com a sintaxe/padrões atuais.
    4. Respeite a arquitetura do projeto (Multi-Tenant + Result Pattern — ver
       .context/docs/architecture.md). Não invente libs novas sem necessidade.
    5. Adicione uma seção "Correções aplicadas" listando o que mudou e por quê
       (citando a lib/versão e o recurso).

    Devolva o PLANO REESTRUTURADO COMPLETO em markdown, pronto para salvar.
  `
})
```

### 4. Salvar e Registrar (sessão principal)

1. Salve o plano reestruturado retornado pelo subagente, **sobrescrevendo** o
   plano original em `.context/plans/{feature}.md` (ou criando-o se o plano só
   existia na conversa).
2. Mostre ao usuário um resumo das **correções aplicadas** (da seção gerada).
3. Atualize o status do workflow, se aplicável:

```yaml
# .context/workflow/status.yaml
phases:
  P:
    status: completed
    outputs:
      - path: ".context/plans/{feature}.md"
```

## Checklist

- [ ] Todas as libs do plano foram levantadas (com versão quando disponível).
- [ ] Cada lib teve documentação atual coletada por subagente `haiku`.
- [ ] A reestruturação foi feita por subagente `opus`.
- [ ] APIs depreciadas/sintaxe obsoleta foram corrigidas no plano.
- [ ] Seção "Correções aplicadas" presente no plano final.
- [ ] Plano reestruturado salvo em `.context/plans/`.
- [ ] Status do workflow atualizado.
