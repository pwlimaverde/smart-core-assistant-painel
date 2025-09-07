"""Serviços para o aplicativo Treinamento."""

import os
import tempfile
from typing import Any

from langchain.docstore.document import Document
from loguru import logger

from smart_core_assistant_painel.modules.ai_engine import FeaturesCompose


class TreinamentoService:
    """Serviço para gerenciar operações de treinamento."""

    @staticmethod
    def aplicar_pre_analise_documentos(
        documentos: list[Document],
    ) -> list[Document]:
        """Aplica pré-análise de IA ao conteúdo de uma lista de documentos."""
        documentos_processados = []
        for documento in documentos:
            try:
                pre_analise_content = (
                    FeaturesCompose.pre_analise_ia_treinamento(
                        documento.page_content
                    )
                )
                documento.page_content = pre_analise_content
                documentos_processados.append(documento)
            except Exception as e:
                logger.error(f"Erro ao aplicar pré-análise no documento: {e}")
                documentos_processados.append(documento)
        return documentos_processados

    @staticmethod
    def processar_arquivo_upload(arquivo: Any) -> str | None:
        """Processa um arquivo enviado e retorna seu caminho temporário."""
        if not arquivo:
            return None
        try:
            return str(arquivo.temporary_file_path())
        except AttributeError:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(arquivo.name)[1]
            ) as temp_file:
                for chunk in arquivo.chunks():
                    temp_file.write(chunk)
                return str(temp_file.name)

    @staticmethod
    def processar_conteudo_texto(
        treinamento_id: int, conteudo: str, tag: str, grupo: str
    ) -> list[Document]:
        """Processa conteúdo de texto para treinamento."""
        if not conteudo:
            raise ValueError("Conteúdo não pode ser vazio")
        try:
            pre_analise_conteudo = FeaturesCompose.pre_analise_ia_treinamento(
                conteudo
            )
            return FeaturesCompose.load_document_conteudo(
                id=str(treinamento_id),
                conteudo=pre_analise_conteudo,
                tag=tag,
                grupo=grupo,
            )
        except Exception as e:
            logger.error(f"Erro ao processar conteúdo de texto: {e}")
            raise

    @staticmethod
    def processar_arquivo_documento(
        treinamento_id: int, documento_path: str, tag: str, grupo: str
    ) -> list[Document]:
        """Processa um arquivo de documento para treinamento."""
        if not documento_path:
            raise ValueError("Caminho do documento não pode ser vazio")
        try:
            data_file = FeaturesCompose.load_document_file(
                id=str(treinamento_id),
                path=documento_path,
                tag=tag,
                grupo=grupo,
            )
            return TreinamentoService.aplicar_pre_analise_documentos(data_file)
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de documento: {e}")
            raise

    @staticmethod
    def limpar_arquivo_temporario(arquivo_path: str | None) -> None:
        """Remove um arquivo temporário, se existir."""
        if arquivo_path and os.path.exists(arquivo_path):
            try:
                os.unlink(arquivo_path)
            except OSError:
                pass
