"""Configuração do painel de administração do Django para o aplicativo Treinamento.

Este módulo registra os modelos do aplicativo Treinamento no painel de administração
do Django e personaliza a forma como eles são exibidos e gerenciados.
"""

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Documento, Treinamento


@admin.register(Treinamento)
class TreinamentoAdmin(admin.ModelAdmin[Treinamento]):
    """Admin para o modelo Treinamento."""

    list_display = [
        "id",
        "tag",
        "grupo",
        "treinamento_finalizado",
        "treinamento_vetorizado",
        "embedding_preview",
        "get_documentos_count",
    ]
    search_fields = ["tag"]
    list_filter = ["treinamento_finalizado", "treinamento_vetorizado"]
    ordering = ["id"]
    fieldsets = (
        (
            "Informações do Treinamento",
            {
                "fields": (
                    "tag",
                    "grupo",
                    "conteudo",
                    "treinamento_finalizado",
                    "treinamento_vetorizado",
                    "embedding_preview",
                ),
                "classes": ("wide",),
            },
        ),
    )
    list_per_page = 25
    save_on_top = True
    readonly_fields = ["embedding_preview"]
    actions = [
        "marcar_como_vetorizado",
        "marcar_como_nao_vetorizado",
        "reprocessar_treinamentos",
    ]

    @admin.display(description="Número de Documentos")
    def get_documentos_count(self, obj: Treinamento) -> int:
        """Retorna o número de documentos associados ao treinamento."""
        if obj and obj.pk:
            try:
                return obj.documentos.count()
            except Exception:
                return 0
        return 0

    @admin.display(description="Embedding (prévia)")
    def embedding_preview(self, obj: Treinamento) -> str:
        """Exibe uma prévia do vetor de embedding salvo."""
        try:
            vetor = getattr(obj, "embedding", None)
            if vetor is None:
                return "-"
            try:
                if hasattr(vetor, "size") and getattr(vetor, "size", 0) == 0:
                    return "[embedding vazio]"
                elif hasattr(vetor, "__len__"):
                    try:
                        if len(vetor) == 0:
                            return "[embedding vazio]"
                    except (ValueError, TypeError):
                        pass
            except Exception:
                pass

            seq: list[Any] = []
            try:
                if isinstance(vetor, (list, tuple)):
                    seq = list(vetor)
                elif hasattr(vetor, "tolist") and callable(getattr(vetor, "tolist")):
                    seq = vetor.tolist()
                else:
                    try:
                        for i, item in enumerate(vetor):
                            if i >= 10:
                                break
                            seq.append(item)
                    except (TypeError, ValueError):
                        return "[embedding inválido]"
            except Exception:
                return "[embedding inválido]"

            if not seq:
                return "[embedding vazio]"

            normalizado: list[float] = []
            for i, x in enumerate(seq):
                if i >= 10:
                    break
                try:
                    normalizado.append(float(x))
                except (ValueError, TypeError):
                    continue

            if not normalizado:
                return "[embedding vazio]"

            tam_total = len(normalizado)
            try:
                if hasattr(vetor, "size"):
                    tam_total = getattr(vetor, "size", tam_total)
                elif hasattr(vetor, "__len__"):
                    try:
                        tam_total = len(vetor)
                    except (ValueError, TypeError):
                        tam_total = len(seq)
                else:
                    tam_total = len(seq)
            except Exception:
                pass

            head = normalizado[:10]
            fmt_head = ", ".join(f"{x:.4f}" for x in head)
            sufixo = ", ..." if tam_total > 10 else ""
            return f"[{fmt_head}{sufixo}] (dim={tam_total})"

        except Exception as e:
            return f"Erro: {type(e).__name__}"

    @admin.action(description="Marcar treinamentos selecionados como vetorizados")
    def marcar_como_vetorizado(
        self, request: HttpRequest, queryset: QuerySet[Treinamento]
    ) -> None:
        """Marca os treinamentos selecionados como vetorizados."""
        queryset.update(treinamento_vetorizado=True)
        self.message_user(
            request,
            f"{queryset.count()} treinamentos marcados como vetorizados.",
        )

    @admin.action(description="Marcar treinamentos selecionados como não vetorizados")
    def marcar_como_nao_vetorizado(
        self, request: HttpRequest, queryset: QuerySet[Treinamento]
    ) -> None:
        """Marca os treinamentos selecionados como não vetorizados."""
        queryset.update(treinamento_vetorizado=False)
        self.message_user(
            request,
            f"{queryset.count()} treinamentos marcados como não vetorizados.",
        )

    @admin.action(
        description="Reprocessar treinamentos selecionados (marca como finalizado)"
    )
    def reprocessar_treinamentos(
        self, request: HttpRequest, queryset: QuerySet[Treinamento]
    ) -> None:
        """Reprocessa os treinamentos selecionados marcando como finalizados."""
        queryset.update(treinamento_finalizado=True, treinamento_vetorizado=False)
        self.message_user(
            request,
            f"{queryset.count()} treinamentos marcados para reprocessamento.",
        )


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin[Documento]):
    """Admin para o modelo Documento."""

    list_display = [
        "id",
        "treinamento_tag",
        "ordem",
        "conteudo_preview",
        "metadata_preview",
        "data_criacao",
    ]
    search_fields = ["treinamento__tag", "conteudo"]
    list_filter = ["treinamento__tag", "treinamento__grupo", "data_criacao"]
    ordering = ["treinamento__tag", "ordem"]
    exclude = ["embedding"]
    readonly_fields = [
        "treinamento",
        "conteudo",
        "metadata",
        "embedding_preview",
        "ordem",
        "data_criacao",
    ]
    list_per_page = 50
    save_on_top = True

    def has_change_permission(
        self, request: HttpRequest, obj: Documento | None = None
    ) -> bool:
        return False

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @admin.display(description="Tag do Treinamento")
    def treinamento_tag(self, obj: Documento) -> str:
        """Retorna a tag do treinamento associado."""
        return (
            obj.treinamento.tag
            if obj.treinamento and obj.treinamento.tag
            else "-"
        )

    @admin.display(description="Conteúdo (prévia)")
    def conteudo_preview(self, obj: Documento) -> str:
        """Exibe uma prévia do conteúdo do documento."""
        if obj and obj.conteudo:
            preview = obj.conteudo[:200]
            return preview + "..." if len(obj.conteudo) > 200 else preview
        return "Conteúdo vazio"

    @admin.display(description="Metadados")
    def metadata_preview(self, obj: Documento) -> str:
        """Exibe uma prévia dos metadados do documento."""
        if obj and obj.metadata:
            try:
                metadata_str = str(obj.metadata)
                preview = metadata_str[:100]
                return preview + "..." if len(metadata_str) > 100 else preview
            except Exception:
                return "Erro ao exibir metadados"
        return "Sem metadados"

    @admin.display(description="Embedding (prévia)")
    def embedding_preview(self, obj: Documento) -> str:
        """Exibe uma prévia do vetor de embedding salvo."""
        try:
            vetor = getattr(obj, "embedding", None)
            if vetor is None:
                return "-"
            try:
                if hasattr(vetor, "size") and getattr(vetor, "size", 0) == 0:
                    return "[embedding vazio]"
                elif hasattr(vetor, "__len__"):
                    try:
                        if len(vetor) == 0:
                            return "[embedding vazio]"
                    except (ValueError, TypeError):
                        pass
            except Exception:
                pass

            seq: list[Any] = []
            try:
                if isinstance(vetor, (list, tuple)):
                    seq = list(vetor)
                elif hasattr(vetor, "tolist") and callable(getattr(vetor, "tolist")):
                    seq = vetor.tolist()
                else:
                    try:
                        for i, item in enumerate(vetor):
                            if i >= 10:
                                break
                            seq.append(item)
                    except (TypeError, ValueError):
                        return "[embedding inválido]"
            except Exception:
                return "[embedding inválido]"

            if not seq:
                return "[embedding vazio]"

            normalizado: list[float] = []
            for i, x in enumerate(seq):
                if i >= 10:
                    break
                try:
                    normalizado.append(float(x))
                except (ValueError, TypeError):
                    continue

            if not normalizado:
                return "[embedding vazio]"

            tam_total = len(normalizado)
            try:
                if hasattr(vetor, "size"):
                    tam_total = getattr(vetor, "size", tam_total)
                elif hasattr(vetor, "__len__"):
                    try:
                        tam_total = len(vetor)
                    except (ValueError, TypeError):
                        tam_total = len(seq)
                else:
                    tam_total = len(seq)
            except Exception:
                pass

            head = normalizado[:10]
            fmt_head = ", ".join(f"{x:.4f}" for x in head)
            sufixo = ", ..." if tam_total > 10 else ""
            return f"[{fmt_head}{sufixo}] (dim={tam_total})"

        except Exception as e:
            return f"Erro: {type(e).__name__}"