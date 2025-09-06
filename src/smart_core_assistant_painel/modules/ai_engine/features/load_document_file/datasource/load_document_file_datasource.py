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
    """Datasource para carregar documentos de diferentes formatos de arquivo.

    Utiliza a biblioteca Langchain para carregar arquivos .pdf, .docx, .txt,
    .xlsx, .xls e .csv, convertendo-os em uma lista de objetos Document.
    """

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
        self, parameters: LoadDocumentFileParameters
    ) -> list[Document]:
        """Carrega um arquivo do caminho especificado nos parâmetros.

        Args:
            parameters (LoadDocumentFileParameters): Os parâmetros contendo
                o caminho do arquivo (`path`) e seu id.

        Returns:
            list[Document]: Uma lista de objetos `Document` contendo o
                conteúdo do arquivo.

        Raises:
            ValueError: Se a extensão do arquivo não for suportada.
            RuntimeError: Se ocorrer qualquer outro erro durante o
                carregamento do arquivo.
        """
        try:
            ext = Path(parameters.path).suffix.lower()

            if ext not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(f"Extensão {ext} não suportada")

            loader_class = self.SUPPORTED_EXTENSIONS[ext]

            # Configura encoding UTF-8 para arquivos de texto e CSV
            if ext in [".txt", ".csv"]:
                loader = TextLoader(parameters.path, encoding="utf-8")
            else:
                loader = loader_class(parameters.path)
            documents = loader.load()

            return documents
        except Exception as e:
            raise RuntimeError(
                f"Falha carregar o documento '{parameters.id}': {str(e)}"
            ) from e
