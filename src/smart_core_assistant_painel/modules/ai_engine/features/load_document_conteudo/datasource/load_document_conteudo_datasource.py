

from datetime import datetime

from langchain.docstore.document import Document

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentConteudoParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import LDCData


class LoadDocumentConteudoDatasource(LDCData):

    def __call__(
            self,
            parameters: LoadDocumentConteudoParameters) -> list[Document]:

        try:
            text_doc = [Document(
                page_content=parameters.conteudo,
                id=parameters.id,
                metadata={
                    "id_treinamento": parameters.id,
                    "tag": parameters.tag,
                    "grupo": parameters.grupo,
                    "source": "treinamento_ia",
                    "processed_at": datetime.now().isoformat(),
                }
            )]

            return text_doc
        except Exception as e:
            raise RuntimeError(
                f"Falha carregar o documento '{parameters.id}': {
                    str(e)}") from e
