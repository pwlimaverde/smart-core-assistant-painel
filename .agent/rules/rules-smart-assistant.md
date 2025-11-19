---
trigger: always_on
---

# Regras e Padrões do Projeto

Este documento define as convenções, ferramentas e melhores práticas a serem seguidas no desenvolvimento deste projeto. A adesão a estas regras é obrigatória para manter a qualidade, consistência e manutenibilidade do código.

## 1. Ambiente de Desenvolvimento

- **Tecnologia Central**: O projeto é desenvolvido em Python utilizando o framework Django.
- **Ambiente Containerizado**: O desenvolvimento e os testes são realizados em um ambiente **Docker**. É essencial que todas as operações, especialmente os testes, sejam realizadas dentro deste ambiente para garantir a consistência.
- **Gerenciamento de Dependências**: Utilizamos o `uv` para gerenciar dependências.
  - Para instalar dependências de produção: `uv sync`
  - Para instalar dependências de desenvolvimento: `uv sync --dev`
  - Para realizar as migrações do django utilise os comandos: `uv run task makemigrations` e `uv run task migrate-remoto`
- **Ambiente Windows**: O ambiente de desenvolvimento primário é Windows. Soluções e scripts devem ser compatíveis.

## 2. Estrutura e Padrões de Código

- **Diretório Principal**: Todo o código-fonte da aplicação está localizado em `src/smart_core_assistant_painel/`.
- **Guia de Estilo**: Seguir estritamente a **PEP8**.
- **Comprimento da Linha**: O limite máximo é de **79 caracteres** por linha.
- **Convenções de Nomenclatura**:
  - **Variáveis e Funções**: `snake_case` (ex: `minha_funcao`).
  - **Classes**: `PascalCase` (ex: `MinhaClasse`).
  - Todos os nomes devem estar em **Inglês**.
- **Comentários**: Os comentários devem ser em **Português** e usados para explicar lógicas complexas ou decisões de design importantes.
- **Anotações de Tipo (Type Hints)**:
  - **OBRIGATÓRIO**: Todas as funções e métodos (incluindo testes e privados) devem ter anotações de tipo completas.
  - **Funções sem retorno**: Use `-> None`.
  - **Sinais do Django (Signals)**: Use `sender: Any`, `instance: ModelClass`, `created: bool`, `**kwargs: Any` conforme aplicável.
  - **Tipos `Union`**: Sempre verifique o tipo do objeto com `isinstance()` antes de acessar seus membros.
    ```python
    # Exemplo de verificação de tipo Union
    if isinstance(response, dict):
        value = response.get("key", default)
    else: # Assumindo que o outro tipo é um objeto Pydantic/Django
        value = response.attribute
    ```
- **Padrão de Importação em `__init__.py`**:
  - Para facilitar o acesso aos componentes de um módulo, arquivos `__init__.py` devem ser usados como uma "fachada" (facade), centralizando e expondo a API pública do módulo.
  - **Centralização**: Importe os objetos principais do módulo para o `__init__.py`.
  - **Exposição**: Use a variável `__all__` para definir explicitamente quais objetos fazem parte da API pública.
  - **Documentação**: Inclua uma `docstring` no início do arquivo explicando o propósito do módulo.
  - **Exemplo**:
    ```python
    """
    Este módulo centraliza e expõe os principais serviços da aplicação.
    """
    from .features.service_hub import SERVICEHUB, ServiceHub
    from .utils.errors import VectorStorageError, WhatsAppServiceError
    from .utils.types import VSUsecase, WSUsecase

    __all__ = [
        # Service Hub
        "ServiceHub",
        "SERVICEHUB",
        # Errors
        "WhatsAppServiceError",
        "VectorStorageError",
        # Types
        "VSUsecase",
        "WSUsecase",
    ]
    ```

## 3. Ferramentas de Qualidade e Automação

### 3.1. Qualidade de Código
A qualidade do código é garantida por um conjunto de ferramentas que automatizam a formatação, linting e verificação de tipos.

- **Formatação e Linting**: `ruff` é a ferramenta principal para formatação (`ruff format`), linting (`ruff check`) e ordenação de importações.
- **Verificação de Tipos**: `pyright` é usado para verificação estática de tipos em modo estrito (`strict`). Certifique-se de que não há erros de tipo antes de submeter código.

### 3.2. Logging e Saída de Terminal
- **Logs Estruturados**: Use `loguru` para gerar logs estruturados e mais detalhados onde aplicável.
- **Saídas de Terminal**: Use `rich` para criar saídas de console mais ricas e legíveis, especialmente em scripts e comandos de gerenciamento.

### 3.3. Comandos e Tarefas (Taskipy)
Use os scripts definidos no `pyproject.toml` para tarefas comuns. Execute-os SEMPRE com `uv run task <nome_da_tarefa>`.

| Categoria     | Comando          | Descrição                                                      |
|---------------|------------------|----------------------------------------------------------------|
| **Servidor**  | `dev`, `start`   | Inicia o servidor de desenvolvimento local.                    |
|               | `cluster`        | Inicia o cluster Django Q.                                     |
|               | `start-all`      | Inicia servidor, cluster e ngrok em abas separadas (Windows).  |
| **Docker**    | `start-docker`   | Sobe os containers (`docker compose up -d`).                   |
|               | `restart-docker` | Reinicia os containers com build.                              |
|               | `logs-docker`    | Visualiza logs do container `django-app`.                      |
| **Testes**    | `test-docker`    | **(PREFERIDO)** Roda todos os testes no ambiente Docker.       |
|               | `test-all`       | Roda todos os testes localmente (lógica de negócio + apps).    |
|               | `test`           | Roda apenas testes de lógica de negócio (pasta `tests/`).      |
|               | `test-apps`      | Roda apenas testes de aplicações Django (pastas `src/`).       |
| **Qualidade** | `format`         | Formata o código com `ruff format`.                            |
|               | `lint`           | Roda o linter com `ruff check`.                                |
|               | `type-check`     | Roda o verificador de tipos com `pyright`.                     |
| **Django**    | `migrate`        | Aplica migrações de banco de dados (local).                    |
|               | `migrate-remoto` | Aplica migrações no banco de dados remoto (PostgreSQL).        |
|               | `makemigrations` | Cria novos arquivos de migração.                               |
|               | `createsuperuser`| Cria um superusuário.                                          |
|               | `shell`          | Inicia o shell do Django.                                      |
| **Setup**     | `dev-setup`      | Instala deps dev e roda migrações locais.                      |
|               | `reset-db`       | Reseta o banco de dados (Cuidado!).                            |

## 4. Testes

- **Framework**: Os testes são escritos com `pytest`, e a cobertura é analisada com `pytest-cov`.
- **Comando Principal**: **SEMPRE** execute os testes com o comando `uv run task test-docker` para garantir que o ambiente seja idêntico ao de produção/CI.
- **Estrutura de Testes**:
  - **Testes de Aplicação Django**: (Models, Views, etc.) devem ser colocados na pasta `tests/` da respectiva aplicação.
    - *Exemplo*: `src/smart_core_assistant_painel/app/user_management/tests/test_models.py`
  - **Testes de Lógica de Negócio**: (Services, Use Cases) devem ser colocados no diretório `tests/` raiz, espelhando a estrutura de `src/`.
    - *Exemplo*: `tests/modules/ai_engine/test_usecase.py`
- **Cobertura Mínima**: A cobertura de testes deve ser de pelo menos **80%**.
- **Qualidade dos Testes**: Todas as funções e métodos de teste devem ter anotações de tipo completas.

## 5. Processo de Revisão e Versionamento

- **Commits**: As mensagens de commit devem seguir o padrão **Conventional Commits**.
  - `feat`: Uma nova funcionalidade.
  - `fix`: Uma correção de bug.
  - `docs`: Alterações apenas na documentação.
  - `style`: Alterações que não afetam o significado do código (espaços em branco, formatação, ponto e vírgula faltando, etc).
  - `refactor`: Uma alteração de código que nem corrige um bug nem adiciona uma funcionalidade.
  - `test`: Adição de testes ausentes ou correção de testes existentes.
  - `chore`: Alterações no processo de build ou ferramentas auxiliares e bibliotecas, como geração de documentação.
- **Pull Requests (PRs)**:
  - Devem passar em todas as verificações de CI (linting, verificação de tipos, testes).
  - A cobertura de testes deve atender ao requisito mínimo.
  - Novas funcionalidades devem ser acompanhadas de testes e, se necessário, documentação.
- **Pre-Commit Hooks**: O projeto utiliza `pre-commit hooks` para garantir a qualidade do código antes do commit.

## 6. Segurança e Desempenho

### 6.1. Segurança
- **Segredos**: Nunca faça commit de segredos, chaves de API ou configurações sensíveis. Use variáveis de ambiente com `python-decouple`.
- **Dependências**: Mantenha as dependências atualizadas para corrigir vulnerabilidades.
- **Melhores Práticas**: Siga as melhores práticas de segurança do Django.

### 6.2. Desempenho
- **Consultas ao Banco de Dados**: Otimize consultas ORM, usando `select_related` e `prefetch_related` onde apropriado.
- **Cache**: Implemente estratégias de cache para dados acessados frequentemente.
- **Código Assíncrono**: Use `async/await` para operações limitadas por I/O (I/O-bound) onde for benéfico.

## 7. Documentação

- **Ferramenta**: A documentação é gerada com `mkdocs` e o tema `material`.
- **Docstrings**: Devem seguir o estilo **Google**. A documentação da API é gerada automaticamente a partir das docstrings via `mkdocstrings`.
- **Manutenção**: A documentação deve ser mantida atualizada.

## 8. Diretrizes para o Agente (IA)

Estas regras são específicas para otimizar o seu desempenho como assistente de codificação neste projeto:

1.  **Verificação de Comandos**: Antes de sugerir ou executar qualquer comando, verifique o arquivo `pyproject.toml` para ver se existe uma tarefa (`task`) configurada para isso.
    -   **Sempre** use `uv run task <nome_da_tarefa>` em vez de chamar `python` ou `pytest` diretamente.
2.  **Consistência de Testes**: Ao depurar ou verificar código, dê preferência ao comando `uv run task test-docker`. Se precisar rodar um teste específico, use `uv run task test-docker -- -k "nome_do_teste"`.
3.  **Análise de Tipos**: Se encontrar erros de tipo, lembre-se que o projeto usa `pyright` em modo estrito. Não tente suprimir erros cegamente; corrija a causa raiz ou use `# type: ignore` apenas como último recurso e com justificativa.
4.  **Contexto**: Ao criar novos arquivos, sempre verifique onde eles se encaixam na arquitetura existente (Django App vs. Módulo de Lógica de Negócio) e siga a estrutura de pastas correspondente.
5.  **Linguagem**: Mantenha toda a comunicação, **planos de implementação**, docstrings e comentários em **Português**, mas o código (nomes de variáveis, funções, classes) em **Inglês**.
