# /test - Executar e Criar Testes

Executa testes ou gera novos testes para código existente.

## Instruções

1. **Use o skill de test-generation**
   - `.context/skills/test-generation/SKILL.md`

2. **Consulte o agente de testes**
   - `.context/agents/test-writer.md`

3. **Comandos de Teste**
   ```bash
   # Todos os testes
   uv run task test-docker

   # Teste específico
   uv run task test-docker -- -k "nome_do_teste"

   # Com cobertura
   uv run task test-docker -- --cov=src
   ```

4. **Estrutura de Testes**
   - `tests/app/` - Testes de apps Django
   - `tests/modules/` - Testes de módulos

## Parâmetros

- `$ARGUMENTS`: Nome do teste ou módulo a testar

## Exemplo de Uso

```
/test                                    # Executa todos
/test atendimentos                       # Testes de atendimentos
/test generate app/clientes/views.py  # Gera testes para arquivo
```

## Tipos de Teste

- **Model**: Validações, métodos custom
- **View**: Endpoints, permissões
- **API**: REST endpoints
- **Usecase**: Lógica de negócio
