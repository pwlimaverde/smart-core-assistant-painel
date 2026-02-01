# /status - Ver Status do Workflow

Exibe o status atual do workflow PREVC e planos ativos.

## Instruções

1. **Leia o status do workflow**
   - `.context/workflow/status.yaml`

2. **Liste planos ativos**
   - `.context/plans/`

3. **Exiba resumo**
   - Fase atual
   - Planos em andamento
   - Próximas ações

## Parâmetros

Nenhum parâmetro necessário.

## Exemplo de Uso

```
/status
```

## Output Esperado

```
## Status do Workflow PREVC

**Projeto:** smart-core-assistant-painel
**Fase Atual:** E (Execution)

### Fases
- [x] P (Planning) - Completo
- [x] R (Review) - Completo
- [→] E (Execution) - Em andamento
- [ ] V (Validation) - Pendente
- [ ] C (Confirmation) - Pendente

### Planos Ativos
- feature-oauth-login.md (Fase E)
- refactor-ai-engine.md (Fase P)

### Próximas Ações
1. Concluir implementação do OAuth
2. Iniciar testes de validação
```
