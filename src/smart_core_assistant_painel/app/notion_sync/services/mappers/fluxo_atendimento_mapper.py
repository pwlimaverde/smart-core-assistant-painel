"""
Mapper para Fluxo de Atendimento ↔ Notion.

Converte instâncias de FluxoAtendimentoSync em propriedades da
API do Notion e define um schema mínimo esperado.

Comentários em Português e type hints completos.
"""

from __future__ import annotations

from typing import Any

from ...models import NotionDatabaseConfig


class FluxoAtendimentoMapper:
    """
    Mapper para o modelo FluxoAtendimento.
    """

    @staticmethod
    def get_notion_schema(config: NotionDatabaseConfig) -> dict[str, Any]:
        """
        Retorna o schema mínimo esperado para a database de Fluxos.

        Args:
            config: Configuração Notion relacionada.

        Returns:
            Dicionário com propriedades do schema.
        """
        return {
            "properties": {
                "Nome": {"title": {}},
                "Descrição": {"rich_text": {}},
                "Ativo": {"checkbox": {}},
                "Data Criação": {"date": {}},
                "Departamento Relacionado": {"relation": {}},
            }
        }

    @staticmethod
    def to_notion_properties(sync_obj: Any) -> dict[str, Any]:
        """
        Converte FluxoAtendimentoSync em propriedades para a API do Notion.

        Comentário: usa relação com Departamento via external_id
        do objeto DepartamentoSync quando disponível.

        Args:
            sync_obj: Instância de FluxoAtendimentoSync.

        Returns:
            Dicionário com propriedades formatadas.
        """
        fluxo = sync_obj.fluxo
        nome: str = getattr(fluxo, "nome", "Fluxo") or "Fluxo"
        descricao: str = getattr(fluxo, "descricao", "") or ""

        # Relação com Departamento (se external_id estiver disponível)
        departamento_rel = []
        try:
            dep_sync = getattr(sync_obj, "departamento_sync", None)
            ext_id = getattr(dep_sync, "external_id", None)
            if ext_id:
                departamento_rel = [{"id": ext_id}]
        except Exception:
            # Silencia caso relação não esteja pronta
            departamento_rel = []

        props: dict[str, Any] = {
            "Nome": {
                "title": [{"type": "text", "text": {"content": nome}}]
            },
            "Descrição": {
                "rich_text": [
                    {"type": "text", "text": {"content": descricao[:1000]}}
                ]
            },
            "Ativo": {"checkbox": bool(getattr(fluxo, "ativo", True))},
        }

        # Serializa data de criação em ISO8601 apenas se existir
        data_criacao = getattr(fluxo, "data_criacao", None)
        if data_criacao:
            try:
                props["Data Criação"] = {
                    "date": {"start": data_criacao.isoformat()}
                }
            except Exception:
                # Comentário: se não conseguir serializar, omite a propriedade
                pass

        # Adiciona relação se disponível
        if departamento_rel:
            props["Departamento Relacionado"] = {"relation": departamento_rel}

        return props