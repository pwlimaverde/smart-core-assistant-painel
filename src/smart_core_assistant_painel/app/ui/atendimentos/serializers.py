"""Serializers DRF para o módulo Atendimentos.

Fornece estruturas enxutas para cards do Kanban e detalhes
de mensagens, seguindo PEP8, type hints e comentários em Português.
"""

from __future__ import annotations

from typing import Any, Optional

from django.utils import timezone
from rest_framework import serializers

from .models import Atendimento, Mensagem


class MensagemSerializer(serializers.ModelSerializer[Mensagem]):
    """Serializa mensagens individuais de um atendimento."""

    class Meta:
        model = Mensagem
        fields: list[str] = [
            "id",
            "tipo",
            "conteudo",
            "remetente",
            "timestamp",
            "respondida",
            "resposta_bot",
            "confianca_resposta",
        ]


class AtendimentoCardSerializer(serializers.ModelSerializer[Atendimento]):
    """Serializa dados compactos para exibição em cards do Kanban."""

    contato_nome = serializers.SerializerMethodField()
    contato_telefone = serializers.SerializerMethodField()
    etapa_atual_id = serializers.SerializerMethodField()
    etapa_atual_nome = serializers.SerializerMethodField()
    etapa_atual_cor = serializers.SerializerMethodField()
    atendente_nome = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    last_message_timestamp = serializers.SerializerMethodField()
    produto_servico = serializers.SerializerMethodField()
    valor_orcamento = serializers.SerializerMethodField()
    categoria_venda = serializers.SerializerMethodField()

    class Meta:
        model = Atendimento
        fields: list[str] = [
            "id",
            "status",
            "departamento",
            "prioridade",
            "assunto",
            "produto_servico",
            "valor_orcamento",
            "categoria_venda",
            "data_ultima_mensagem",
            # Campos derivados
            "contato_nome",
            "contato_telefone",
            "etapa_atual_id",
            "etapa_atual_nome",
            "etapa_atual_cor",
            "atendente_nome",
            "last_message_preview",
            "last_message_timestamp",
        ]

    def get_contato_nome(self, obj: Atendimento) -> str:
        """Obtém nome do contato com fallback para perfil/telefone."""
        nome: Optional[str] = obj.contato.nome_contato
        if not nome:
            nome = obj.contato.nome_perfil_whatsapp or obj.contato.telefone
        return nome or obj.contato.telefone

    def get_contato_telefone(self, obj: Atendimento) -> str:
        return obj.contato.telefone

    def get_etapa_atual_id(self, obj: Atendimento) -> Optional[int]:
        return obj.etapa_atual.id if obj.etapa_atual else None

    def get_etapa_atual_nome(self, obj: Atendimento) -> Optional[str]:
        return obj.etapa_atual.nome if obj.etapa_atual else None

    def get_etapa_atual_cor(self, obj: Atendimento) -> Optional[str]:
        return obj.etapa_atual.cor if obj.etapa_atual else None

    def get_atendente_nome(self, obj: Atendimento) -> Optional[str]:
        return obj.atendente_humano.nome if obj.atendente_humano else None

    def get_last_message_preview(self, obj: Atendimento) -> Optional[str]:
        """Retorna um preview da última mensagem para contexto rápido."""
        mensagem: Optional[Mensagem] = obj.mensagens.order_by(
            "-timestamp"
        ).first()
        if not mensagem:
            return None
        conteudo: str = mensagem.conteudo or ""
        return conteudo[:120] + ("..." if len(conteudo) > 120 else "")

    def get_last_message_timestamp(self, obj: Atendimento) -> Optional[str]:
        """Retorna ISO timestamp da última mensagem (fallback para `data_ultima_mensagem`)."""
        mensagem: Optional[Mensagem] = obj.mensagens.order_by(
            "-timestamp"
        ).first()
        if mensagem:
            return mensagem.timestamp.isoformat()
        if obj.data_ultima_mensagem:
            return obj.data_ultima_mensagem.isoformat()
        return timezone.now().isoformat()

    def get_produto_servico(self, obj: Atendimento) -> Optional[str]:
        """Retorna produto/serviço se existir; compatível com remoção de campo."""
        valor: Any = getattr(obj, "produto_servico", None)
        return valor if isinstance(valor, str) else None

    def get_valor_orcamento(self, obj: Atendimento) -> Optional[float]:
        """Retorna valor do orçamento se existir; converte para float com segurança."""
        valor: Any = getattr(obj, "valor_orcamento", None)
        if valor is None:
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        try:
            return float(valor)  # type: ignore[arg-type]
        except Exception:
            return None

    def get_categoria_venda(self, obj: Atendimento) -> Optional[str]:
        """Retorna categoria de venda se existir; compatível com remoção de campo."""
        valor: Any = getattr(obj, "categoria_venda", None)
        return valor if isinstance(valor, str) else None


class AtendimentoDetailSerializer(serializers.ModelSerializer[Atendimento]):
    """Serializa detalhes completos de um atendimento para modal/detalhe."""

    contato_nome = serializers.SerializerMethodField()
    contato_telefone = serializers.SerializerMethodField()
    atendente_nome = serializers.SerializerMethodField()
    etapa_atual_nome = serializers.SerializerMethodField()
    departamento_nome = serializers.SerializerMethodField()
    produto_servico = serializers.SerializerMethodField()
    valor_orcamento = serializers.SerializerMethodField()
    categoria_venda = serializers.SerializerMethodField()

    class Meta:
        model = Atendimento
        fields: list[str] = [
            "id",
            "status",
            "prioridade",
            "assunto",
            "produto_servico",
            "valor_orcamento",
            "categoria_venda",
            "data_inicio",
            "data_ultima_mensagem",
            "data_fim",
            "contexto_conversa",
            "tags",
            "avaliacao",
            "feedback",
            # Derivados
            "contato_nome",
            "contato_telefone",
            "atendente_nome",
            "etapa_atual_nome",
            "departamento_nome",
        ]

    def get_contato_nome(self, obj: Atendimento) -> str:
        nome: Optional[str] = obj.contato.nome_contato
        if not nome:
            nome = obj.contato.nome_perfil_whatsapp or obj.contato.telefone
        return nome or obj.contato.telefone

    def get_contato_telefone(self, obj: Atendimento) -> str:
        return obj.contato.telefone

    def get_atendente_nome(self, obj: Atendimento) -> Optional[str]:
        return obj.atendente_humano.nome if obj.atendente_humano else None

    def get_etapa_atual_nome(self, obj: Atendimento) -> Optional[str]:
        return obj.etapa_atual.nome if obj.etapa_atual else None

    def get_departamento_nome(self, obj: Atendimento) -> Optional[str]:
        return obj.departamento.nome if obj.departamento else None

    def get_produto_servico(self, obj: Atendimento) -> Optional[str]:
        """Retorna produto/serviço se existir; compatível com remoção de campo."""
        valor: Any = getattr(obj, "produto_servico", None)
        return valor if isinstance(valor, str) else None

    def get_valor_orcamento(self, obj: Atendimento) -> Optional[float]:
        """Retorna valor do orçamento se existir; converte para float com segurança."""
        valor: Any = getattr(obj, "valor_orcamento", None)
        if valor is None:
            return None
        if isinstance(valor, (int, float)):
            return float(valor)
        try:
            return float(valor)  # type: ignore[arg-type]
        except Exception:
            return None

    def get_categoria_venda(self, obj: Atendimento) -> Optional[str]:
        """Retorna categoria de venda se existir; compatível com remoção de campo."""
        valor: Any = getattr(obj, "categoria_venda", None)
        return valor if isinstance(valor, str) else None
