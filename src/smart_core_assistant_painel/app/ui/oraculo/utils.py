import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import find_dotenv, load_dotenv
from groq import Groq
from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
)

from smart_core_assistant_painel.app.features.features_compose import FeaturesCompose

load_dotenv(find_dotenv())
client = Groq()


class DocumentProcessor:
    """Processador universal para diferentes tipos de documentos"""

    SUPPORTED_EXTENSIONS = {
        ".pdf": PyPDFLoader,
        ".doc": Docx2txtLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".xls": UnstructuredExcelLoader,
        ".csv": TextLoader,
    }

    @classmethod
    def load_document(
        cls,
        id: str,
        path: Optional[str],
        tag: str,
        grupo: str,
        conteudo: Optional[str],
    ) -> str:

        try:
            todos_documentos: List[Document] = []

            if conteudo:
                # parameters.context = conteudo
                pre_analise = FeaturesCompose.pre_analise_ia_treinamento(
                    conteudo)
                text_doc = Document(
                    page_content=pre_analise,
                )

                todos_documentos.append(text_doc)

            if path:
                ext = Path(path).suffix.lower()

                if ext not in cls.SUPPORTED_EXTENSIONS:
                    raise ValueError(f"Extensão {ext} não suportada")

                loader_class = cls.SUPPORTED_EXTENSIONS[ext]
                loader = loader_class(path)
                documents = loader.load()

                for doc in documents:
                    # parameters.context = doc.page_content
                    pre_analise = FeaturesCompose.pre_analise_ia_treinamento(
                        doc.page_content)
                    doc.page_content = pre_analise

                todos_documentos.extend(documents)

            conteudo_completo = "\n\n".join(
                [doc.page_content for doc in todos_documentos])

            completo_doc = Document(
                id=id,
                page_content=conteudo_completo,
                metadata={
                    "id_treinamento": id,
                    "tag": tag,
                    "grupo": grupo,
                    "source": "treinamento_ia",
                    "processed_at": datetime.now().isoformat(),
                }
            )

            completo_json = completo_doc.model_dump_json(indent=2)

            return completo_json
        except Exception as e:
            raise RuntimeError(
                f"Falha carregar o documento '{id}': {
                    str(e)}") from e


def gerar_documentos(
    id: str,
    path: Optional[str],
    tag: str,
    grupo: str,
    conteudo: Optional[str],
) -> str:
    """
    Gerar documentos RAG a partir de múltiplas fontes

    Args:
        id: Identificador único do documento
        path: Caminho para arquivo (opcional)
        tag: Tag de classificação
        conteudo: Conteúdo direto (opcional)

    Returns:
        str: Resultado do processamento

    Raises:
        ValueError: Quando nem path nem conteudo são fornecidos
        DocumentProcessingError: Quando há erro no processamento
    """
    # Validação de entrada
    if not (path or conteudo):
        raise ValueError(
            "É obrigatório fornecer pelo menos um dos parâmetros: 'path' ou 'conteudo'"
        )

    try:
        treinamento = DocumentProcessor.load_document(
            id=id,
            path=path,
            tag=tag,
            grupo=grupo,
            conteudo=conteudo
        )
        logging.info(f"treinamento {treinamento}")
        return treinamento

    except Exception as e:
        raise RuntimeError(
            f"Falha no processamento do documento '{id}': {
                str(e)}") from e
