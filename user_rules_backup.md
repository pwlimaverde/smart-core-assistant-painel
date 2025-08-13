# User Rules - Configuration for AI in Trae IDE

## Code style and formatting
- Use `ruff format` for automatic code formatting, with autopep8 available as fallback with aggressiveness 3 and a 79-character line limit.
- Sort imports using `isort` with the "black" profile, keeping trailing commas and parentheses as configured.
- Write comments in Portuguese, clear and explanatory, especially in complex code blocks, critical flows, and logic-heavy parts.
- Use variable and function names in English, following the snake_case convention for better readability.
- Avoid lines longer than 79 characters to facilitate reading and code review.
- All Python files must strictly follow PEP8 standards.
- Class names should follow PascalCase convention.
- Use type hints consistently throughout the codebase for better code documentation and IDE support.

## Interaction with the AI
- Always respond in Portuguese to maintain consistency with project language.
- Provide clear, formatted code examples aligned with Django best practices.
- When explaining errors or issues, always suggest solutions involving pytest for testing and ruff for formatting.
- Present routines and commands objectively, contextualizing with the scripts configured in `taskipy`.
- Structure responses in clear sections and use lists and code blocks for better comprehension.
- Be direct, technical, but maintain cordiality and clarity.
- Always consider the Windows development environment when providing solutions.
- Prioritize solutions that work with the existing toolchain (uv, taskipy, ruff, etc.).

## Testing and code quality
- Always recommend minimum test coverage of 80% with pytest and pytest-cov.
- Suggest using mypy for static type analysis, taking into account the ignore_missing_imports configuration.
- Advise constant static code analysis using `ruff`.
- Encourage regular execution of linting and automated formatting to keep consistent quality.
- Test files must be placed inside the root `tests/` directory (not inside `src/`).
- Inside `tests/`, maintain a folder structure that mirrors the source apps and modules.
- Test files should follow the pattern `test_*.py` or `*_test.py`.
- Never place tests directly inside source code directories to ensure clear separation between code and tests.
- Run the full test suite before any commit to ensure no regressions.

## Project organization
- Source code should be located in appropriate `src/` directories.
- Comments are mandatory in Portuguese to explain complex logic, important flows, and critical parts.
- Variable and function names must be in English following snake_case convention for better readability.
- A minimum coverage of 80% is mandatory. Anything below must be justified and reviewed.
- Use `uv` for dependency management and virtual environment handling.

## Development workflow
- Use scripts mapped in pyproject.toml for development tasks:
  - Running the server: `dev`, `start`, `server`, `cluster`.
  - Django commands: `migrate`, `makemigrations`, `createsuperuser`, `collectstatic`, `shell`, `startapp`.
  - Development and test routines: `test`, `lint`, `format`, `type-check`.
  - Combined routines: `setup`, `dev-setup`.
- Ensure all commands run without errors before any merge.
- Every Pull Request must contain formatted code and be free of lint errors.
- Automated tests should cover new features and bug fixes with minimum 80% coverage.
- Significant changes need updated documentation.
- Always use `uv sync` for dependency installation and `uv sync --dev` for development dependencies.

## Documentation standards
- Document using `mkdocs` with the `mkdocs-material` theme when applicable.
- Use `mkdocstrings` and `mkdocstrings-python` for automatic API documentation.
- Docstrings should follow a consistent style, preferably Google-style.
- Documentation should be updated regularly and validated.
- Include practical examples and use cases in documentation.
- Maintain up-to-date README.md with clear setup and usage instructions.

## Security and best practices
- Never commit secrets, API keys, or sensitive configuration to the repository.
- Use environment variables for configuration management via `python-decouple`.
- Implement proper error handling and logging throughout the application.
- Follow Django security best practices for web application development.
- Use secure coding practices and validate all user inputs.

## Important information
- Always chat in Português.
- My system is Windows.
- The development environment is Windows-based.
- Use `loguru` for structured logging when applicable.
- Consider using `blue` formatter as an alternative when needed.
- Use `rich` for enhanced terminal output when applicable.