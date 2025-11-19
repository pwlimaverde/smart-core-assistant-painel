---
trigger: always_on
---

---
trigger: always_on
---

# Regras do Projeto - Configuração para IA no Trae IDE

## Framework principal e ferramentas
- O projeto é desenvolvido em Python usando Django.
- **O ambiente de desenvolvimento e testes é baseado em Docker.**
- O servidor e scripts são executados via comandos definidos no pyproject.toml (`dev`, `start`, `server`, `cluster`).
- **Para testes, use sempre o comando `test-docker` que roda os testes no ambiente Docker.**
- Use `ruff format` para formatação automática de código, com autopep8 disponível como fallback com agressividade 3 e limite de linha de 79 caracteres.
- Ordene importações com `isort` usando o perfil "black", mantendo vírgulas finais e parênteses.
- Realize linting com `ruff` e formatação automática via ruff também.
- Execute testes com `pytest` e analise cobertura com `pytest-cov`.
- Verificação estática de tipos é feita com `mypy`, com ignore_missing_imports habilitado.
- Use `loguru` para logging estruturado quando aplicável.
- Sempre responda em Português ao interagir com o usuário.
- O ambiente de desenvolvimento é Windows.
- Use `uv` para gerenciamento de dependências e ambiente virtual.
- Considere usar o formatador `blue` como alternativa quando necessário.
- Use `rich` para saída de terminal aprimorada quando aplicável.

## Organização e estrutura de código
- O código-fonte está localizado em `src/smart_core_assistant_painel/`.
- Todos os arquivos Python devem seguir estritamente a PEP8 com comprimento máximo de linha de 79 caracteres.
- Comentários são obrigatórios em Português para explicar lógica complexa, fluxos importantes e partes críticas.
- Nomes de variáveis e funções devem ser em Inglês seguindo a convenção snake_case para melhor legibilidade.
- Nomes de classes devem seguir a convenção PascalCase.

## Organização e Estrutura de Testes

### Testes de Apps Django
- Testes específicos de apps Django (models, views, forms, admin, etc.) devem ser colocados dentro do diretório de cada app em um subdiretório `tests/` ou arquivo `tests.py`.
- Esses testes são diretamente relacionados à funcionalidade do Django e devem ficar próximos ao código da app.
- Exemplo: `src/smart_core_assistant_painel/app/user_management/tests/test_models.py`

### Testes de Módulo e Lógica de Negócio
- Testes para lógica de negócio, serviços, casos de uso e módulos de domínio devem ser colocados no diretório raiz `tests/` (não dentro de `src/`).
- Dentro da raiz `tests/`, mantenha uma estrutura de pastas que espelhe exatamente a estrutura dos módulos fonte.
- Arquivos de teste devem seguir o padrão `test_*.py` ou `*_test.py`.
- Exemplo: `tests/modules/ai_engine/features/whatsapp_services/test_usecase.py` espelha `src/smart_core_assistant_painel/modules/ai_engine/features/whatsapp_services/usecase.py`

### Regras Gerais de Teste
- Nunca coloque testes de lógica de negócio diretamente dentro dos diretórios de código-fonte para garantir separação clara.
- Tanto testes de app Django quanto testes de módulo devem manter a mesma estrutura de pastas hierárquica que seu código-fonte correspondente.
- Todos os diretórios de teste devem incluir arquivos `__init__.py` para garantir estrutura de pacote Python adequada.
- Uma cobertura mínima de 80% é obrigatória. Qualquer coisa abaixo deve ser justificada e revisada.
- Evite linhas com mais de 79 caracteres para facilitar a leitura e revisão de código.
- Use dicas de tipo (type hints) consistentemente em toda a base de código para melhor documentação e suporte da IDE.
- TODAS as funções e métodos DEVEM ter anotações de tipo completas, incluindo parâmetros e tipos de retorno.
- Use `from typing import Any` ao lidar com sinais do Django ou tipos dinâmicos.
- Para handlers de sinais do Django, use estas anotações de tipo padrão:
  - `sender: Any` para o parâmetro sender
  - `instance: ModelClass` para a instância específica do modelo
  - `created: bool` para sinais post_save com parâmetro created
  - `**kwargs: Any` para argumentos de palavra-chave adicionais
  - `-> None` para tipo de retorno quando a função não retorna valor
- Funções privadas (começando com underscore) também devem ter anotações de tipo completas.
- Ao trabalhar com modelos Django, importe a classe do modelo e use-a como anotação de tipo.
- **TIPOS UNIÃO E VERIFICAÇÃO DE TIPO**: Sempre verifique tipos de objetos antes de acessar atributos ao lidar com tipos união (ex: `dict | BaseModel`):
  - Use `isinstance(obj, dict)` para verificar se o objeto é um dicionário antes de acessar com `obj["key"]`
  - Use `isinstance(obj, BaseModel)` para verificar se o objeto é um modelo Pydantic antes de acessar com `obj.attribute`
  - Nunca assuma o tipo de objetos retornados de bibliotecas externas ou APIs
  - Sempre trate ambos os tipos possíveis em cenários de união para prevenir erros `union-attr` do MyPy
  - Exemplo de padrão:
    ```python
    if isinstance(response, dict):
        value = response.get("key", default)
    else:
        value = response.attribute
    ```
- **ANOTAÇÕES DE TIPO EM TESTES**: Todas as funções e métodos de teste DEVEM ter anotações de tipo completas:
  - Métodos de teste devem ter anotação de retorno `-> None`
  - Funções auxiliares em testes devem ter anotações de parâmetro e tipo de retorno
  - Objetos mock e fixtures devem ser tipados adequadamente
  - Handlers de sinais em testes devem seguir as mesmas regras de tipagem do código de produção
  - Exemplo:
    ```python
    def test_example_function(self) -> None:
        """Test example with proper typing."""
        
    def helper_function(param: str) -> bool:
        """Helper function with proper typing."""
        return True
    ```

## Comandos e tarefas via `taskipy`
- Use os scripts mapeados no pyproject.toml para:
  - Rodar o servidor: `dev`, `start`, `server`, `cluster`.
  - Comandos Django: `migrate`, `makemigrations`, `createsuperuser`, `collectstatic`, `shell`, `startapp`.
  - Rotinas de desenvolvimento e teste: 
    - **`test-docker`** (PREFERIDO: roda pytest no ambiente Docker com cobertura)
    - [test](cci:1://file:///c:/PROJETOS/PYTHON/APPS/smart-core-assistant-painel/teste_debug/test_flow_simulation.py:165:0-306:37) (roda pytest na pasta raiz tests/ para testes de módulo/lógica de negócio)
    - `test-apps` (roda pytest nos testes de app Django dentro de src/)
    - `test-all` (roda ambos testes de módulo e testes de app Django)
    - `lint` (ruff check em src), `format` (ruff format em src), `type-check` (mypy em src).
  - Rotinas combinadas: `setup`, `dev-setup`.
  - Tarefas específicas como `faiss_to_json`.
- Garanta que todos os comandos rodem conforme indicado sem erros antes de qualquer merge.
- Ao explicar erros ou problemas, sempre sugira soluções envolvendo pytest para testes e ruff para formatação (não autopep8, pois ruff é usado para formatação).
- Apresente rotinas e comandos objetivamente, contextualizando com os scripts configurados no `taskipy`.
- Sempre use `uv sync` para instalação de dependências e `uv sync --dev` para dependências de desenvolvimento.

## Documentação
- Documente usando `mkdocs` com o tema `mkdocs-material`.
- Use `mkdocstrings` e `mkdocstrings-python` para documentação automática de API.
- Docstrings devem seguir um estilo consistente, preferencialmente estilo Google.
- A documentação deve ser atualizada a cada sprint e validada pela IA.
- Forneça exemplos de código claros e formatados alinhados com as melhores práticas do Django.
- Estruture respostas em seções claras e use listas e blocos de código para melhor compreensão.
- Inclua exemplos práticos e casos de uso na documentação.
- Mantenha o README.md atualizado com instruções claras de configuração e uso.

## Qualidade e processo de revisão
- Todo Pull Request deve conter código formatado e estar livre de erros de lint.
- Testes automatizados devem cobrir novas funcionalidades e correções de bugs com cobertura mínima de 80%.
- Testes de app Django devem cobrir models, views, forms e funcionalidade de admin.
- Testes de módulo/lógica de negócio devem cobrir casos de uso, serviços e lógica de domínio.
- Ambas as suítes de teste (apps Django e módulos) devem ser executadas antes de qualquer commit.
- **Sempre use `test-docker` para rodar testes, pois o projeto roda em ambiente Docker.**
- Mudanças significativas precisam de documentação atualizada.
- Revisores devem verificar conformidade com estas regras antes de fazer merge.
- Encoraje execução regular de linting e formatação automatizada para manter qualidade consistente.
- Aconselhe análise estática de código constante usando `ruff`.
- Seja direto, técnico, mas mantenha cordialidade e clareza em todas as interações.
- Rode a suíte de testes completa (`test-docker`) antes de qualquer commit para garantir que não haja regressões.
- Use hooks de pre-commit para forçar padrões de qualidade de código automaticamente.

## Segurança e melhores práticas
- Nunca commite segredos, chaves de API ou configuração sensível no repositório.
- Use variáveis de ambiente para gerenciamento de configuração via `python-decouple`.
- Implemente tratamento de erros e logging adequados em toda a aplicação.
- Siga as melhores práticas de segurança do Django para desenvolvimento de aplicações web.
- Atualize regularmente dependências para resolver vulnerabilidades de segurança.
- Use práticas de codificação segura e valide todas as entradas de usuário.

## Considerações de desempenho
- Otimize consultas de banco de dados e use o ORM do Django eficientemente.
- Implemente estratégias de cache adequadas onde apropriado.
- Monitore desempenho da aplicação e identifique gargalos.
- Use padrões async/await para operações limitadas por I/O quando benéfico.
- Faça perfilamento de código regularmente e otimize caminhos críticos.

## Diretrizes de Interação com IA
- Sempre responda em Português para manter consistência com a linguagem do projeto.
- Forneça exemplos de código claros e formatados alinhados com as melhores práticas do Django.
- Ao explicar erros ou problemas, sempre sugira soluções envolvendo pytest para testes e ruff para formatação.
- Apresente rotinas e comandos objetivamente, contextualizando com os scripts configurados no `taskipy`.
- Estruture respostas em seções claras e use listas e blocos de código para melhor compreensão.
- Seja direto, técnico, mas mantenha cordialidade e clareza.
- Recomende cobertura mínima de teste de 80% com pytest e pytest-cov tanto para testes de app Django quanto para testes de módulo.
- **Sempre recomende usar o comando `test-docker` para rodar testes no ambiente Docker adequado.**
- Guie desenvolvedores para colocar testes específicos de Django dentro de diretórios de app e testes de lógica de negócio na pasta raiz tests/.
- Garanta que a estrutura de teste espelhe a hierarquia do código-fonte para fácil navegação e manutenção.
- Sugira usar mypy para análise estática de tipos, levando em conta a configuração ignore_missing_imports.
- Aconselhe análise estática de código constante usando `ruff`.
- Encoraje execução regular de linting e formatação automatizada para manter qualidade consistente.
- Sempre considere o ambiente de desenvolvimento Windows ao fornecer soluções.
- Priorize soluções que funcionem com o toolchain existente (uv, taskipy, ruff, etc.).
- Use `loguru` para logging estruturado quando aplicável.
- Considere usar o formatador `blue` como alternativa ao ruff format quando necessário.
- **Sempre incluir sugestão de commit**: Em cada resumo de conclusão de tarefa, deve conter um campo "sugestão de commit" com uma mensagem de commit clara e descritiva seguindo o padrão conventional commits (feat:, fix:, test:, docs:, refactor:, etc.).
- **Artefatos em Português**: Todos os planos de implementação ([implementation_plan.md](cci:7://file:///C:/Users/pwlim/.gemini/antigravity/brain/2fbf8bc7-08f1-4245-8a47-dd97fda95f68/implementation_plan.md:0:0-0:0)) e listas de tarefas (`task.md`) devem ser escritos inteiramente em Português.