from py_return_success_or_error import (
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    GenerateEmbeddingsParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import GEUsecase


class GenerateEmbeddingsUseCase(GEUsecase):
    """Use case para gerar embeddings de um texto.

    Esta classe orquestra o processo de geração de embeddings, delegando
    a interação com bibliotecas externas para o datasource e mantendo
    apenas a lógica de coordenação.
    """

    def __call__(
        self, parameters: GenerateEmbeddingsParameters
    ) -> ReturnSuccessOrError[list[float]]:
        """Executa o caso de uso de geração de embeddings.

        Args:
            parameters (GenerateEmbeddingsParameters): Os parâmetros necessários
                para gerar embeddings, incluindo o texto de entrada.

        Returns:
            ReturnSuccessOrError[list[float]]: Um objeto de retorno que
                contém o vetor de embeddings em caso de sucesso
                (SuccessReturn) ou um `AppError` em caso de falha
                (ErrorReturn).
        """
        return self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )
