from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from langchain_core.documents.base import Document
from smart_core_assistant_painel.app.ui.oraculo.fields import VectorField


from django.db.models.fields.json import JSONField


from django.db.models.fields import DateTimeField, PositiveIntegerField, TextField


from django.db.models.fields.related import ForeignKey


from typing import Any, List, Optional

from django.conf import settings
from django.db import models
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger
from pgvector.django import CosineDistance, HnswIndex
from smart_core_assistant_painel.modules.services import SERVICEHUB

from .fields import VectorField
from .embedding_data import EmbeddingData


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
    
    treinamento: ForeignKey[Any, Any] = models.ForeignKey(
        "Treinamento",
        on_delete=models.CASCADE,
        related_name="documentos",
        help_text="Treinamento ao qual este documento pertence",
    )
    
    conteudo: TextField[Any, Any] = models.TextField(
        blank=True,
        null=True,
        help_text="Conteúdo do chunk de treinamento",
    )
    
    metadata: JSONField[Any, Any] = models.JSONField(
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
    
    ordem: PositiveIntegerField[Any, Any] = models.PositiveIntegerField(
        default=1,
        help_text="Ordem do documento no treinamento",
    )
    
    data_criacao: DateTimeField[Any, Any] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do documento",
    )
    
    class Meta:
        verbose_name: str = "Documento"
        verbose_name_plural: str = "Documentos"
        ordering: list[str] = ["treinamento", "ordem"]
        indexes: list[Any] = [
            models.Index(fields=["treinamento", "ordem"]),
            models.Index(fields=["data_criacao"]),
            HnswIndex(
                name='documento_embedding_hnsw_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops']
            ),
        ]

    def __str__(self) -> str:
        """Retorna representação string do objeto."""
        if self.conteudo:
            return f"Documento {self.pk}: {self.conteudo[:50]}..."
        return f"Documento {self.pk} (vazio)"
    
    @classmethod
    def buscar_documentos_similares(
        cls,
        query_vec: List[float],
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
            documentos = cls.objects.filter(
                treinamento__treinamento_finalizado=True,
                embedding__isnull=False
            ).annotate(
                distance=CosineDistance('embedding', query_vec)
            ).order_by('distance')[:top_k]
            
            # Formata contexto
            if not documentos:
                return ""
                
            contexto_lines = ["📚 Contexto relevante:"]
            for i, doc in enumerate(documentos, 1):
                contexto_lines.extend([
                    f"\n[{i}] {doc.treinamento.tag} - {doc.treinamento.grupo}",
                    doc.conteudo.strip(),
                    "---"
                ])
            
            return "\n".join(contexto_lines)
            
        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return ""

    # ============================
    # MÉTODOS ESSENCIAIS DE APOIO
    # ============================
    
    @classmethod
    def limpar_documentos_por_treinamento(cls, treinamento_id: int) -> None:
        """Remove todos os documentos de um treinamento."""
        count = cls.objects.filter(treinamento_id=treinamento_id).count()
        cls.objects.filter(treinamento_id=treinamento_id).delete()
        logger.info(f"Removidos {count} documentos do treinamento {treinamento_id}")

    
        