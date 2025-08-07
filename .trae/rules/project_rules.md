# Project Rules - Configuration for AI in Trae IDE

## Main framework and tools
- The project is developed in Python using Django.
- The server and scripts are executed via commands defined in pyproject.toml (`dev`, `start`, `server`, `cluster`).
- Use `ruff format` for automatic code formatting, with autopep8 available as fallback with aggressiveness 3 and a 79-character line limit.
- Sort imports with `isort` using the "black" profile, maintaining trailing commas and parentheses.
- Perform linting with `ruff` and automatic formatting via ruff as well.
- Run tests with `pytest` and analyze coverage with `pytest-cov`.
- Static type checking is done with `mypy`, with ignore_missing_imports enabled.
- Use `loguru` for structured logging when applicable.
- Always respond in Portuguese when interacting with the user.
- The development environment is Windows-based.
- Use `uv` for dependency management and virtual environment handling.
- Consider using `blue` formatter as an alternative when needed.
- Use `rich` for enhanced terminal output when applicable.

## Code organization and structure
- Source code is located in `src/smart_core_assistant_painel/`.
- All Python files must strictly follow PEP8 with maximum line length of 79 characters.
- Comments are mandatory in Portuguese to explain complex logic, important flows, and critical parts.
- Variable and function names must be in English following snake_case convention for better readability.
- Class names should follow PascalCase convention.
## Test Organization and Structure

### Django App Tests
- Django app-specific tests (models, views, forms, admin, etc.) should be placed inside each app's directory in a `tests/` subdirectory or `tests.py` file.
- These tests are directly related to Django functionality and should stay close to the app code.
- Example: `src/smart_core_assistant_painel/app/user_management/tests/test_models.py`

### Module and Business Logic Tests
- Tests for business logic, services, use cases, and domain modules must be placed in the root `tests/` directory (not inside `src/`).
- Inside the root `tests/`, maintain a folder structure that exactly mirrors the source modules structure.
- Test files should follow the pattern `test_*.py` or `*_test.py`.
- Example: `tests/modules/ai_engine/features/whatsapp_services/test_usecase.py` mirrors `src/smart_core_assistant_painel/modules/ai_engine/features/whatsapp_services/usecase.py`

### General Test Rules
- Never place business logic tests directly inside source code directories to ensure clear separation.
- Both Django app tests and module tests must maintain the same hierarchical folder structure as their corresponding source code.
- All test directories must include `__init__.py` files to ensure proper Python package structure.
- A minimum coverage of 80% is mandatory. Anything below must be justified and reviewed.
- Avoid lines longer than 79 characters to facilitate reading and code review.
- Use type hints consistently throughout the codebase for better code documentation and IDE support.
- ALL functions and methods MUST have complete type annotations including parameters and return types.
- Use `from typing import Any` when dealing with Django signals or dynamic types.
- For Django signal handlers, use these standard type annotations:
  - `sender: Any` for the sender parameter
  - `instance: ModelClass` for the specific model instance
  - `created: bool` for post_save signals with created parameter
  - `**kwargs: Any` for additional keyword arguments
  - `-> None` for return type when function doesn't return a value
- Private functions (starting with underscore) must also have complete type annotations.
- When working with Django models, import the model class and use it as the type annotation.
- **UNION TYPES AND TYPE CHECKING**: Always verify object types before accessing attributes when dealing with union types (e.g., `dict | BaseModel`):
  - Use `isinstance(obj, dict)` to check if object is a dictionary before accessing with `obj["key"]`
  - Use `isinstance(obj, BaseModel)` to check if object is a Pydantic model before accessing with `obj.attribute`
  - Never assume the type of objects returned from external libraries or APIs
  - Always handle both possible types in union scenarios to prevent `union-attr` MyPy errors
  - Example pattern:
    ```python
    if isinstance(response, dict):
        value = response.get("key", default)
    else:
        value = response.attribute
    ```

## Commands and tasks via `taskipy`
- Use the scripts mapped in pyproject.toml for:
  - Running the server: `dev`, `start`, `server`, `cluster`.
  - Django commands: `migrate`, `makemigrations`, `createsuperuser`, `collectstatic`, `shell`, `startapp`.
  - Development and test routines: 
    - `test` (runs pytest on the root tests/ folder for module/business logic tests)
    - `test-apps` (runs pytest on Django app tests within src/)
    - `test-all` (runs both module tests and Django app tests)
    - `lint` (ruff check on src), `format` (ruff format on src), `type-check` (mypy on src).
  - Combined routines: `setup`, `dev-setup`.
  - Specific tasks such as `faiss_to_json`.
- Ensure all commands run as indicated without errors before any merge.
- When explaining errors or issues, always suggest solutions involving pytest for testing and ruff for formatting (not autopep8, as ruff is used for formatting).
- Present routines and commands objectively, contextualizing with the scripts configured in `taskipy`.
- Always use `uv sync` for dependency installation and `uv sync --dev` for development dependencies.

## Documentation
- Document using `mkdocs` with the `mkdocs-material` theme.
- Use `mkdocstrings` and `mkdocstrings-python` for automatic API documentation.
- Docstrings should follow a consistent style, preferably Google-style.
- Documentation should be updated every sprint and validated by the AI.
- Provide clear, formatted code examples aligned with Django best practices.
- Structure responses in clear sections and use lists and code blocks for better comprehension.
- Include practical examples and use cases in documentation.
- Maintain up-to-date README.md with clear setup and usage instructions.

## Quality and review process
- Every Pull Request must contain formatted code and be free of lint errors.
- Automated tests should cover new features and bug fixes with minimum 80% coverage.
- Django app tests must cover models, views, forms, and admin functionality.
- Module/business logic tests must cover use cases, services, and domain logic.
- Both test suites (Django apps and modules) should be executed before any commit.
- Significant changes need updated documentation.
- Reviewers must verify compliance with these rules before merging.
- Encourage regular execution of linting and automated formatting to keep consistent quality.
- Advise constant static code analysis using `ruff`.
- Be direct, technical, but maintain cordiality and clarity in all interactions.
- Run the full test suite (`test-all`) before any commit to ensure no regressions.
- Use pre-commit hooks to enforce code quality standards automatically.

## Security and best practices
- Never commit secrets, API keys, or sensitive configuration to the repository.
- Use environment variables for configuration management via `python-decouple`.
- Implement proper error handling and logging throughout the application.
- Follow Django security best practices for web application development.
- Regularly update dependencies to address security vulnerabilities.
- Use secure coding practices and validate all user inputs.

## Performance considerations
- Optimize database queries and use Django ORM efficiently.
- Implement proper caching strategies where appropriate.
- Monitor application performance and identify bottlenecks.
- Use async/await patterns for I/O-bound operations when beneficial.
- Profile code performance regularly and optimize critical paths.

## AI Interaction Guidelines
- Always respond in Portuguese to maintain consistency with project language.
- Provide clear, formatted code examples aligned with Django best practices.
- When explaining errors or issues, always suggest solutions involving pytest for testing and ruff for formatting.
- Present routines and commands objectively, contextualizing with the scripts configured in `taskipy`.
- Structure responses in clear sections and use lists and code blocks for better comprehension.
- Be direct, technical, but maintain cordiality and clarity.
- Recommend minimum test coverage of 80% with pytest and pytest-cov for both Django app tests and module tests.
- Guide developers to place Django-specific tests within app directories and business logic tests in the root tests/ folder.
- Ensure test structure mirrors the source code hierarchy for easy navigation and maintenance.
- Suggest using mypy for static type analysis, taking into account the ignore_missing_imports configuration.
- Advise constant static code analysis using `ruff`.
- Encourage regular execution of linting and automated formatting to keep consistent quality.
- Always consider the Windows development environment when providing solutions.
- Prioritize solutions that work with the existing toolchain (uv, taskipy, ruff, etc.).
- Use `loguru` for structured logging when applicable.
- Consider using `blue` formatter as an alternative to ruff format when needed.
- **Sempre incluir sugestão de commit**: Em cada resumo de conclusão de tarefa, deve conter um campo "sugestão de commit" com uma mensagem de commit clara e descritiva seguindo o padrão conventional commits (feat:, fix:, test:, docs:, refactor:, etc.).