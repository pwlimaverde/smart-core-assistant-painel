

from typing import Any, Self, override

from django.db import models
from django.db.models.query import QuerySet
from loguru import logger
from pgvector.django import CosineDistance, VectorField


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

    id = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )

    treinamento = models.ForeignKey(
        "Treinamento",
        on_delete=models.CASCADE,
        related_name="documentos",
        help_text="Treinamento ao qual este documento pertence",
    )

    conteudo = models.TextField(
        blank=True,
        null=True,
        help_text="Conteúdo do chunk de treinamento",
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadados do documento (tag, grupo, source, etc.)",
    )

    embedding = VectorField(
        dimensions=1024,
        null=True,
        blank=True,
        help_text="Vetor de embeddings do conteúdo do documento",
    )

    ordem = models.PositiveIntegerField(
        default=1,
        help_text="Ordem do documento no treinamento",
    )

    data_criacao = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do documento",
    )

    class Meta:
        verbose_name: str = "Documento"
        verbose_name_plural: str = "Documentos"
        ordering: list[str] = ["treinamento", "ordem"]
        indexes: list[Any] = [
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
        count: int = cls.objects.filter(treinamento_id=treinamento_id).count()
        docs = cls.objects.filter(treinamento_id=treinamento_id).delete()
        logger.info(
            f"Removidos {count} documentos do treinamento {treinamento_id} {docs}"
        )
