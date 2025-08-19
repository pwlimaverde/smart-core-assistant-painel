# Regras e Padrões do Projeto

Este documento define as convenções, ferramentas e melhores práticas a serem seguidas no desenvolvimento deste projeto. A adesão a estas regras é obrigatória para manter a qualidade, consistência e manutenibilidade do código.

## 1. Ambiente de Desenvolvimento

- **Tecnologia Principal**: O projeto é desenvolvido em Python com o framework Django.
- **Ambiente Contêinerizado**: O desenvolvimento e os testes são executados em um ambiente **Docker**. É fundamental que todas as operações, especialmente os testes, sejam realizadas dentro deste ambiente para garantir a consistência.
- **Gerenciamento de Dependências**: Usamos `uv` para gerenciar as dependências.
  - Para instalar dependências de produção: `uv sync`
  - Para instalar dependências de desenvolvimento: `uv sync --dev`
- **Ambiente Windows**: O ambiente de desenvolvimento primário é o Windows. As soluções e scripts devem ser compatíveis.

## 2. Estrutura e Padrões de Código

- **Diretório Principal**: Todo o código-fonte da aplicação se encontra em `src/smart_core_assistant_painel/`.
- **Guia de Estilo**: Siga estritamente a **PEP8**.
- **Comprimento da Linha**: O limite máximo é de **79 caracteres** por linha.
- **Nomenclatura**:
  - **Variáveis e Funções**: `snake_case` (ex: `minha_funcao`).
  - **Classes**: `PascalCase` (ex: `MinhaClasse`).
  - Todos os nomes devem ser em **inglês**.
- **Comentários**: Comentários devem ser em **português** e usados para explicar lógicas complexas ou decisões de design importantes.
- **Anotações de Tipo (Type Hints)**:
  - **OBRIGATÓRIO**: Todas as funções e métodos (incluindo os de teste e privados) devem ter anotações de tipo completas.
  - **Funções sem retorno**: Use `-> None`.
  - **Sinais do Django**: Use `sender: Any`, `instance: ModelClass`, `created: bool`, `**kwargs: Any` conforme aplicável.
  - **Tipos `Union`**: Sempre verifique o tipo do objeto com `isinstance()` antes de acessar seus membros.
    ```python
    # Exemplo de verificação de tipo Union
    if isinstance(response, dict):
        value = response.get("key", default)
    else: # Supondo que o outro tipo seja um objeto Pydantic/Django
        value = response.attribute
    ```

## 3. Ferramentas de Qualidade e Automação

### 3.1. Qualidade de Código
A qualidade do código é garantida por um conjunto de ferramentas que automatizam a formatação, linting e verificação de tipos.

- **Formatação e Linting**: `ruff` é a ferramenta principal para formatação (`ruff format`), linting (`ruff check`) e ordenação de importações.
- **Verificação de Tipos**: `mypy` é utilizado para a verificação estática de tipos. A configuração `ignore_missing_imports = true` está ativa.

### 3.2. Logs e Saídas de Terminal
- **Logs Estruturados**: Utilize `loguru` para gerar logs estruturados e mais detalhados quando aplicável.
- **Saídas no Terminal**: Utilize `rich` para criar saídas de console mais ricas e legíveis, especialmente em scripts e comandos de gerenciamento.

### 3.3. Comandos e Tarefas (Taskipy)
Use os scripts definidos no `pyproject.toml` para as tarefas comuns. Execute-os com `uv run task <nome_da_tarefa>`.

| Categoria           | Comando          | Descrição                                                              |
| ------------------- | ---------------- | ---------------------------------------------------------------------- |
| **Servidor**        | `dev`, `start`   | Inicia o servidor de desenvolvimento.                                  |
| **Testes**          | `test-docker`    | **(PREFERENCIAL)** Executa todos os testes no ambiente Docker.         |
|                     | `test-all`       | Executa todos os testes localmente (lógica de negócio + apps).         |
|                     | `test`           | Executa apenas os testes de lógica de negócio (pasta `tests/`).        |
|                     | `test-apps`      | Executa apenas os testes de aplicações Django (pastas `src/`).         |
| **Qualidade**       | `format`         | Formata o código com `ruff format`.                                    |
|                     | `lint`           | Executa o linter com `ruff check`.                                     |
|                     | `type-check`     | Executa a verificação de tipos com `mypy`.                             |
| **Django**          | `migrate`        | Aplica as migrações do banco de dados.                                 |
|                     | `makemigrations` | Cria novos arquivos de migração.                                       |
|                     | `createsuperuser`| Cria um superusuário.                                                  |
|                     | `shell`          | Inicia o shell do Django.                                              |

## 4. Testes

- **Framework**: Os testes são escritos com `pytest` e a cobertura é analisada com `pytest-cov`.
- **Comando Principal**: **SEMPRE** execute os testes com o comando `uv run task test-docker`.
- **Estrutura dos Testes**:
  - **Testes de Aplicações Django**: (Models, Views, etc.) devem ficar na pasta `tests/` da respectiva aplicação.
    - *Exemplo*: `src/smart_core_assistant_painel/app/user_management/tests/test_models.py`
  - **Testes de Lógica de Negócio**: (Serviços, Casos de Uso) devem ficar no diretório raiz `tests/`, espelhando a estrutura de `src/`.
    - *Exemplo*: `tests/modules/ai_engine/test_usecase.py`
- **Cobertura Mínima**: A cobertura de teste deve ser de, no mínimo, **80%**.
- **Qualidade dos Testes**: Todas as funções e métodos de teste devem possuir anotações de tipo completas.

## 5. Processo de Revisão e Versionamento

- **Commits**: As mensagens de commit devem seguir o padrão **Conventional Commits**.
  - `feat`: Nova funcionalidade.
  - `fix`: Correção de bug.
  - `docs`: Mudanças na documentação.
  - `style`: Mudanças de formatação e estilo.
  - `refactor`: Refatoração de código sem alteração de funcionalidade.
  - `test`: Adição ou refatoração de testes.
  - `chore`: Mudanças em build, scripts ou configuração.
- **Pull Requests (PRs)**:
  - Devem passar em todas as verificações de CI (lint, tipos, testes).
  - A cobertura de testes deve atender ao requisito mínimo.
  - Novas funcionalidades devem ser acompanhadas de testes e documentação.
- **Hooks de Pré-Commit**: O projeto utiliza `pre-commit hooks` para garantir a qualidade do código antes do commit.

## 6. Segurança e Performance

### 6.1. Segurança
- **Segredos**: Nunca comite segredos, chaves de API ou configurações sensíveis. Utilize variáveis de ambiente com `python-decouple`.
- **Dependências**: Mantenha as dependências atualizadas para corrigir vulnerabilidades.
- **Melhores Práticas**: Siga as recomendações de segurança do Django.

### 6.2. Performance
- **Consultas ao Banco**: Otimize as queries do ORM, utilizando `select_related` e `prefetch_related` quando apropriado.
- **Cache**: Implemente estratégias de cache para dados acessados com frequência.
- **Código Assíncrono**: Use `async/await` para operações de I/O-bound quando for benéfico.

## 7. Documentação

- **Ferramenta**: A documentação é gerada com `mkdocs` e o tema `material`.
- **Docstrings**: Devem seguir o estilo **Google**. A documentação da API é gerada automaticamente a partir das docstrings via `mkdocstrings`.
- **Manutenção**: A documentação deve ser mantida atualizada.

## 8. Diretrizes para Interação com a IA (Jules)

- **Comunicação**: Interaja sempre em **português**.
- **Sugestão de Commit**: Ao concluir uma tarefa, sempre forneça uma sugestão de mensagem de commit no padrão Conventional Commits.
- **Contexto do Projeto**: Sempre leve em conta as ferramentas e padrões deste documento ao fornecer soluções.
- **Comando de Teste**: Ao falar sobre testes, sempre recomende o uso de `uv run task test-docker`.
