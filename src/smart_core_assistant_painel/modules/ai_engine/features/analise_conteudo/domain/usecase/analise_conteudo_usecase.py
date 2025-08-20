from py_return_success_or_error import (
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LlmParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import ACUsecase


class AnaliseConteudoUseCase(ACUsecase):
    """Use case para analisar um conteúdo usando um Large Language Model (LLM).

    Esta classe encapsula a lógica para enviar um conteúdo de texto para um
    datasource que interage com um LLM e retorna o resultado da análise.
    """

    def __call__(self, parameters: LlmParameters) -> ReturnSuccessOrError[str]:
        """Executa o caso de uso de análise de conteúdo.

        Args:
            parameters (LlmParameters): Os parâmetros necessários para a
                interação com o LLM, incluindo prompts e o contexto a ser
                analisado.

        Returns:
            ReturnSuccessOrError[str]: Um objeto de retorno que contém o
                resultado da análise como uma string em caso de sucesso
                (SuccessReturn) ou um `AppError` em caso de falha
                (ErrorReturn).
        """
        return self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )
