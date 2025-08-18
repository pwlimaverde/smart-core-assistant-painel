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
from smart_core_assistant_painel.modules.ai_engine.utils.types import (
    LDCUsecase,
)


class LoadDocumentConteudoUseCase(LDCUsecase):
    """Use case para carregar um conteúdo de texto em um objeto Document.

    Este caso de uso não possui um datasource, pois opera diretamente em
    memória. Ele recebe uma string de conteúdo e a transforma em um
    objeto `langchain.docstore.document.Document`, enriquecendo-o com
    metadados.
    """

    def __call__(
        self, parameters: LoadDocumentConteudoParameters
    ) -> ReturnSuccessOrError[list[Document]]:
        """Executa o caso de uso de carregamento de conteúdo.

        Args:
            parameters (LoadDocumentConteudoParameters): Parâmetros contendo o
                ID, conteúdo, tag e grupo para criar o documento.

        Returns:
            ReturnSuccessOrError[list[Document]]: Um objeto de retorno
                contendo uma lista com o documento criado em caso de sucesso
                (SuccessReturn), ou um AppError em caso de falha
                (ErrorReturn).
        """
        try:
            text_doc = [
                Document(
                    page_content=parameters.conteudo,
                    id=parameters.id,
                    metadata={
                        "id_treinamento": str(parameters.id),
                        "tag": parameters.tag,
                        "grupo": parameters.grupo,
                        "source": "treinamento_ia",
                        "processed_at": datetime.now().isoformat(),
                    },
                )
            ]
            return SuccessReturn(text_doc)
        except Exception as e:
            error = parameters.error
            error.message = f"{error.message} - Exception: {str(e)}"
            return ErrorReturn(error)
