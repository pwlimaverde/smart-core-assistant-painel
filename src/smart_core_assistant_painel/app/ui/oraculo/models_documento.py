from datetime import datetime
from typing import Any, Self, cast, override

from django.db import models
from django.db.models.indexes import Index
from django.db.models.query import QuerySet
from langchain_core.documents.base import Document
from loguru import logger
from pgvector.django import CosineDistance, VectorField

from .models_treinamento import Treinamento


class Documento(models.Model):
    """
    Modelo que representa um documento vetorizado individual.

    Cada instância armazena um chunk de conteúdo de treinamento
    com seu respectivo embedding vetorial para busca semântica.

    Attributes:
        treinamento: Relacionamento com o modelo Treinamento
        conteudo: Conteúdo do chunk de treinamento
        metadata: Metadados do documento (tag, grupo, source, etc.)
        embedding: Vetor de embeddings do conteúdo (1024 dimensões)
        ordem: Ordem do documento no treinamento
        data_criacao: Timestamp de criação
    """

    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )

    treinamento: models.ForeignKey[Treinamento] = models.ForeignKey(
        Treinamento,
        on_delete=models.CASCADE,
        related_name="documentos",
        help_text="Treinamento ao qual este documento pertence",
    )

    conteudo: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Conteúdo do chunk de treinamento",
    )

    metadata: models.JSONField[dict[str, Any] | None] = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados do documento (tag, grupo, source, etc.)",
    )

    embedding: VectorField = VectorField(
        dimensions=1024,
        null=True,
        blank=True,
        help_text="Vetor de embeddings do conteúdo do documento",
    )

    ordem: models.PositiveIntegerField[int] = models.PositiveIntegerField(
        default=1,
        help_text="Ordem do documento no treinamento",
    )

    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do documento",
    )

    class Meta:
        verbose_name: str = "Documento"
        verbose_name_plural: str = "Documentos"
        ordering: list[str] = ["treinamento", "ordem"]
        indexes: list[Index] = [
            models.Index(fields=["treinamento", "ordem"]),
        ]

    @override
    def __str__(self) -> str:
        return f"Documento {self.id}"

    @classmethod
    def buscar_documentos_similares(
        cls,
        query_vec: list[float],
        top_k: int = 5,
    ) -> str:
        """Busca documentos relacionados à mensagem recebida pelo webhook.

        Args:
            mensagem: Texto da mensagem recebida
            top_k: Número de documentos a retornar

        Returns:
            Contexto formatado com os documentos mais relevantes
        """
        try:
            # Busca documentos similares
            documentos: QuerySet[Self] = (
                cls.objects.filter(
                    treinamento__treinamento_finalizado=True,
                    embedding__isnull=False,
                )
                .annotate(distance=CosineDistance("embedding", query_vec))
                .order_by("distance")[:top_k]
            )

            # Formata contexto
            if not documentos:
                return ""

            contexto_lines: list[str] = ["📚 Contexto relevante:"]
            for i, doc in enumerate(documentos, 1):
                if doc.conteudo:
                    contexto_lines.extend(
                        [
                            f"\n[{i}] {doc.treinamento.tag} - {doc.treinamento.grupo}",
                            doc.conteudo.strip(),
                            "---",
                        ]
                    )

            return "\n".join(contexto_lines)

        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return ""

    @classmethod
    def limpar_documentos_por_treinamento(cls, treinamento_id: int) -> None:
        """Remove todos os documentos de um treinamento."""
        docs = cls.objects.filter(treinamento_id=treinamento_id).delete()
        logger.info(
            f"Removidos {docs} documentos do treinamento {treinamento_id}"
        )

    @classmethod
    def criar_documentos_de_chunks(
        cls,
        chunks: list[Document],
        treinamento_id: int
    ) -> list['Documento']:
        """Cria documentos a partir de uma lista de chunks e o ID do treinamento.
        
        Args:
            chunks: lista de objetos Document (chunks) do LangChain
            treinamento_id: ID do treinamento ao qual os documentos pertencem
            
        Returns:
            lista de objetos Documento criados
        """
        documentos_criados: list[Documento] = []
        
        for ordem, chunk in enumerate(chunks, start=1):
            metadata_dict: dict[str, Any] = cast(dict[str, Any], chunk.metadata or {})
            documento = cls.objects.create(
                treinamento_id=treinamento_id,
                conteudo=chunk.page_content,
                metadata=metadata_dict,
                ordem=ordem
            )
            documentos_criados.append(documento)
            
        logger.info(f"Criados {len(documentos_criados)} documentos para o treinamento {treinamento_id}")
        return documentos_criados
