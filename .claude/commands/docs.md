# /docs - Gerar/Atualizar Documentação

Gera ou atualiza documentação técnica do projeto.

## Instruções

1. **Use o skill de documentation**
   - `.context/skills/documentation/SKILL.md`

2. **Consulte o agente especializado**
   - `.context/agents/documentation-writer.md`

3. **Tipos de Documentação**
   - Docstrings (Google style)
   - README de módulo
   - Documentação de API (OpenAPI)
   - Diagramas (Mermaid)

4. **Locais de Documentação**
   - `.context/docs/` - Documentação de contexto
   - `docs/` - Documentação pública (MkDocs)
   - `docs_dev/` - Documentação de desenvolvimento

## Parâmetros

- `$ARGUMENTS`: Módulo ou tipo de documentação

## Exemplo de Uso

```
/docs api atendimentos           # Documenta API de atendimentos
/docs module ai_engine           # Documenta módulo ai_engine
/docs update architecture        # Atualiza docs de arquitetura
```

## Checklist

- [ ] Docstrings em funções públicas
- [ ] README do módulo/feature
- [ ] Exemplos de uso
- [ ] Diagramas onde útil
- [ ] Changelog atualizado
