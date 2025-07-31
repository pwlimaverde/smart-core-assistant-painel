

from datetime import datetime

from langchain.docstore.document import Document
from py_return_success_or_error import (
    ErrorReturn,
    ReturnSuccessOrError,
    SuccessReturn,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentConteudoParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import LDCUsecase


class LoadDocumentConteudoUseCase(LDCUsecase):

    def __call__(
            self,
            parameters: LoadDocumentConteudoParameters) -> ReturnSuccessOrError[list[Document]]:
        try:
            text_doc = [Document(
                page_content=parameters.conteudo,
                id=parameters.id,
                metadata={
                        "id_treinamento": str(parameters.id),
                        "tag": parameters.tag,
                        "grupo": parameters.grupo,
                        "source": "treinamento_ia",
                        "processed_at": datetime.now().isoformat(),
                        }
            )]
            return SuccessReturn(text_doc)
        except Exception as e:
            error = parameters.error
            error.message = f'{error.message} - Exception: {str(e)}'
            return ErrorReturn(error)
