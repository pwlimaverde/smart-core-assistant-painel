"""Use case para transcrição de áudio."""

from py_return_success_or_error import ErrorReturn, ReturnSuccessOrError

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    TranscribeAudioParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import TAUsecase


class TranscribeAudioUseCase(TAUsecase):
    """Orquestra validações e execução da transcrição de áudio."""

    def __call__(
        self, parameters: TranscribeAudioParameters
    ) -> ReturnSuccessOrError[str]:
        has_url = bool(parameters.audio_url and parameters.audio_url.strip())
        has_base64 = bool(
            parameters.audio_base64 and parameters.audio_base64.strip()
        )

        if not has_url and not has_base64:
            return ErrorReturn(
                parameters.error.__class__(
                    "URL ou base64 do áudio não fornecida."
                )
            )

        if has_url and not parameters.audio_url.startswith(
            ("http://", "https://")
        ):
            return ErrorReturn(
                parameters.error.__class__(
                    "URL do áudio inválida. Use http:// ou https://."
                )
            )

        return self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )
