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
    """Use case para carregar um arquivo e prepará-lo para treinamento.

    Esta classe orquestra o processo de carregar um arquivo de um caminho,
    processar seu conteúdo e enriquecer seus metadados para uso futuro em
    treinamentos de IA.
    """

    def __call__(
        self, parameters: LoadDocumentFileParameters
    ) -> ReturnSuccessOrError[list[Document]]:
        """Executa o caso de uso.

        Args:
            parameters (LoadDocumentFileParameters): Os parâmetros necessários
                para carregar o arquivo, incluindo id, caminho, tags e grupo.

        Returns:
            ReturnSuccessOrError[list[Document]]: Um objeto de retorno que
                contém uma lista de `Document` em caso de sucesso
                (SuccessReturn) ou um `AppError` em caso de falha
                (ErrorReturn).
        """
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
            return ErrorReturn(
                parameters.error(message="Erro ao obter dados do datasource.")
            )
