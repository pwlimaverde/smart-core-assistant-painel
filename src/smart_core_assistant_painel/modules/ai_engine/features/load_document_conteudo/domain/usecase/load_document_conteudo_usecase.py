
import json

from loguru import logger
from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.erros import DocumentError
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentConteudoParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import LDCUsecase


class LoadDocumentConteudoUseCase(LDCUsecase):

    def __call__(
            self,
            parameters: LoadDocumentConteudoParameters) -> ReturnSuccessOrError[str]:

        documentos = self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )

        if isinstance(documentos, SuccessReturn):
            completo_json = json.dumps([documento.model_dump_json(
                indent=2) for documento in documentos.result], ensure_ascii=False)
            logger.warning(
                f"Processando completo_json: {completo_json}"
            )
            return SuccessReturn(completo_json)
        else:
            return ErrorReturn(
                DocumentError('Erro ao obter dados do datasource.'))
