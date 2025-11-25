"""
Mapper para Etapa do Fluxo ↔ Notion.

Converte EtapaFluxoSync em propriedades para a API do Notion e
define um schema mínimo esperado.

Comentários em Português e type hints completos.
"""

from __future__ import annotations

from typing import Any

from ...models import NotionDatabaseConfig


class EtapaFluxoMapper:
    """
    Mapper para o modelo EtapaFluxo.
    """

    @staticmethod
    def get_notion_schema(config: NotionDatabaseConfig) -> dict[str, Any]:
        """
        Retorna o schema mínimo esperado para a database de Etapas.

        Args:
            config: Configuração Notion relacionada.

        Returns:
            Dicionário com propriedades do schema.
        """
        return {
            "properties": {
                "Nome": {"title": {}},
                "Descrição": {"rich_text": {}},
                "Ordem": {"number": {"format": "number"}},
                "Cor": {"select": {}},
                "Tipo de Etapa": {"select": {}},
                "Permite Atribuição": {"checkbox": {}},
                "Fluxo Relacionado": {"relation": {}},
                "Data Criação": {"date": {}},
            }
        }

    @staticmethod
    def to_notion_properties(sync_obj: Any) -> dict[str, Any]:
        """
        Converte EtapaFluxoSync em propriedades para a API do Notion.

        Args:
            sync_obj: Instância de EtapaFluxoSync.

        Returns:
            Dicionário com propriedades formatadas.
        """
        etapa = sync_obj.etapa
        nome: str = getattr(etapa, "nome", "Etapa") or "Etapa"
        descricao: str = getattr(etapa, "descricao", "") or ""
        ordem_val: int = int(getattr(etapa, "ordem", 0) or 0)
        cor_val: str = getattr(etapa, "cor", "") or ""
        tipo_val: str = getattr(etapa, "tipo_etapa", "") or ""
        permite: bool = bool(getattr(etapa, "permite_atribuicao", False))

        # Relação com Fluxo (se external_id estiver disponível)
        fluxo_rel = []
        try:
            fluxo_sync = getattr(sync_obj, "fluxo_sync", None)
            ext_id = getattr(fluxo_sync, "external_id", None)
            if ext_id:
                fluxo_rel = [{"id": ext_id}]
        except Exception:
            fluxo_rel = []

        props: dict[str, Any] = {
            "Nome": {"title": [{"type": "text", "text": {"content": nome}}]},
            "Descrição": {
                "rich_text": [
                    {"type": "text", "text": {"content": descricao[:1000]}}
                ]
            },
            "Ordem": {"number": ordem_val},
            "Cor": {"select": {"name": cor_val}} if cor_val else {},
            "Tipo de Etapa": {"select": {"name": tipo_val}}
            if tipo_val
            else {},
            "Permite Atribuição": {"checkbox": permite},
        }

        # Serializa data de criação em ISO8601 apenas se existir
        data_criacao = getattr(etapa, "data_criacao", None)
        if data_criacao:
            try:
                props["Data Criação"] = {
                    "date": {"start": data_criacao.isoformat()}
                }
            except Exception:
                # Comentário: omite propriedade se não serializar
                pass

        if fluxo_rel:
            props["Fluxo Relacionado"] = {"relation": fluxo_rel}

        return props
