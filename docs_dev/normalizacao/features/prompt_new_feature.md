# Prompt para Geração de Script de Nova Feature (Aprimorado e Limpo)

## Objetivo

Gerar um script Python (`new_feature_script.py`) para automatizar a criação da estrutura de novas features, seguindo a arquitetura limpa (Clean Architecture) descrita. O script deverá ser colocado na pasta `scripts/` na raiz do projeto. Adicionalmente, configurar o `pyproject.toml` com *tasks* para execução do script, diferenciando features baseadas em `UsecaseBase` e `UsecaseBaseCallData`.

## Instruções Detalhadas para o Script `new_feature_script.py`

1.  **Localização:** `scripts/new_feature_script.py` na raiz do projeto.

2.  **Fluxo de Execução:**
    *   Ao ser executado, o script deve solicitar informações básicas ao usuário:
        *   `Informe o nome do módulo:` (Ex: `services`, `ai_engine`).
        *   `Informe o nome da feature:` (Ex: `gerar_relatorio`, `generate_chunks`).
    *   O script deverá receber um argumento (`--type base` ou `--type call_data`) para determinar o tipo de feature a ser criada.

3.  **Estrutura de Pastas (base):**
    *   O nome do projeto é fixo: `smart_core_assistant_painel`.
    *   Módulos sempre ficam em: `src/{NOME_DO_PROJETO}/modules/{NOME_DO_MODULO}/`.
    *   A estrutura base para a feature é: `src/{NOME_DO_PROJETO}/modules/{NOME_DO_MODULO}/features/{NOME_DA_FEATURE}/`.
    *   `__init__.py` deve ser criado em todos os novos diretórios (`features/{NOME_DA_FEATURE}/`, `features/{NOME_DA_FEATURE}/domain/`, `features/{NOME_DA_FEATURE}/domain/usecase/`, `features/{NOME_DA_FEATURE}/datasource/` - se aplicável).
    *   **Funções Auxiliares Necessárias no Script:**
        *   `get_project_name()`: Retorna o nome fixo do projeto.
        *   `sanitize_name(name: str) -> str`: Converte strings para `snake_case` para nomes de arquivos e diretórios.
        *   `camel_case(name: str) -> str`: Converte `snake_case` para `CamelCase` para nomes de classes.
        *   `get_feature_initials(feature_name: str) -> str`: Retorna as duas primeiras letras maiúsculas da feature (Ex: `generate_chunks` -> `GC`).

4.  **Criação e Conteúdo dos Arquivos:**

    **4.1. `src/{NOME_DO_PROJETO}/modules/{NOME_DO_MODULO}/utils/erros.py`**
    *   **Ação:** Inserir o novo erro **após a última linha existente** no arquivo.
    *   **Conteúdo a ser inserido:**
        ```python
        from dataclasses import dataclass
        from py_return_success_or_error import AppError

        @dataclass
        class {CamelCaseFeatureName}Error(AppError):
            message: str

            def __str__(self) -> str:
                return f"{CamelCaseFeatureName}Error - {{self.message}}"
        ```

    **4.2. `src/{NOME_DO_PROJETO}/modules/{NOME_DO_MODULO}/utils/parameters.py`**
    *   **Ação:** Inserir os novos parâmetros **após a última linha existente** no arquivo.
    *   **Conteúdo a ser inserido:**
        ```python
        from dataclasses import dataclass
        from typing import Any
        from py_return_success_or_error import AppError, ParametersReturnResult
        from .erros import {CamelCaseFeatureName}Error

        @dataclass
        class {CamelCaseFeatureName}Parameters(ParametersReturnResult):
            # TODO: Adicione os atributos específicos da feature aqui
            param_exemplo: str = "valor_default"
            error: type[AppError] = {CamelCaseFeatureName}Error

            def __str__(self) -> str:
                return self.__repr__()
        ```

    **4.3. `src/{NOME_DO_PROJETO}/modules/{NOME_DO_MODULO}/utils/types.py`**
    *   **Ação:** Inserir os novos tipos **após a última linha existente** no arquivo.
    *   **Nomenclatura para o `TypeAlias` do UseCase:** `{FeatureInitials}Usecase`.
    *   **Nomenclatura para o `TypeAlias` do Datasource (apenas para `call_data`):** `{FeatureInitials}Data`.
    *   **Comportamento condicional com base no argumento `--type`:**

        *   **Se `--type base`:**
            ```python
            from typing import TypeAlias
            from py_return_success_or_error import UsecaseBase
            from .parameters import {CamelCaseFeatureName}Parameters

            {FeatureInitials}Usecase: TypeAlias = UsecaseBase[
                None,
                {CamelCaseFeatureName}Parameters,
            ]
            ```

        *   **Se `--type call_data`:**
            ```python
            from typing import TypeAlias
            from py_return_success_or_error import Datasource, UsecaseBaseCallData
            from .parameters import {CamelCaseFeatureName}Parameters

            {FeatureInitials}Data: TypeAlias = Datasource[None, {CamelCaseFeatureName}Parameters]
            {FeatureInitials}Usecase: TypeAlias = UsecaseBaseCallData[
                None,
                None,
                {CamelCaseFeatureName}Parameters,
            ]
            ```

    **4.4. Estrutura de Pastas e Arquivos da Feature (`src/{NOME_DO_PROJETO}/modules/{NOME_DO_MODULO}/features/{NOME_DA_FEATURE}/`)**

        *   **Se `--type base`:**
            *   Criar diretório: `features/{snake_case_feature_name}/domain/usecase/`
            *   Criar arquivo: `features/{snake_case_feature_name}/domain/usecase/{snake_case_feature_name}_usecase.py`
            *   **Conteúdo do arquivo `{snake_case_feature_name}_usecase.py`:**
                ```python
                from py_return_success_or_error import ErrorReturn, ReturnSuccessOrError, SuccessReturn
                from ...utils.parameters import {CamelCaseFeatureName}Parameters
                from ...utils.types import {FeatureInitials}Usecase

                class {CamelCaseFeatureName}UseCase({FeatureInitials}Usecase):
                    def __call__(
                        self, parameters: {CamelCaseFeatureName}Parameters
                    ) -> ReturnSuccessOrError[None]:
                        pass
                ```

        *   **Se `--type call_data`:**
            *   Criar diretórios:
                *   `features/{snake_case_feature_name}/domain/usecase/`
                *   `features/{snake_case_feature_name}/datasource/`
            *   Criar arquivo: `features/{snake_case_feature_name}/domain/usecase/{snake_case_feature_name}_usecase.py`
            *   **Conteúdo do arquivo `{snake_case_feature_name}_usecase.py`:**
                ```python
                from py_return_success_or_error import ErrorReturn, ReturnSuccessOrError, SuccessReturn
                from ...utils.parameters import {CamelCaseFeatureName}Parameters
                from ...utils.types import {FeatureInitials}Usecase

                class {CamelCaseFeatureName}UseCase({FeatureInitials}Usecase):
                    def __call__(
                        self, parameters: {CamelCaseFeatureName}Parameters
                    ) -> ReturnSuccessOrError[None]:
                        data = self._resultDatasource(
                            parameters=parameters, datasource=self._datasource
                        )

                        if isinstance(data, SuccessReturn):
                            return SuccessReturn(data.result)
                        elif isinstance(data, ErrorReturn):
                            return ErrorReturn(parameters.error(message=f"Erro ao {acao_do_usecase}: {data.result}"))
                        else:
                            return ErrorReturn(parameters.error(message="Tipo de retorno inesperado do datasource."))
                ```
            *   Criar arquivo: `features/{snake_case_feature_name}/datasource/{snake_case_feature_name}_datasource.py`
            *   **Conteúdo do arquivo `{snake_case_feature_name}_datasource.py`:**
                ```python
                from ...utils.parameters import {CamelCaseFeatureName}Parameters
                from ...utils.types import {FeatureInitials}Data

                class {CamelCaseFeatureName}Datasource({FeatureInitials}Data):
                    def __call__(self, parameters: {CamelCaseFeatureName}Parameters) -> None:
                        pass
                ```

    **4.5. `src/{NOME_DO_PROJETO}/modules/{NOME_DO_MODULO}/features/features_compose.py`**
    *   **Ação:** Inserir um novo método estático na classe `FeaturesCompose` **após o último método existente**.
    *   **Conteúdo a ser inserido:**

        *   **Se `--type base`:**
            ```python
            from ...utils.parameters import {CamelCaseFeatureName}Parameters
            from ...utils.types import {FeatureInitials}Usecase
            from ...utils.erros import {CamelCaseFeatureName}Error
            from ..features.{snake_case_feature_name}.domain.usecase.{snake_case_feature_name}_usecase import {CamelCaseFeatureName}UseCase
            from py_return_success_or_error import ErrorReturn, SuccessReturn, ReturnSuccessOrError

            class FeaturesCompose:
                @staticmethod
                def {snake_case_feature_name}(# TODO: Adicione os parâmetros que a fachada expõe aqui) -> None:
                    error = {CamelCaseFeatureName}Error("Erro ao {acao_da_feature}!")
                    parameters = {CamelCaseFeatureName}Parameters(
                        # TODO: Mapear parâmetros da fachada para os parâmetros do UseCase
                        error=error,
                    )
                    usecase: {FeatureInitials}Usecase = {CamelCaseFeatureName}UseCase()
                    data: ReturnSuccessOrError[None] = usecase(parameters)

                    if isinstance(data, SuccessReturn):
                        return data.result
                    elif isinstance(data, ErrorReturn):
                        raise data.result
                    else:
                        raise ValueError("Unexpected return type from usecase")
            ```

        *   **Se `--type call_data`:**
            ```python
            from ...utils.parameters import {CamelCaseFeatureName}Parameters
            from ...utils.types import {FeatureInitials}Data, {FeatureInitials}Usecase
            from ...utils.erros import {CamelCaseFeatureName}Error
            from ..features.{snake_case_feature_name}.datasource.{snake_case_feature_name}_datasource import {CamelCaseFeatureName}Datasource
            from ..features.{snake_case_feature_name}.domain.usecase.{snake_case_feature_name}_usecase import {CamelCaseFeatureName}UseCase
            from py_return_success_or_error import ErrorReturn, SuccessReturn, ReturnSuccessOrError

            class FeaturesCompose:
                @staticmethod
                def {snake_case_feature_name}(# TODO: Adicione os parâmetros que a fachada expõe aqui) -> None:
                    error = {CamelCaseFeatureName}Error("Erro ao {acao_da_feature}!")
                    parameters = {CamelCaseFeatureName}Parameters(
                        # TODO: Mapear parâmetros da fachada para os parâmetros do UseCase
                        error=error,
                    )
                    datasource: {FeatureInitials}Data = {CamelCaseFeatureName}Datasource()
                    usecase: {FeatureInitials}Usecase = {CamelCaseFeatureName}UseCase(datasource)
                    data: ReturnSuccessOrError[None] = usecase(parameters)

                    if isinstance(data, SuccessReturn):
                        return data.result
                    elif isinstance(data, ErrorReturn):
                        raise data.result
                    else:
                        raise ValueError("Unexpected return type from usecase")
            ```

## Instruções para o Arquivo `pyproject.toml`

1.  **Ação:** Adicionar as seguintes seções de `[tool.poe.tasks]` ao `pyproject.toml` (ou integrá-las se já existirem).
2.  **Tasks:**
    *   `feature-base`: Para features derivadas de `UsecaseBase`.
        ```toml
        [tool.poe.tasks]
        "feature-base" = "python scripts/new_feature_script.py --type base"
        ```
    *   `feature-call-data`: Para features derivadas de `UsecaseBaseCallData`.
        ```toml
        [tool.poe.tasks]
        "feature-call-data" = "python scripts/new_feature_script.py --type call_data"
        ```