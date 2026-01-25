# AGENTS.md

## Dicas do ambiente de desenvolvimento

- Instale dependências com `pip install -r requirements.txt` ou `poetry install` antes de executar scaffolds.
- Use `docker-compose up` para iniciar o ambiente local completo.
- Execute migrações com `python manage.py migrate` antes de testar novas funcionalidades.
- Armazene artefatos gerados em `.context/` para manter as execuções determinísticas.

## Instruções de Teste

- Execute `pytest` para rodar a suíte de testes.
- Use `pytest -f` (se `pytest-watch` estiver instalado) para iterar em testes que falham.
- Acione `pytest` e `ruff check .` antes de abrir um PR para imitar a CI.
- Adicione ou atualize testes junto com qualquer mudança em geradores ou CLI.

## Instruções de PR

- Siga Conventional Commits (por exemplo, `feat(scaffolding): adicionar links de documentação`).
- Faça links cruzados de novos scaffolds em `docs/README.md` e `agents/README.md` para que futuros agentes possam encontrá-los.
- Anexe saídas de exemplo da CLI ou markdown gerado quando o comportamento mudar.
- Confirme que os artefatos construídos correspondem às novas mudanças no código fonte.

## Mapa do Repositório

- `CHANGELOG.md/` — Histórico de mudanças do projeto.
- `CLAUDE.md/` — Regras e instruções específicas para agentes Claude.
- `cspell.json/` — Configurações do corretor ortográfico.
- `docker/` — Configurações de contêineres e orquestração.
- `docs/` — Documentação viva produzida por esta ferramenta.
- `docs_dev/` — Documentação técnica de desenvolvimento e planejamento.
- `mkdocs.yml/` — Configuração para geração de site de documentação estática.
- `pyproject.toml/` — Configuração do projeto Python e dependências.

## Referências de Contexto de IA

- Índice de documentação: `.context/docs/README.md`
- Playbooks de agentes: `.context/agents/README.md`
- Guia de contribuição: `CONTRIBUTING.md` (ou `docs/development-workflow.md`)
