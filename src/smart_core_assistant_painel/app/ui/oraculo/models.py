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
    tag: models.TextField = models.TextField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o treinamento")
    grupo: models.TextField = models.TextField(
        max_length=40,
        validators=[validate_tag],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do treinamento")
    documentos: models.JSONField = models.JSONField(
        default=list, blank=True, null=True)
    treinamento_finalizado: models.BooleanField = models.BooleanField(
        default=False,)

    def save(self, *args, **kwargs):
        """
        Executa validação OBRIGATÓRIA antes de qualquer salvamento
        """
        # Valida o campo tag especificamente
        if self.tag:
            validate_tag(self.tag)

        # Executa todas as validações do modelo
        self.full_clean()

        # Só salva se passou em todas as validações
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validação adicional no nível do modelo
        """
        super().clean()
        if self.tag:
            validate_tag(self.tag)

    def __str__(self):
        return str(self.tag) if self.tag else f"Treinamento {self.id}"

    def get_conteudo_unificado(self):
        """
        Retorna todos os page_content da lista de documentos concatenados
        """
        todos_page_contents = []

        if self.documentos:
            # Se documentos é uma string, faz parse primeiro
            if isinstance(self.documentos, str):

                documentos_lista = json.loads(self.documentos)

            else:
                documentos_lista = self.documentos

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

    def processar_documentos(self) -> List[Document]:
        """
        Processa e converte documentos JSON para objetos Document.

        Returns:
            List[Document]: Lista de documentos processados
        """
        documentos: list[Document] = []

        if not self.documentos:
            return documentos

        try:
            # Se é uma string, faz parse primeiro
            if isinstance(self.documentos, str):
                documentos_lista = json.loads(self.documentos)
            else:
                documentos_lista = self.documentos

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
