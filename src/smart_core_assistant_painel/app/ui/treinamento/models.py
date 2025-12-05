from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Self, cast, override

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.indexes import Index
from django.db.models.query import QuerySet
from langchain_core.documents import Document
from loguru import logger
from pgvector.django import CosineDistance, VectorField


def validate_identificador(value: str) -> None:
    """Valida se o identificador está em formato válido."""
    if len(value) > 40:
        raise ValidationError(
            "Identificador deve ter no máximo 40 caracteres."
        )
    if " " in value:
        raise ValidationError("Identificador não deve conter espaços.")
    if not value.islower():
        raise ValidationError(
            "Identificador deve conter apenas letras minúsculas."
        )
    if not re.match(r"^[a-z0-9_]+$", value):
        raise ValidationError(
            "Identificador deve conter apenas letras minúsculas, números e underscore."
        )


class Treinamento(models.Model):
    """[TRN-CON-003] Modelo para gestão de treinamentos vetorizados.

    Armazena metadados e status dos documentos processados para a base de conhecimento.
    """

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
        distance_threshold: float = 0.40,  # valor de corte para distância
    ) -> tuple[str, list[int]]:
        """Busca documentos similares com rastreabilidade.

        Args:
            query_vec: Vetor de embedding da query.
            top_k: Número máximo de resultados.
            distance_threshold: Limiar de distância máxima.

        Returns:
            Tupla (contexto_formatado, lista_ids_documentos).
            - contexto_formatado: String com contexto RAG.
            - lista_ids_documentos: Lista de IDs para rastreabilidade.
        """
        doc_ids: list[int] = []
        try:
            documentos: QuerySet[Self] = (
                cls.objects.annotate(
                    distance=CosineDistance("embedding", query_vec)
                )
                .filter(
                    treinamento__treinamento_finalizado=True,
                    embedding__isnull=False,
                    distance__lte=distance_threshold,
                )
                .order_by("distance")[:top_k]
            )
            if not documentos:
                return "", []

            contexto_lines: list[str] = ["📚 Contexto relevante:"]
            for i, doc in enumerate(documentos, 1):
                doc_ids.append(doc.id)  # Coleta ID para rastreabilidade
                if doc.conteudo:
                    contexto_lines.extend(
                        [
                            f"[{i}] {doc.treinamento.tag} - {doc.treinamento.grupo}",
                            doc.conteudo.strip(),
                            "---",
                        ]
                    )
                logger.info(
                    f"RAG: doc_id={doc.id}, distância={doc.distance:.4f}"
                )

            return "\n".join(contexto_lines), doc_ids

        except Exception as e:
            logger.error(f"Erro na busca semântica: {e}")
            return "", []

    @classmethod
    def limpar_documentos_por_treinamento(cls, treinamento_id: int) -> None:
        docs = cls.objects.filter(treinamento_id=treinamento_id).delete()
        logger.info(
            f"Removidos {docs} documentos do treinamento {treinamento_id}"
        )

    @classmethod
    def criar_documentos_de_chunks(
        cls,
        chunks: list[Document],
        treinamento_id: int,
    ) -> list["Documento"]:
        documentos_criados: list[Documento] = []
        for ordem, chunk in enumerate(chunks, start=1):
            metadata_dict: dict[str, Any] = cast(
                dict[str, Any], chunk.metadata or {}
            )
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
    """[TRN-INT-001] Representa um intent: descrição -> embedding + prompt system associado.

    Cadastro de Intenções (Query Compose).
    """

    id: models.AutoField = models.AutoField(
        primary_key=True, help_text="Chave primária do registro"
    )
    tag: models.CharField[str] = models.CharField(
        max_length=40,
        validators=[validate_identificador],
        blank=False,
        null=False,
        help_text="Tag auxiliar para organizar intents (ex: 'orcamento', 'suporte')",
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
        help_text="Texto descritivo usado para gerar o embedding (representação do intent)",
    )
    exemplo: models.TextField[str] = models.TextField(
        blank=False,
        null=False,
        help_text="Exemplo de query que representa o intent",
    )
    comportamento: models.TextField[str] = models.TextField(
        blank=False,
        null=False,
        help_text="Prompt system que orienta o comportamento da LLM para esse intent",
    )
    embedding: VectorField = VectorField(
        dimensions=1024,
        null=True,
        blank=True,
        help_text="Embedding gerado a partir da description",
    )

    created_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Query Compose"
        verbose_name_plural = "Query Composes"
        indexes = [
            models.Index(fields=["tag"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.tag or 'sem-tag'}"

    def to_embedding_text(self) -> str:
        """
        Gera texto otimizado para criação de embeddings, padronizando o
        conteúdo conforme esperado pelos testes e pelo pipeline de
        embeddings.

        Regras:
        - Primeira linha: "Categoria: <tag>" quando houver tag.
        - Segunda linha: descrição (quando houver)
        - Terceira linha: "Exemplo: <exemplo>" (quando houver)
        - Quando descrição e exemplo estiverem vazios, retornar string vazia.

        Returns:
            str: Texto formatado para geração de embedding.
        """
        # Partes que compõem o texto final, respeitando as regras acima
        parts: list[str] = []

        tag: str = (self.tag or "").strip()
        descricao: str = (self.descricao or "").strip()
        exemplo: str = (self.exemplo or "").strip()

        # Se não houver conteúdo semântico (descrição e exemplo), retornar vazio
        if not descricao and not exemplo:
            return ""

        if tag:
            parts.append(f"Categoria: {tag}")
        if descricao:
            parts.append(descricao)
        if exemplo:
            parts.append(f"Exemplo: {exemplo}")

        return "\n".join(parts)

    @classmethod
    def buscar_comportamento_similar(
        cls,
        query_vec: list[float],
        top_k: int = 1,
        distance_threshold: float = 0.25,  # threshold configurável
    ) -> str | None:
        """Busca comportamento similar via embedding com filtro no banco.

        O filtro de distância é aplicado diretamente na query SQL,
        evitando trazer registros que serão descartados em Python.

        Args:
            query_vec: Vetor de embedding da query.
            top_k: Número máximo de resultados.
            distance_threshold: Limiar de distância (padrão 0.25).

        Returns:
            Prompt formatado com comportamento ou None se não encontrado.
        """
        try:
            comportamento: QuerySet[Self] = (
                cls.objects.filter(
                    embedding__isnull=False,
                )
                .annotate(distance=CosineDistance("embedding", query_vec))
                .filter(distance__lte=distance_threshold)  # Filtro no banco
                .only("tag", "descricao", "comportamento")
                .order_by("distance")[:top_k]
            )
            if not comportamento:
                return None

            # Log da distância mais similar encontrada
            most_similar_distance = comportamento[0].distance
            logger.info(
                f"Comportamento similar encontrado - Tag: {comportamento[0].tag}, "
                f"Distância: {most_similar_distance:.4f} (limiar: {distance_threshold})"
            )

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
        qs: QuerySet[Self] = cls.objects.only(
            "grupo", "tag", "descricao", "exemplo"
        ).order_by("grupo", "tag")

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
