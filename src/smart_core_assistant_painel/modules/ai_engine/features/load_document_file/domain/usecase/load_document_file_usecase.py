from datetime import datetime

from langchain.docstore.document import Document
from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.erros import DocumentError
from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentFileParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import LDFUsecase


class LoadDocumentFileUseCase(LDFUsecase):
    def __call__(
        self, parameters: LoadDocumentFileParameters
    ) -> ReturnSuccessOrError[list[Document]]:
        data = self._resultDatasource(
            parameters=parameters, datasource=self._datasource
        )

        if isinstance(data, SuccessReturn):
            documentos = data.result
            for doc in documentos:
                # parameters.context = doc.page_content
                doc.id = parameters.id
                doc.metadata.update(
                    {
                        "id_treinamento": str(parameters.id),
                        "tag": parameters.tag,
                        "grupo": parameters.grupo,
                        "source": "treinamento_ia",
                        "processed_at": datetime.now().isoformat(),
                    }
                )
            return SuccessReturn(documentos)
        else:
            return ErrorReturn(DocumentError("Erro ao obter dados do datasource."))
