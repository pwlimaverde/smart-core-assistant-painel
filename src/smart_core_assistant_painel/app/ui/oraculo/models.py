import json
import re
from typing import List

from django.core.exceptions import ValidationError
from django.db import models
from langchain.docstore.document import Document
from loguru import logger


def validate_tag(value):
    """
    Valida se a tag está em minúsculo, sem espaços e com no máximo 40 caracteres
    """
    if len(value) > 40:
        raise ValidationError('Tag deve ter no máximo 40 caracteres.')

    if ' ' in value:
        raise ValidationError('Tag não deve conter espaços.')

    if not value.islower():
        raise ValidationError('Tag deve conter apenas letras minúsculas.')

    # Opcional: validar se contém apenas letras, números e underscore
    if not re.match(r'^[a-z0-9_]+$', value):
        raise ValidationError(
            'Tag deve conter apenas letras minúsculas, números e underscore.')


class Treinamentos(models.Model):
    tag: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o treinamento")
    grupo: models.CharField = models.CharField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do treinamento")
    _documentos: models.JSONField = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Lista de documentos LangChain serializados (campo privado)",
        db_column='documentos'
    )
    treinamento_finalizado: models.BooleanField = models.BooleanField(
        default=False,)

    def save(self, *args, **kwargs):
        """
        Executa validação antes do salvamento
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validação personalizada do modelo
        """
        super().clean()

        # Validação customizada: tag não pode ser igual ao grupo
        if self.tag and self.grupo and self.tag == self.grupo:
            raise ValidationError({
                'grupo': 'O grupo não pode ser igual à tag.'
            })

    def __str__(self):
        return str(self.tag) if self.tag else f"Treinamento {self.id}"

    def get_conteudo_unificado(self):
        """
        Retorna todos os page_content da lista de documentos concatenados
        """
        todos_page_contents = []

        if self._documentos:
            # documentos é sempre uma lista (JSONField)
            documentos_lista = self._documentos

            for i, doc in enumerate(documentos_lista):

                # Se o documento é uma string JSON, faz o parse
                if isinstance(doc, str):
                    doc_parsed = json.loads(doc)
                else:
                    doc_parsed = doc

                # Extrai o page_content do documento parseado
                if isinstance(doc_parsed,
                              dict) and 'page_content' in doc_parsed:
                    page_content = doc_parsed['page_content']
                    todos_page_contents.append(page_content)

        # Concatena todos os conteúdos em uma única string
        resultado = '\n\n'.join(str(content)
                                for content in todos_page_contents if content)
        return resultado

    def set_documentos(self, documentos: List[Document]) -> None:
        """
        Define uma lista de documentos LangChain, serializando-os para JSON.

        Este método processa uma lista de objetos Document do LangChain e os
        serializa adequadamente para armazenamento no campo JSONField do modelo.

        Args:
            documentos: Lista de objetos Document do LangChain a serem armazenados

        Raises:
            TypeError: Se algum item da lista não for um objeto Document válido
            ValueError: Se houver erro na serialização dos dados

        Example:
            >>> from langchain.docstore.document import Document
            >>> docs = [
            ...     Document(page_content="Texto 1", metadata={"source": "doc1.txt"}),
            ...     Document(page_content="Texto 2", metadata={"source": "doc2.txt"})
            ... ]
            >>> treinamento.set_documentos(docs)
        """
        if not documentos:
            self._documentos = []
            return

        try:
            serialized_docs = []

            for i, documento in enumerate(documentos):
                if not isinstance(documento, Document):
                    error_msg = f"Item na posição {i} não é um Document válido: {
                        type(documento)}"
                    logger.error(error_msg)
                    raise TypeError(error_msg)

                try:
                    # Serializa o Document para dicionário
                    doc_dict = documento.model_dump_json(
                        indent=2)
                    serialized_docs.append(doc_dict)

                except Exception as e:
                    error_msg = f"Erro ao serializar documento na posição {i}: {e}"
                    logger.error(error_msg)
                    raise ValueError(error_msg) from e

            self._documentos = serialized_docs
            logger.info(
                f"Documentos serializados com sucesso: {
                    len(serialized_docs)} documentos")

        except (TypeError, ValueError):
            # Re-raise erros já tratados
            raise
        except Exception as e:
            error_msg = f"Erro inesperado ao processar documentos: {e}"
            logger.error(error_msg)
            self._documentos = []
            raise ValueError(error_msg) from e

    def get_documentos(self) -> List[Document]:
        """
        Processa e converte documentos JSON para objetos Document.

        Returns:
            List[Document]: Lista de documentos processados
        """
        documentos: list[Document] = []

        if not self._documentos:
            return documentos

        try:
            # documentos é sempre uma lista (JSONField)
            documentos_lista = self._documentos or []

            # Converte cada documento para objeto Document
            for doc_json in documentos_lista:
                if isinstance(doc_json, str):
                    # Se é string JSON, faz parse primeiro
                    documento = Document.model_validate_json(doc_json)
                else:
                    # Se já é dicionário, converte para Document
                    documento = Document(**doc_json)
                documentos.append(documento)

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(
                f"Erro ao processar documentos do treinamento {
                    self.pk or 'novo'}: {e}")

        return documentos

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
