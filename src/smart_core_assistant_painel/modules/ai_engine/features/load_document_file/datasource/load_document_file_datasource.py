

from datetime import datetime
from pathlib import Path

from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
)

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    LoadDocumentFileParameters,
)
from smart_core_assistant_painel.modules.ai_engine.utils.types import LDFData


class LoadDocumentFileDatasource(LDFData):

    SUPPORTED_EXTENSIONS = {
        ".pdf": PyPDFLoader,
        ".doc": Docx2txtLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".xls": UnstructuredExcelLoader,
        ".csv": TextLoader,
    }

    def __call__(
            self,
            parameters: LoadDocumentFileParameters) -> list[Document]:

        try:
            ext = Path(parameters.path).suffix.lower()

            if ext not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(f"Extensão {ext} não suportada")

            loader_class = self.SUPPORTED_EXTENSIONS[ext]

            # Configura encoding UTF-8 para arquivos de texto e CSV
            if ext in ['.txt', '.csv']:
                loader = TextLoader(parameters.path, encoding="utf-8")
            else:
                loader = loader_class(parameters.path)
            documents = loader.load()

            for doc in documents:
                # parameters.context = doc.page_content
                doc.id = parameters.id
                doc.metadata.update({
                    "id_treinamento": str(parameters.id),
                    "tag": parameters.tag,
                    "grupo": parameters.grupo,
                    "source": "treinamento_ia",
                    "processed_at": datetime.now().isoformat(),
                })

            return documents
        except Exception as e:
            raise RuntimeError(
                f"Falha carregar o documento '{parameters.id}': {
                    str(e)}") from e
