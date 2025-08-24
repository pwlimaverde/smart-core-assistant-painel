---
trigger: manual
---
# Project Rules and Standards

This document defines the conventions, tools, and best practices to be followed in this project's development. Adherence to these rules is mandatory to maintain code quality, consistency, and maintainability.

## 1. Development Environment

- **Core Technology**: The project is developed in Python using the Django framework.
- **Containerized Environment**: Development and testing are performed in a **Docker** environment. It is essential that all operations, especially tests, are carried out within this environment to ensure consistency.
- **Dependency Management**: We use `uv` to manage dependencies.
  - To install production dependencies: `uv sync`
  - To install development dependencies: `uv sync --dev`
- **Windows Environment**: The primary development environment is Windows. Solutions and scripts must be compatible.

## 2. Code Structure and Standards

- **Main Directory**: All application source code is located in `src/smart_core_assistant_painel/`.
- **Style Guide**: Strictly follow **PEP8**.
- **Line Length**: The maximum limit is **79 characters** per line.
- **Naming Conventions**:
  - **Variables and Functions**: `snake_case` (e.g., `my_function`).
  - **Classes**: `PascalCase` (e.g., `MyClass`).
  - All names must be in **English**.
- **Comments**: Comments should be in **Portuguese** and used to explain complex logic or important design decisions.
- **Type Annotations (Type Hints)**:
  - **MANDATORY**: All functions and methods (including tests and private ones) must have complete type annotations.
  - **Functions with no return**: Use `-> None`.
  - **Django Signals**: Use `sender: Any`, `instance: ModelClass`, `created: bool`, `**kwargs: Any` as applicable.
  - **`Union` Types**: Always check the object's type with `isinstance()` before accessing its members.
    ```python
    # Example of Union type checking
    if isinstance(response, dict):
        value = response.get("key", default)
    else: # Assuming the other type is a Pydantic/Django object
        value = response.attribute
    ```
- **Import Pattern in `__init__.py`**:
  - To facilitate access to a module's components, `__init__.py` files should be used as a "facade," centralizing and exposing the module's public API.
  - **Centralization**: Import the main objects from the module into the `__init__.py`.
  - **Exposure**: Use the `__all__` variable to explicitly define which objects are part of the public API.
  - **Documentation**: Include a `docstring` at the beginning of the file explaining the module's purpose.
  - **Example**:
    ```python
    """
    This module centralizes and exposes the application's main services.
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

## 3. Quality and Automation Tools

### 3.1. Code Quality
Code quality is ensured by a set of tools that automate formatting, linting, and type checking.

- **Formatting and Linting**: `ruff` is the primary tool for formatting (`ruff format`), linting (`ruff check`), and import sorting.
- **Type Checking**: `mypy` is used for static type checking. The `ignore_missing_imports = true` setting is active.

### 3.2. Logging and Terminal Output
- **Structured Logs**: Use `loguru` to generate structured and more detailed logs where applicable.
- **Terminal Outputs**: Use `rich` to create richer and more readable console outputs, especially in scripts and management commands.

### 3.3. Commands and Tasks (Taskipy)
Use the scripts defined in `pyproject.toml` for common tasks. Run them with `uv run task <task_name>`.

| Category      | Command          | Description                                                    |
|---------------|------------------|----------------------------------------------------------------|
| **Server**    | `dev`, `start`   | Starts the development server.                                 |
| **Testing**   | `test-docker`    | **(PREFERRED)** Runs all tests in the Docker environment.      |
|               | `test-all`       | Runs all tests locally (business logic + apps).                |
|               | `test`           | Runs only business logic tests (`tests/` folder).              |
|               | `test-apps`      | Runs only Django application tests (`src/` folders).           |
| **Quality**   | `format`         | Formats the code with `ruff format`.                           |
|               | `lint`           | Runs the linter with `ruff check`.                             |
|               | `type-check`     | Runs the type checker with `mypy`.                             |
| **Django**    | `migrate`        | Applies database migrations.                                   |
|               | `makemigrations` | Creates new migration files.                                   |
|               | `createsuperuser`| Creates a superuser.                                           |
|               | `shell`          | Starts the Django shell.                                       |

## 4. Testing

- **Framework**: Tests are written with `pytest`, and coverage is analyzed with `pytest-cov`.
- **Main Command**: **ALWAYS** run tests with the `uv run task test-docker` command.
- **Test Structure**:
  - **Django Application Tests**: (Models, Views, etc.) should be placed in the `tests/` folder of the respective application.
    - *Example*: `src/smart_core_assistant_painel/app/user_management/tests/test_models.py`
  - **Business Logic Tests**: (Services, Use Cases) should be placed in the root `tests/` directory, mirroring the `src/` structure.
    - *Example*: `tests/modules/ai_engine/test_usecase.py`
- **Minimum Coverage**: Test coverage must be at least **80%**.
- **Test Quality**: All test functions and methods must have complete type annotations.

## 5. Review and Versioning Process

- **Commits**: Commit messages must follow the **Conventional Commits** standard.
  - `feat`: A new feature.
  - `fix`: A bug fix.
  - `docs`: Documentation only changes.
  - `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).
  - `refactor`: A code change that neither fixes a bug nor adds a feature.
  - `test`: Adding missing tests or correcting existing tests.
  - `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation.
- **Pull Requests (PRs)**:
  - Must pass all CI checks (linting, type checking, tests).
  - Test coverage must meet the minimum requirement.
  - New features must be accompanied by tests and, if necessary, documentation.
- **Pre-Commit Hooks**: The project uses `pre-commit hooks` to ensure code quality before the commit.

## 6. Security and Performance

### 6.1. Security
- **Secrets**: Never commit secrets, API keys, or sensitive configurations. Use environment variables with `python-decouple`.
- **Dependencies**: Keep dependencies updated to patch vulnerabilities.
- **Best Practices**: Follow Django's security best practices.

### 6.2. Performance
- **Database Queries**: Optimize ORM queries, using `select_related` and `prefetch_related` where appropriate.
- **Caching**: Implement caching strategies for frequently accessed data.
- **Asynchronous Code**: Use `async/await` for I/O-bound operations where beneficial.

## 7. Documentation

- **Tool**: Documentation is generated with `mkdocs` and the `material` theme.
- **Docstrings**: Must follow the **Google** style. The API documentation is automatically generated from docstrings via `mkdocstrings`.
- **Maintenance**: Documentation must be kept up-to-date.

## 8. Guidelines for AI Interaction (Jules)

- **Communication**: Always interact in **Portuguese**.
- **Commit Suggestion**: When completing a task, always provide a commit message suggestion in the Conventional Commits format.
- **Project Context**: Always consider the tools and standards in this document when providing solutions.
- **Test Command**: When discussing tests, always recommend using `uv run task test-docker`.