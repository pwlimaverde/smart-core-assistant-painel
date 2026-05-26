"""Usecase para interpretação de mídia via LLM multimodal."""

from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
)

from smart_core_assistant_painel.modules.ai_engine.utils.erros import (
    InterpretMediaError,
)
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    InterpretMediaParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    IMUsecase,
    MediaAnalysis,
)


class InterpretMediaUseCase(IMUsecase):
    """Orquestra validações e interpretação de mídia.

    Valida que a mídia possui URL ou base64 válido antes
    de encaminhar ao datasource para processamento.
    """

    def __call__(
        self, parameters: InterpretMediaParameters
    ) -> ReturnSuccessOrError[MediaAnalysis]:
        """Executa validação e interpretação de mídia.

        Args:
            parameters: Parâmetros com dados da mídia.

        Returns:
            SuccessReturn com ``MediaAnalysis`` (analise + resumo) ou
            ErrorReturn em caso de falha.
        """
        has_url = bool(parameters.media_url and parameters.media_url.strip())
        has_base64 = bool(
            parameters.media_base64 and parameters.media_base64.strip()
        )

        if not has_url and not has_base64:
            return ErrorReturn(
                InterpretMediaError("URL ou base64 da mídia não fornecida.")
            )

        # Validar tipos de mídia suportados
        supported_types = {
            "imageMessage",
            "videoMessage",
            "documentMessage",
        }
        if parameters.media_type not in supported_types:
            return ErrorReturn(
                InterpretMediaError(
                    f"Tipo de mídia não suportado: {parameters.media_type}"
                )
            )

        return self._resultDatasource(
            parameters=parameters,
            datasource=self._datasource,
        )
