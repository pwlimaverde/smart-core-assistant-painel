# Metodologia para Criação de Novas Features

Este documento descreve a metodologia e o padrão arquitetural para a criação de novas features no sistema Smart Core Assistant. Aderir a este padrão é crucial para manter a consistência, manutenibilidade e escalabilidade do código.

## 1. Visão Geral da Arquitetura

O projeto adota uma arquitetura limpa (Clean Architecture), que separa as responsabilidades em camadas distintas. A comunicação entre as camadas é feita através de contratos bem definidos, utilizando a biblioteca `py-return-success-or-error` para garantir um fluxo de dados e erros previsível.

As principais pastas envolvidas na criação de uma feature são:

-   `src/smart_core_assistant_painel/modules/`: Contém os grandes domínios da aplicação (ex: `ai_engine`, `services`).
-   `.../features/`: Dentro de cada módulo, agrupa as features específicas daquele domínio.
-   `.../features/nome_da_feature/`: Cada feature possui seu próprio diretório.
-   `.../domain/usecase/`: Contém o **Use Case**, o coração da feature.
-   `.../datasource/`: Contém o **Datasource**, a implementação de acesso a dados/APIs.
-   `.../utils/`: Dentro de cada módulo, a pasta `utils` centraliza definições compartilhadas:
    -   `erros.py`: Define exceções customizadas, que **devem** herdar de `AppError`.
    -   `parameters.py`: Define as classes de parâmetros de entrada, que **devem** herdar de `ParametersReturnResult`.
    -   `types.py`: Define os "contratos" para UseCases e Datasources usando `TypeAlias`.
-   `.../features/features_compose.py`: Atua como uma **Facade**, expondo as features do módulo.

## 2. Passo a Passo para Criar uma Nova Feature

Vamos criar uma feature `gerar_relatorio` no módulo `services`.

### Passo 1: Criar a Estrutura de Diretórios

```bash
mkdir -p src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/domain/usecase
mkdir -p src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/datasource
# ... criar arquivos __init__.py ...
```

### Passo 2: Definir Erros, Parâmetros e Tipos na pasta `utils`

Este é o passo mais crítico para garantir o acoplamento correto com a arquitetura.

1.  **Erro Específico** (em `utils/erros.py`):
    O erro customizado **deve** herdar de `AppError`.

    ```python
    # src/smart_core_assistant_painel/modules/services/utils/erros.py
    from dataclasses import dataclass
    from py_return_success_or_error import AppError
    ...

    @dataclass
    class RelatorioError(AppError):
        message: str

        def __str__(self) -> str:
            return f"RelatorioError - {self.message}"
    ```

2.  **Parâmetros de Entrada** (em `utils/parameters.py`):
    A classe de parâmetros **deve** herdar de `ParametersReturnResult`.

    ```python
    # src/smart_core_assistant_painel/modules/services/utils/parameters.py
    from dataclasses import dataclass
    from py_return_success_or_error import AppError, ParametersReturnResult
    from .erros import RelatorioError
    ...

    @dataclass
    class GerarRelatorioParameters(ParametersReturnResult):
        id_usuario: str
        formato: str
        error: type[AppError] = RelatorioError
    ```

3.  **Tipos do Use Case e Datasource** (em `utils/types.py`):
    Defina os contratos usando `TypeAlias` e os tipos genéricos da biblioteca.

    -   `Datasource[ReturnType, ParametersType]`: Contrato para um datasource.
    -   `UsecaseBaseCallData[SuccessType, DatasourceReturnType, ParametersType]`: Contrato para um use case que chama um datasource.
    -   `UsecaseBase[SuccessType, ParametersType]`: Contrato para um use case sem dependência de datasource.

    ```python
    # src/smart_core_assistant_painel/modules/services/utils/types.py
    from typing import TypeAlias
    from py_return_success_or_error import Datasource, UsecaseBaseCallData
    from .parameters import GerarRelatorioParameters
    ...

    GRData: TypeAlias = Datasource[str, GerarRelatorioParameters]
    GRUsecase: TypeAlias = UsecaseBaseCallData[str, str, GerarRelatorioParameters]
    ```

### Passo 3: Implementar o Datasource

A classe do datasource deve herdar do `TypeAlias` que criamos (`GRData`).

```python
# src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/datasource/gerar_relatorio_datasource.py
from ..utils.parameters import GerarRelatorioParameters
from ..utils.types import GRData

class GerarRelatorioDatasource(GRData):
    def __call__(self, parameters: GerarRelatorioParameters) -> str:
        # ... implementação ...
```

### Passo 4: Implementar o Use Case

O use case herda do seu respectivo `TypeAlias` (`GRUsecase`). A herança de `UsecaseBaseCallData` fornece o método `_resultDatasource` para uma chamada segura ao datasource.

```python
# src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/domain/usecase/gerar_relatorio_usecase.py
from py_return_success_or_error import ErrorReturn, ReturnSuccessOrError, SuccessReturn
from ..utils.parameters import GerarRelatorioParameters
from ..utils.types import GRUsecase

class GerarRelatorioUseCase(GRUsecase):
    def __call__(self, parameters: GerarRelatorioParameters) -> ReturnSuccessOrError[str]:
        if parameters.formato not in ["pdf", "csv"]:
            return ErrorReturn(ValueError("Formato de relatório não suportado"))

        data = self._resultDatasource(parameters=parameters, datasource=self._datasource)

        if isinstance(data, SuccessReturn):
            caminho_arquivo = data.result
            return SuccessReturn(f"Relatório gerado com sucesso em: {caminho_arquivo}")
        elif isinstance(data, ErrorReturn):
            return ErrorReturn(parameters.error(message=f"Erro ao gerar relatório: {data.result}"))
        else:
            return ErrorReturn(parameters.error(message="Tipo de retorno inesperado do datasource."))
```

### Passo 5: Expor a Feature no `features_compose.py`

Adicione um método estático na fachada do módulo.

```python
# src/smart_core_assistant_painel/modules/services/features/features_compose.py
from .features.gerar_relatorio.datasource.gerar_relatorio_datasource import GerarRelatorioDatasource
from .features.gerar_relatorio.domain.usecase.gerar_relatorio_usecase import GerarRelatorioUseCase
from .utils.parameters import GerarRelatorioParameters
from .utils.types import GRData, GRUsecase
# ...

class FeaturesCompose:
    @staticmethod
    def gerar_relatorio_usuario(id_usuario: str, formato: str) -> str:
        parameters = GerarRelatorioParameters(id_usuario=id_usuario, formato=formato)
        datasource: GRData = GerarRelatorioDatasource()
        usecase: GRUsecase = GerarRelatorioUseCase(datasource)
        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            return data.result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Tipo de retorno inesperado do usecase")

```

## 3. Testando a Nova Feature

Os testes devem residir na pasta `tests/` na raiz, espelhando a estrutura do código-fonte.

```python
# tests/modules/services/features/gerar_relatorio/test_gerar_relatorio_usecase.py
import unittest
from unittest.mock import MagicMock
from py_return_success_or_error import SuccessReturn
# ...

class TestGerarRelatorioUseCase(unittest.TestCase):
    def test_gerar_relatorio_success(self) -> None:
        mock_datasource = MagicMock()
        mock_datasource.return_value = SuccessReturn("/tmp/relatorio_teste.pdf")
        usecase = GerarRelatorioUseCase(datasource=mock_datasource)
        parameters = GerarRelatorioParameters(id_usuario="teste", formato="pdf")

        result = usecase(parameters)

        self.assertIsInstance(result, SuccessReturn)
        self.assertEqual(result.result, "Relatório gerado com sucesso em: /tmp/relatorio_teste.pdf")
```
