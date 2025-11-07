"""
Mapper para Movimento do Fluxo ↔ Notion.

Converte MovimentoFluxoSync em propriedades e, se necessário, blocos.
Define um schema mínimo esperado para a database de Movimentos.

Comentários em Português e type hints completos.
"""

from __future__ import annotations

import json
from typing import Any

from ...models import NotionDatabaseConfig


class MovimentoFluxoMapper:
    """
    Mapper para o modelo MovimentoFluxo.
    """

    @staticmethod
    def get_notion_schema(config: NotionDatabaseConfig) -> dict[str, Any]:
        """
        Retorna o schema mínimo esperado para a database de Movimentos.

        Args:
            config: Configuração Notion relacionada.

        Returns:
            Dicionário com propriedades do schema.
        """
        return {
            "properties": {
                "Título": {"title": {}},
                "Motivo": {"rich_text": {}},
                "Dados Complementares": {"rich_text": {}},
                "Automático": {"checkbox": {}},
                "Data do Movimento": {"date": {}},
                "Duração (s)": {"number": {"format": "number"}},
                "Atendimento": {"relation": {}},
                "Etapa Origem": {"relation": {}},
                "Etapa Destino": {"relation": {}},
                "Atendente Origem": {"relation": {}},
                "Atendente Destino": {"relation": {}},
            }
        }

    @staticmethod
    def to_notion_properties(sync_obj: Any) -> dict[str, Any]:
        """
        Converte MovimentoFluxoSync em propriedades para a API do Notion.

        Args:
            sync_obj: Instância de MovimentoFluxoSync.

        Returns:
            Dicionário com propriedades formatadas.
        """
        mov = sync_obj.movimento
        origem_nome: str = getattr(mov, "etapa_origem_nome", "") or ""
        destino_nome: str = getattr(mov, "etapa_destino_nome", "") or ""
        titulo_val: str = (
            f"{origem_nome or 'Origem'} -> {destino_nome or 'Destino'}"
        )

        motivo_txt: str = getattr(mov, "motivo", "") or ""
        dados: Any = getattr(mov, "dados_complementares", None)
        dados_txt: str = ""
        if dados is not None:
            try:
                dados_txt = json.dumps(dados, ensure_ascii=False)[:1000]
            except Exception:
                dados_txt = str(dados)[:1000]

        # Relações
        rel_atendimento = []
        rel_etapa_origem = []
        rel_etapa_destino = []
        rel_atendente_origem = []
        rel_atendente_destino = []

        def _rel_from_sync(sync: Any) -> list[dict[str, str]]:
            ext_id = getattr(sync, "external_id", None)
            return [{"id": ext_id}] if ext_id else []

        try:
            rel_atendimento = _rel_from_sync(
                getattr(sync_obj, "atendimento_sync", None)
            )
        except Exception:
            rel_atendimento = []
        try:
            rel_etapa_origem = _rel_from_sync(
                getattr(sync_obj, "etapa_origem_sync", None)
            )
        except Exception:
            rel_etapa_origem = []
        try:
            rel_etapa_destino = _rel_from_sync(
                getattr(sync_obj, "etapa_destino_sync", None)
            )
        except Exception:
            rel_etapa_destino = []
        try:
            rel_atendente_origem = _rel_from_sync(
                getattr(sync_obj, "atendente_origem_sync", None)
            )
        except Exception:
            rel_atendente_origem = []
        try:
            rel_atendente_destino = _rel_from_sync(
                getattr(sync_obj, "atendente_destino_sync", None)
            )
        except Exception:
            rel_atendente_destino = []

        props: dict[str, Any] = {
            "Título": {
                "title": [
                    {"type": "text", "text": {"content": titulo_val[:200]}}
                ]
            },
            "Motivo": {
                "rich_text": [
                    {"type": "text", "text": {"content": motivo_txt[:1000]}}
                ]
            },
            "Dados Complementares": {
                "rich_text": [{"type": "text", "text": {"content": dados_txt}}]
            },
            "Automático": {
                "checkbox": bool(getattr(mov, "automatico", False))
            },
            "Duração (s)": {
                "number": int(getattr(mov, "duracao_segundos", 0) or 0)
            },
        }

        # Serializa data do movimento em ISO8601 apenas se existir
        data_mov = getattr(mov, "data_movimento", None)
        if data_mov:
            try:
                props["Data do Movimento"] = {
                    "date": {"start": data_mov.isoformat()}
                }
            except Exception:
                # Comentário: omite propriedade se não serializar
                pass

        if rel_atendimento:
            props["Atendimento"] = {"relation": rel_atendimento}
        if rel_etapa_origem:
            props["Etapa Origem"] = {"relation": rel_etapa_origem}
        if rel_etapa_destino:
            props["Etapa Destino"] = {"relation": rel_etapa_destino}
        if rel_atendente_origem:
            props["Atendente Origem"] = {"relation": rel_atendente_origem}
        if rel_atendente_destino:
            props["Atendente Destino"] = {"relation": rel_atendente_destino}

        return props
