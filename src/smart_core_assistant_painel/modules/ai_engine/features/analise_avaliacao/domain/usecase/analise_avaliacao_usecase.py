import math

from py_return_success_or_error import (
    ErrorReturn,
    SuccessReturn,
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    AnaliseAvaliacaoParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    AAUsecase,
    AnaliseAvaliacao,
)


class AnaliseAvaliacaoUsecase(AAUsecase):
    """Use case para realizar a análise de avaliação de atendimento."""

    def __call__(
        self, parameters: AnaliseAvaliacaoParameters
    ) -> ReturnSuccessOrError[AnaliseAvaliacao]:
        try:
            # Chama o datasource (LLM)
            result_data = self._resultDatasource(
                parameters=parameters, datasource=self._datasource
            )

            if isinstance(result_data, ErrorReturn):
                return result_data

            if isinstance(result_data, SuccessReturn):
                avaliacao: AnaliseAvaliacao = result_data.result

                # Lógica de Normalização
                raw_nota = avaliacao.nota

                # Se nota <= 5: Mantém
                if raw_nota <= 5:
                    final_nota = raw_nota
                # Se nota entre 6 e 10: floor(nota / 2)
                elif 6 <= raw_nota <= 10:
                    final_nota = math.floor(raw_nota / 2)
                # Se nota > 10: Define como 5 (máximo assumido para escala estourada que expressa satisfação total)
                else:
                    final_nota = 5

                # Garante que não seja menor que 1 (se veio 0 ou negativo)
                if final_nota < 1:
                    final_nota = 1

                avaliacao.nota = final_nota

                return SuccessReturn(success=avaliacao)

            return ErrorReturn(parameters.error)

        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)
