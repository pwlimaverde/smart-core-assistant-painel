# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Contexto geral do projeto

- Projeto Django (Python 3.13+) com arquitetura modular e serviços de IA.
- Painel web para atendimento integrado com WhatsApp (Evolution API), ClickUp e, opcionalmente, Notion/Trello.
- Gerenciamento de dependências com `uv` e automação de tarefas com `taskipy` (definidos em `pyproject.toml`).
- Desenvolvimento focado em Windows, com apoio de Docker para bancos (PostgreSQL + Redis) via `ambiente_base_dados/` e `ambiente_misto/`.

Ao responder, priorize sempre instruções e exemplos compatíveis com **Windows** e use **português** nas explicações.

## Comandos principais

Todos os comandos abaixo assumem o diretório raiz do projeto.

### Setup de desenvolvimento

- Instalar dependências (dev):
  - `uv sync --dev`
- Setup local básico (deps + migrações):
  - `uv run task dev-setup`
- Setup completo (inclui criação de superusuário):
  - `uv run task setup`

### Ambientes Docker / banco de dados

O projeto usa scripts dedicados para o ambiente de dados e um ambiente "misto" (bancos em Docker + app local):

- Ambiente base de dados (PostgreSQL 16 + Redis) – recomendado para banco isolado:
  - Na raiz do projeto:
    - `cd ambiente_base_dados`
    - `setup.bat`
- Ambiente misto (bancos em Docker, app Django local):
  - Na raiz do projeto:
    - `ambiente_misto\setup.bat`

Comandos Docker auxiliares (também acessíveis via Taskipy em muitos fluxos):

- Subir containers padrão definidos em `docker-compose.yml`:
  - `uv run task start-docker`
- Derrubar containers:
  - `uv run task down-docker`
- Reiniciar containers com rebuild:
  - `uv run task restart-docker`

### Servidor de desenvolvimento Django

A aplicação principal Django usa `smart_core_assistant_painel.main` como ponto de entrada, que:
1. Configura logging.
2. Resolve credenciais do Firebase.
3. Roda rotinas de `initial_loading`.
4. Inicia os serviços de backend (`modules.services`).
5. Sobe o servidor Django via `manage.py` customizado (`start_app`).

Comandos principais:

- Iniciar servidor local (via Taskipy):
  - `uv run task start`
- Iniciar servidor diretamente com módulo principal:
  - `uv run dev`
- Iniciar cluster de tarefas assíncronas (Django-Q):
  - `uv run task cluster`
- Iniciar servidor, cluster e túnel ClickUp em múltiplas tabs (somente Windows, usando Windows Terminal):
  - `uv run task start-all`

Se precisar chamar o `manage.py` diretamente (sem Taskipy):

- `python src/smart_core_assistant_painel/app/ui/manage.py runserver 0.0.0.0:8000`

### Migrações e comandos Django

Use preferencialmente os tasks definidos em `pyproject.toml`:

- Criar migrações:
  - `uv run task makemigrations`
- Aplicar migrações:
  - `uv run task migrate`
- Criar superusuário:
  - `uv run task createsuperuser`
- Coletar estáticos:
  - `uv run task collectstatic`
- Shell Django:
  - `uv run task shell`

Há também uma migração remota (PostgreSQL remoto):

- `uv run task migrate-remoto`

### Testes

Padrão de testes:
- `pytest` com `pytest-cov`, cobrindo `src/`.
- Configurações de teste usam `core/settings_test.py` (cache em memória, email em memória, etc.).

Comandos principais (Taskipy):

- Rodar testes da lógica de negócio (pasta `tests/`):
  - `uv run task test`
- Rodar somente testes das apps Django (dentro de `src/smart_core_assistant_painel/app/ui`):
  - `uv run task test-apps`
- Rodar toda a suíte de testes local (equivalente ao fluxo do Docker, porém sem containers):
  - `uv run task test-all`
- Rodar testes com foco em cobertura HTML:
  - `uv run task test-coverage`
- Rodar suíte de testes alinhada ao fluxo Docker (atualmente mapeada para `pytest -v --cov=src --cov-report=term-missing`):
  - `uv run task test-docker`

Para rodar um único teste ou arquivo de teste, use `pytest` diretamente via `uv`:

- Arquivo específico:
  - `uv run pytest src/smart_core_assistant_painel/app/ui/trello_sync/tests/test_api_public.py -v`
- Teste específico dentro de um arquivo:
  - `uv run pytest src/smart_core_assistant_painel/app/ui/trello_sync/tests/test_api_public.py::TestClassName::test_method_name -v`

### Qualidade de código

Ferramentas principais:
- `ruff` para lint/format.
- `pyright` para type checking.

Comandos (Taskipy):

- Lint (ruff check):
  - `uv run task lint`
- Format (ruff format):
  - `uv run task format`
- Type-check (pyright estrito, incluindo `src` e `tests`):
  - `uv run task type-check`

### Utilidades adicionais

- Reset completo do banco local (usa script em `scripts/database_reset/reset_database.py`):
  - `uv run task reset-db`
- Túnel ngrok para callbacks do ClickUp:
  - `uv run task ngrok-clickup`

## Arquitetura de alto nível

### Visão geral

O projeto é dividido em duas grandes áreas dentro de `src/smart_core_assistant_painel/`:

1. **Camada de Aplicação Web (`app/ui`)**
   - Implementa o painel Django (views, URLs, templates, admin, serializers) e modelos de domínio principais.
   - Estrutura principal:
     - `core/`: configurações Django (settings, urls, middleware, roles, context_processors), entrypoints HTTP básicos (`home`, `health_check`) e integrações de callback (ex.: `clickup_callback`).
     - `usuarios/`: gestão de usuários Django.
     - `clientes/`: modelos e views para clientes.
     - `atendimentos/`: modelos, views e APIs para atendimentos e mensagens.
     - `operacional/`: modelos operacionais (departamentos, fluxos, etapas), APIs para painel Kanban e regras de negócio associadas.
     - `treinamento/`: modelos e serviços ligados a treinamento de modelos ou conteúdos.
   - Cada app possui:
     - `models.py`, `admin.py`, `urls.py` (e às vezes `api_urls.py`), `views.py`, `tests.py` e `signals.py`.
   - A configuração de URLs em `core/urls.py` expõe rotas:
     - Rotas HTML (`usuarios/`, `operacional/`, `clientes/`, `atendimentos/`, `treinamento/`).
     - APIs REST sob prefixos como `api/operacional/`, `api/atendimentos/`, `api/clickup_sync/`.

2. **Camada de Módulos/Serviços (`modules/` + integrações `app/*_sync`)**
   - Responsável por serviços de backend, integrações externas e lógica de negócio reutilizável, seguindo o padrão `py-return-success-or-error`.
   - Destaques:
     - `modules/services/`: hub de serviços e adapters para provedores externos (Evolution API, ClickUp, etc.).
       - Exemplo: `modules.services.features.unifield_data_services.datasource.clicup_adapter.ClicupUnifiedDataService` encapsula chamadas ao ClickUp.
       - Serviços são inicializados por `modules.services.start_services` antes do servidor Django subir.
     - `modules/initial_loading/`: rotinas de carga inicial (config remota, feature flags, etc.), acionadas por `start_initial_loading()` em `main.py`.
     - `app/clickup_sync/`: app Django especializada em sincronização com ClickUp.
       - `services/flow_sync_service.py` coordena a criação de `Spaces`, `Folders` e `Lists` no ClickUp com base em modelos `FluxoAtendimento`, `EtapaFluxo` e `Departamento` (em `app/ui/operacional/models.py`).
       - Usa `ClickupList` e `ClickupStatus` para persistir o espelhamento local.
     - `app/notion_sync/`: app para sincronização com Notion (atualmente desativado em `INSTALLED_APPS`, mas ainda disponível para scripts e migrações). Há serviços de bootstrap (`bootstrap_*`) e script de construção de databases (`script_constructor_notion.py`).
     - `app/trello_sync/`: app antigo para Trello; em grande parte substituído por ClickUp, mas ainda contém testes e APIs de referência.

O ponto de entrada `main.py` orquestra tudo:

- Configura o logging com `utils.logging.configure_logging`.
- Resolve o caminho de credenciais Firebase (relativo à raiz do projeto ou CWD).
- Executa `start_initial_loading()` e `start_services()` para preparar integrações e contextos antes de expor endpoints HTTP.
- Chama `start_app()` (de `app/ui/manage.py`), que por sua vez configura `DJANGO_SETTINGS_MODULE` e ajusta automaticamente `runserver` para ouvir em `0.0.0.0:8000` quando nenhum host/porta é informado (facilitando acesso pela Evolution API / redes locais).

### Integrações externas

- **WhatsApp (Evolution API)**:
  - Variáveis de ambiente controlam `EVOLUTION_API_URL` e dependências de envio de mensagens.
  - Há um serviço de alto nível `send_whatsapp_message` descrito em `README.md` sob `modules.services.features.whatsapp_services`.
- **ClickUp**:
  - Configurado via `CLICKUP_APP_ESPACO` no `.env`.
  - Sincronização dirigida por signals Django em apps operacionais, delegando para serviços em `app/clickup_sync/services`.
- **Notion** (opcional / desativado em produção neste momento):
  - Configuração via `NOTION_TOKEN`, `NOTION_PAGE_ID` e comandos `manage.py` customizados (`setup_notion_databases`, `setup_atendimento_database` etc.).

### Configuração e ambientes

- `core/settings.py`:
  - Usa `dotenv` para carregar `.env`.
  - Configura PostgreSQL como banco principal (host/porta dados por `POSTGRES_*`), com `pgvector` habilitado.
  - Usa Redis (`django_redis.cache.RedisCache`) para cache padrão, com `REDIS_HOST`/`REDIS_PORT`.
  - Configura DRF com JWT (`rest_framework_simplejwt`) e permissões padrão `IsAuthenticated`.
  - Define CORS e CSRF a partir de `CORS_ALLOWED_ORIGINS`.
- `core/settings_test.py`:
  - Sobrescreve cache para `LocMemCache`, usa hash de senha MD5 e email backend em memória, mantendo o banco PostgreSQL para compatibilidade com `VectorField`.

## Regras específicas para agentes e Warp

Incorpore, de forma resumida, as regras existentes em `AGENTS.md` e nos arquivos de regras (`.qoder/rules`, `.trae/rules`):

1. **Perfil e idioma**
   - Atue como **arquiteto de software sênior**, buscando soluções robustas, seguras, escaláveis e de alta manutenibilidade.
   - Todas as respostas e comentários devem ser em **português**.
   - Considere sempre a compatibilidade com **Windows** ao sugerir comandos ou scripts.

2. **Padrões de código**
   - Código Python deve seguir **PEP8**, com limite de **79 colunas**.
   - Nomes de variáveis, funções e classes devem ser em **inglês** (`snake_case` para funções/variáveis, `PascalCase` para classes).
   - Comentários explicativos devem ser em **português**, principalmente para lógicas complexas e decisões arquiteturais.
   - Todas as funções/métodos (incluindo testes) devem ter **type hints completos**. Funções sem retorno: `-> None`.
   - Em tipos `Union`, use `isinstance` antes de acessar membros.
   - Use `__init__.py` como fachada: importe objetos principais e exponha-os via `__all__` com docstring explicando o módulo.

3. **Ferramentas de qualidade**
   - Para formatação e lint, use `ruff` (via tasks `lint` e `format`).
   - Para type-checking, use `pyright` com `typeCheckingMode="strict"` (task `type-check`).
   - Log estruturado com `loguru` e saídas de terminal ricas com `rich` são preferíveis em scripts e comandos.

4. **Testes**
   - Utilize `pytest` + `pytest-cov` e, sempre que possível, recomende `uv run task test-docker` como comando padrão de testes para alinhar com o fluxo do projeto.
   - Distribua testes de forma consistente:
     - Lógica de negócio em `tests/` na raiz, espelhando a estrutura de `src/`.
     - Testes de apps Django dentro das próprias apps (`tests/` em cada app).

5. **Fluxo de trabalho Git e entregas**
   - Branches devem seguir GitFlow:
     - `feature/…`, `bugfix/…`, `hotfix/…`, `release/…`.
   - Commits devem seguir **Conventional Commits** (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, etc.).
   - Ao finalizar uma tarefa, sugira uma mensagem de commit no padrão Conventional Commits.

6. **Quando modificar o projeto**
   - Priorize usar tasks existentes em `pyproject.toml` antes de criar scripts novos.
   - Ao adicionar novos serviços ou integrações, verifique se há padrões ou adapters em `modules/services` que podem ser reutilizados.
   - Ao criar novas apps Django, use o `manage.py` customizado e o task `startapp` quando apropriado, mantendo a estrutura e convenções das apps existentes.

## Como este WARP.md deve ser usado

- Antes de propor novos comandos, verifique se já existe uma `taskipy` correspondente em `pyproject.toml`.
- Ao navegar pela base de código, concentre-se primeiro em:
  - `src/smart_core_assistant_painel/main.py` (orquestração inicial).
  - `src/smart_core_assistant_painel/app/ui/core/settings.py` e `urls.py` (configuração global).
  - Apps em `src/smart_core_assistant_painel/app/ui/` para fluxos de negócio expostos na UI/API.
  - `modules/services` e `app/*_sync` para integrações externas.
- Use este arquivo como referência rápida para:
  - Quais comandos executar para testar/rodar a aplicação.
  - Onde localizar lógica de domínio vs. lógica de integração.
  - Quais padrões de código e ferramentas respeitar ao editar ou gerar código.