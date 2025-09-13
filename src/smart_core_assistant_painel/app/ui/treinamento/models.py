from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Self, cast, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.indexes import Index
from django.db.models.query import QuerySet
from langchain_core.documents.base import Document
from loguru import logger
from pgvector.django import CosineDistance, VectorField


def validate_identificador(value: str) -> None:
    """Valida se o identificador está em formato válido."""
    if len(value) > 40:
        raise ValidationError("Identificador deve ter no máximo 40 caracteres.")
    if " " in value:
        raise ValidationError("Identificador não deve conter espaços.")
    if not value.islower():
        raise ValidationError("Identificador deve conter apenas letras minúsculas.")
    if not re.match(r"^[a-z0-9_]+$", value):
        raise ValidationError(
            "Identificador deve conter apenas letras minúsculas, números e underscore."
        )

class Treinamento(models.Model):
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    tag: models.CharField[str] = models.CharField(
        max_length=40,
        validators=[validate_identificador],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o treinamento",
    )
    grupo: models.CharField[str] = models.CharField(
        max_length=40,
        validators=[validate_identificador],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do treinamento",
    )
    conteudo: models.TextField[str | None] = models.TextField(
        blank=True,
        null=True,
        help_text="Conteúdo completo do treinamento (antes da divisão em chunks)",
    )
    treinamento_finalizado: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Indica se o treinamento foi finalizado",
    )
    treinamento_vetorizado: models.BooleanField[bool] = models.BooleanField(
        default=False,
        help_text="Indica se o treinamento foi vetorizado com sucesso",
    )
    data_criacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do treinamento",
    )
    data_atualizacao: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True,
        help_text="Data da última atualização do treinamento",
    )

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
        ordering = ["-data_criacao"]
        db_table = "oraculo_treinamento"
        indexes: list[Index] = [
            models.Index(fields=["tag", "grupo"]),
            models.Index(fields=["data_criacao"]),
            models.Index(
                fields=["treinamento_finalizado", "treinamento_vetorizado"]
            ),
        ]

    @override
    def clean(self) -> None:
        super().clean()
        if self.tag and self.grupo and self.tag == self.grupo:
            raise ValidationError(
                message={"grupo": "O grupo não pode ser igual à tag."}
            )

    @override
    def __str__(self) -> str:
        return str(self.tag) if self.tag else f"Treinamento {self.id}"

class Documento(models.Model):
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    treinamento: models.ForeignKey["Treinamento"] = models.ForeignKey(
        "Treinamento",
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
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["treinamento", "ordem"]
        db_table = "oraculo_documento"
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
        try:
            documentos: QuerySet[Self] = (
                cls.objects.filter(
                    treinamento__treinamento_finalizado=True,
                    embedding__isnull=False,
                )
                .annotate(distance=CosineDistance("embedding", query_vec))
                .order_by("distance")[:top_k]
            )
            if not documentos:
                return ""
            contexto_lines: list[str] = ["📚 Contexto relevante:"]
            for i, doc in enumerate(documentos, 1):
                if doc.conteudo:
                    contexto_lines.extend(
                        [
                            f"[{i}] {doc.treinamento.tag} - {doc.treinamento.grupo}",
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
        docs = cls.objects.filter(treinamento_id=treinamento_id).delete()
        logger.info(f"Removidos {docs} documentos do treinamento {treinamento_id}")

    @classmethod
    def criar_documentos_de_chunks(
        cls,
        chunks: list[Document],
        treinamento_id: int,
    ) -> list["Documento"]:
        documentos_criados: list[Documento] = []
        for ordem, chunk in enumerate(chunks, start=1):
            metadata_dict: dict[str, Any] = cast(dict[str, Any], chunk.metadata or {})
            documento = cls.objects.create(
                treinamento_id=treinamento_id,
                conteudo=chunk.page_content,
                metadata=metadata_dict,
                ordem=ordem,
            )
            documentos_criados.append(documento)
        logger.info(
            f"Criados {len(documentos_criados)} documentos para o treinamento {treinamento_id}"
        )
        return documentos_criados

class QueryCompose(models.Model):
    """
    Representa um intent: descrição -> embedding + prompt system associado.
    """
    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    tag: models.CharField[str] = models.CharField(
        max_length=40,
        validators=[validate_identificador],
        blank=False,
        null=False,
        help_text="Tag auxiliar para organizar intents (ex: 'orcamento', 'suporte')"
    )
    grupo: models.CharField[str] = models.CharField(
        max_length=40,
        validators=[validate_identificador],
        blank=False,
        null=False,
        help_text="Campo obrigatório para identificar o grupo do QueryCompose",
    )
    descricao: models.TextField[str] = models.TextField(
        blank=False,
        null=False,
        help_text="Texto descritivo usado para gerar o embedding (representação do intent)"
    )
    exemplo: models.TextField[str] = models.TextField(
        blank=False,
        null=False,
        help_text="Exemplo de query que representa o intent"
    )
    comportamento: models.TextField[str] = models.TextField(
        blank=False,
        null=False,
        help_text="Prompt system que orienta o comportamento da LLM para esse intent"
    )
    embedding: VectorField = VectorField(
        dimensions=1024,
        null=True,
        blank=True,
        help_text="Embedding gerado a partir da description"
    )

    created_at: models.DateTimeField[datetime] = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Query Compose"
        verbose_name_plural = "Query Composes"
        indexes = [
        models.Index(fields=['tag']),
        models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.tag or 'sem-tag'}"
    
    def to_embedding_text(self) -> str:
        """
        Gera texto otimizado para criação de embeddings.
        Combina descrição e exemplo de forma que capture melhor a semântica do intent.
        
        Returns:
            str: Texto otimizado para embedding
        """
        embedding_parts: list[str] = []
        if self.tag:
            embedding_parts.append(f"{self.tag}:")
 
        if self.descricao:
            embedding_parts.append(f"{self.descricao.strip()}")
        return "\n".join(embedding_parts)

    @classmethod
    def buscar_comportamento_similar(
        cls,
        query_vec: list[float],
        top_k: int = 1,
    ) -> str | None:
        try:
            comportamento: QuerySet[Self] = (
                cls.objects.filter(embedding__isnull=False,)
                .annotate(distance=CosineDistance("embedding", query_vec))
                .only("tag", "descricao", "comportamento")
                .order_by("distance")[:top_k]
            )
            if not comportamento:
                return ""
            
            # Log da distância mais similar encontrada
            most_similar_distance = comportamento[0].distance
            logger.warning(
                f"Comportamento similar encontrado - Tag: {comportamento[0].tag}, "
                f"Distância: {most_similar_distance:.4f}"
            )
            if most_similar_distance > 0.25:
                return None
            # Formatação conforme especificado no planejamento
            prompt = (
                f"📚 Comportamento que deve ser seguido:\n"
                f"{comportamento[0].comportamento}"
            )
            return prompt
            
        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return None

    @classmethod
    def build_intent_types_config(
        cls,
    ) -> str:
        """Gera JSON (string) de intent_types baseado nos registros.

        Estrutura:
            {
                "intent_types": {
                    "<grupo>": {
                        "<tag>": "<descricao> e exemplos estruturados"
                    }
                }
            }

        Returns:
            str: JSON válido (string) com a chave raiz "intent_types".
        """
        # Consulta ordenada para previsibilidade da saída
        qs: QuerySet[Self] = (
            cls.objects
            .only("grupo", "tag", "descricao", "exemplo")
            .order_by("grupo", "tag")
        )

        result: dict[str, dict[str, dict[str, str]]] = {"intent_types": {}}

        for qc in qs:
            grupo: str = (qc.grupo or "").strip()
            tag: str = (qc.tag or "").strip()
            if not grupo or not tag:
                # Ignora registros sem grupo ou tag válidos
                continue

            group_map: dict[str, str]
            group_map = result["intent_types"].setdefault(grupo, {})

            # Normaliza descricao em linha única e prepara exemplos multilinha
            descricao_clean: str = re.sub(
                r"\s+", " ", (qc.descricao or "")
            ).strip()
            exemplo_raw: str = (qc.exemplo or "").strip()
            exemplos: list[str] = [
                ln.strip() for ln in exemplo_raw.splitlines() if ln.strip()
            ]

            # Monta string estruturada para interpretação clara pela LLM
            if descricao_clean or exemplos:
                lines: list[str] = []
                if descricao_clean:
                    lines.append(descricao_clean)
                if exemplos:
                    lines.append("Exemplos:")
                    for item in exemplos:
                        lines.append(f"- {item}")
                value: str = "\n".join(lines)
            else:
                # Mantém compatibilidade caso ambos estejam vazios
                value = ""

            group_map[tag] = value

        # Retorna string JSON válida e estável (ordenada)
        return json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )