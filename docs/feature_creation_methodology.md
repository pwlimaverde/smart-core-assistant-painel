# Metodologia para Criação de Novas Features

Este documento descreve a metodologia e o padrão arquitetural para a criação de novas features no sistema Smart Core Assistant. Aderir a este padrão é crucial para manter a consistência, manutenibilidade e escalabilidade do código.

## 1. Visão Geral da Arquitetura

O projeto adota uma arquitetura limpa (Clean Architecture), que separa as responsabilidades em camadas distintas. Isso garante que a lógica de negócio (core da feature) seja independente de detalhes de implementação como banco de dados, frameworks ou APIs externas.

As principais pastas envolvidas na criação de uma feature são:

-   `src/smart_core_assistant_painel/modules/`: Contém os grandes domínios da aplicação (ex: `ai_engine`, `services`). Cada módulo é uma unidade coesa de funcionalidade.
-   `.../features/`: Dentro de cada módulo, esta pasta agrupa as features específicas daquele domínio.
-   `.../features/nome_da_feature/`: Cada feature possui seu próprio diretório, contendo sua lógica de negócio e implementações de acesso a dados.
-   `.../features/nome_da_feature/domain/usecase/`: Contém o **Use Case**, que é o coração da feature. Ele orquestra o fluxo, executa a lógica de negócio e não conhece detalhes de implementação externos.
-   `.../features/nome_da_feature/datasource/`: Contém o **Datasource**, que é a implementação concreta das interfaces requeridas pelo Use Case para interagir com o mundo exterior (ex: acessar um banco de dados, uma API, ou o sistema de arquivos).
-   `.../features/features_compose.py`: Atua como uma **fachada (Facade)** para o módulo. Ele expõe as features de forma simples e coesa para o resto da aplicação, abstraindo a complexidade interna de instanciação de use cases e datasources.

## 2. Passo a Passo para Criar uma Nova Feature

Vamos seguir um exemplo prático para criar uma feature chamada `gerar_relatorio` dentro do módulo `services`.

### Passo 1: Criar a Estrutura de Diretórios

Primeiro, crie a estrutura de pastas para a nova feature. Todos os diretórios devem conter um arquivo `__init__.py` para serem reconhecidos como pacotes Python.

```bash
mkdir -p src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/domain/usecase
mkdir -p src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/datasource

touch src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/__init__.py
touch src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/domain/__init__.py
touch src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/domain/usecase/__init__.py
touch src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/datasource/__init__.py
```

### Passo 2: Definir Tipos, Parâmetros e Erros

Antes de implementar, defina os "contratos" da feature.

1.  **Tipo do Use Case e Datasource** (em `.../utils/types.py`):
    Adicione os type aliases para o novo use case e datasource. Isso facilita a manutenção e a legibilidade.

    ```python
    # src/smart_core_assistant_painel/modules/services/utils/types.py
    ...
    from smart_core_assistant_painel.modules.services.features.gerar_relatorio.domain.usecase.gerar_relatorio_usecase import GerarRelatorioUseCase
    from smart_core_assistant_painel.modules.services.features.gerar_relatorio.datasource.gerar_relatorio_datasource import GerarRelatorioDatasource

    GRUsecase = GerarRelatorioUseCase
    GRData = GerarRelatorioDatasource
    ```

2.  **Parâmetros de Entrada** (em `.../utils/parameters.py`):
    Crie uma classe `dataclass` para agrupar os parâmetros de entrada do use case.

    ```python
    # src/smart_core_assistant_painel/modules/services/utils/parameters.py
    from dataclasses import dataclass
    ...

    @dataclass
    class GerarRelatorioParameters:
        id_usuario: str
        formato: str  # "pdf", "csv", etc.
        error: Exception
    ```

3.  **Erro Específico** (em `.../utils/erros.py`):
    Crie uma classe de exceção customizada para a feature.

    ```python
    # src/smart_core_assistant_painel/modules/services/utils/erros.py
    ...
    class RelatorioError(Exception):
        pass
    ```

### Passo 3: Implementar o Datasource

O Datasource implementa a lógica de acesso a dados. Ele não contém regras de negócio.

```python
# src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/datasource/gerar_relatorio_datasource.py

from smart_core_assistant_painel.modules.services.utils.parameters import GerarRelatorioParameters
from smart_core_assistant_painel.modules.services.utils.types import GRData

class GerarRelatorioDatasource(GRData):
    def __call__(self, parameters: GerarRelatorioParameters) -> str:
        """
        Simula a geração de um relatório e retorna o caminho do arquivo.
        """
        try:
            # Lógica real de geração de arquivo (ex: usando pandas, reportlab)
            print(f"Gerando relatório para {parameters.id_usuario} em formato {parameters.formato}...")
            caminho_arquivo = f"/tmp/relatorio_{parameters.id_usuario}.{parameters.formato}"
            with open(caminho_arquivo, "w") as f:
                f.write("Conteúdo do relatório")
            return caminho_arquivo
        except Exception as e:
            raise RuntimeError(f"Falha ao gerar o arquivo de relatório: {e}") from e

```

### Passo 4: Implementar o Use Case

O Use Case contém a lógica de negócio e orquestra o datasource. Ele utiliza a biblioteca `py-return-success-or-error` para retornar o resultado.

```python
# src/smart_core_assistant_painel/modules/services/features/gerar_relatorio/domain/usecase/gerar_relatorio_usecase.py

from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)
from smart_core_assistant_painel.modules.services.utils.parameters import GerarRelatorioParameters
from smart_core_assistant_painel.modules.services.utils.types import GRUsecase

class GerarRelatorioUseCase(GRUsecase):
    def __call__(self, parameters: GerarRelatorioParameters) -> ReturnSuccessOrError[str]:
        """
        Orquestra a geração do relatório.
        """
        try:
            # Validações de negócio
            if parameters.formato not in ["pdf", "csv"]:
                return ErrorReturn(ValueError("Formato de relatório não suportado"))

            # Chama o datasource para executar a ação
            caminho_arquivo = self._datasource(parameters)

            # Retorna o resultado com sucesso
            return SuccessReturn(f"Relatório gerado com sucesso em: {caminho_arquivo}")

        except Exception as e:
            # Retorna um erro em caso de falha
            return ErrorReturn(parameters.error(f"Erro no caso de uso de geração de relatório: {e}"))
```

### Passo 5: Expor a Feature no `features_compose.py`

Agora, integre a nova feature na fachada do módulo para que ela seja acessível por outras partes do sistema.

```python
# src/smart_core_assistant_painel/modules/services/features/features_compose.py
...
# Importações da nova feature
from smart_core_assistant_painel.modules.services.features.gerar_relatorio.datasource.gerar_relatorio_datasource import GerarRelatorioDatasource
from smart_core_assistant_painel.modules.services.features.gerar_relatorio.domain.usecase.gerar_relatorio_usecase import GerarRelatorioUseCase
from smart_core_assistant_painel.modules.services.utils.erros import RelatorioError
from smart_core_assistant_painel.modules.services.utils.parameters import GerarRelatorioParameters
from smart_core_assistant_painel.modules.services.utils.types import GRData, GRUsecase
...

class FeaturesCompose:
    ...
    @staticmethod
    def gerar_relatorio_usuario(id_usuario: str, formato: str) -> str:
        """
        Gera um relatório para um usuário específico.
        """
        error = RelatorioError("Erro ao gerar relatório!")
        parameters = GerarRelatorioParameters(
            id_usuario=id_usuario,
            formato=formato,
            error=error,
        )

        datasource: GRData = GerarRelatorioDatasource()
        usecase: GRUsecase = GerarRelatorioUseCase(datasource)

        data = usecase(parameters)

        if isinstance(data, SuccessReturn):
            result: str = data.result
            return result
        elif isinstance(data, ErrorReturn):
            raise data.result
        else:
            raise ValueError("Tipo de retorno inesperado do usecase")

```

## 3. Testando a Nova Feature

Os testes são fundamentais para garantir a qualidade. Para cada feature de lógica de negócio, o teste deve residir no diretório `tests/` na raiz do projeto, espelhando a estrutura do código-fonte.

### Estrutura de Testes

Crie o arquivo de teste:

```bash
mkdir -p tests/modules/services/features/gerar_relatorio/
touch tests/modules/services/features/gerar_relatorio/__init__.py
touch tests/modules/services/features/gerar_relatorio/test_gerar_relatorio_usecase.py
```

### Exemplo de Teste de Use Case

No teste do use case, o datasource deve ser "mocado" (mocked) para que o teste seja focado puramente na lógica de negócio do use case, sem depender de sistemas externos.

```python
# tests/modules/services/features/gerar_relatorio/test_gerar_relatorio_usecase.py

import unittest
from unittest.mock import MagicMock

from py_return_success_or_error import SuccessReturn, ErrorReturn

from smart_core_assistant_painel.modules.services.features.gerar_relatorio.domain.usecase.gerar_relatorio_usecase import GerarRelatorioUseCase
from smart_core_assistant_painel.modules.services.utils.parameters import GerarRelatorioParameters
from smart_core_assistant_painel.modules.services.utils.erros import RelatorioError

class TestGerarRelatorioUseCase(unittest.TestCase):

    def test_gerar_relatorio_success(self) -> None:
        """
        Testa o caso de sucesso da geração de relatório.
        """
        # Arrange
        mock_datasource = MagicMock()
        mock_datasource.return_value = "/tmp/relatorio_teste.pdf"

        usecase = GerarRelatorioUseCase(datasource=mock_datasource)
        parameters = GerarRelatorioParameters(
            id_usuario="usuario_teste",
            formato="pdf",
            error=RelatorioError
        )

        # Act
        result = usecase(parameters)

        # Assert
        self.assertIsInstance(result, SuccessReturn)
        self.assertEqual(result.result, "Relatório gerado com sucesso em: /tmp/relatorio_teste.pdf")
        mock_datasource.assert_called_once_with(parameters)

    def test_gerar_relatorio_unsupported_format(self) -> None:
        """
        Testa a falha ao usar um formato não suportado.
        """
        # Arrange
        mock_datasource = MagicMock()
        usecase = GerarRelatorioUseCase(datasource=mock_datasource)
        parameters = GerarRelatorioParameters(
            id_usuario="usuario_teste",
            formato="docx",
            error=RelatorioError
        )

        # Act
        result = usecase(parameters)

        # Assert
        self.assertIsInstance(result, ErrorReturn)
        self.assertIsInstance(result.result, ValueError)
        self.assertEqual(str(result.result), "Formato de relatório não suportado")
        mock_datasource.assert_not_called()

    def test_gerar_relatorio_datasource_error(self) -> None:
        """
        Testa o tratamento de erro vindo do datasource.
        """
        # Arrange
        mock_datasource = MagicMock()
        mock_datasource.side_effect = RuntimeError("Falha de I/O")

        usecase = GerarRelatorioUseCase(datasource=mock_datasource)
        parameters = GerarRelatorioParameters(
            id_usuario="usuario_teste",
            formato="csv",
            error=RelatorioError
        )

        # Act
        result = usecase(parameters)

        # Assert
        self.assertIsInstance(result, ErrorReturn)
        self.assertIsInstance(result.result, RelatorioError)

```

## 4. Conclusão

Seguir esta metodologia garante que:
- O código seja fracamente acoplado e altamente coeso.
- A lógica de negócio seja testável de forma isolada.
- As features sejam fáceis de encontrar, manter e estender.
- A complexidade seja gerenciada de forma eficaz, permitindo que o projeto cresça de maneira sustentável.
