"""Contrato genérico para serviços de dados externos.

Define a interface `UnifiedDataService` para padronizar operações de
criação e manipulação de recursos (containers, data sources, itens e
blocos) em provedores externos. Essa interface permite que adapters
concretos (ex.: Notion) sejam plugados sem acoplar a aplicação ao
provedor.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class UnifiedDataService(ABC):
    """Interface para operações de dados unificadas.

    Comentários em Português para explicar o contrato e suas operações.
    Todos os métodos devem retornar IDs dos recursos criados/alterados ou
    estruturas simples quando consulta for necessária.
    """

    @abstractmethod
    def create_container(self, name: str) -> str:
        """Cria um container genérico (ex.: página raiz) e retorna seu ID.

        Args:
            name (str): Nome do container.

        Returns:
            str: ID do container criado.
        """

    @abstractmethod
    def add_data_source(
        self,
        container_id: str,
        data_source_id: str,
        position: Optional[float] = None,
    ) -> str:
        """Adiciona uma fonte de dados ao container e retorna o ID do vínculo.

        Args:
            container_id (str): ID do container.
            data_source_id (str): Identificador da fonte (ex.: `data_source_id`).
            position (float | None): Posição opcional da fonte no container.
                No Trello, corresponde ao `pos` da lista.

        Returns:
            str: ID de referência do vínculo com a fonte de dados.
        """

    @abstractmethod
    def update_schema(
        self, data_source_id: str, schema: Dict[str, Any]
    ) -> str:
        """Atualiza o schema da data source e retorna um ID de versão/revisão.

        Args:
            data_source_id (str): Fonte de dados alvo.
            schema (dict[str, Any]): Estrutura de propriedades/campos.

        Returns:
            str: ID de versão/revisão do schema.
        """

    @abstractmethod
    def create_item(self, data_source_id: str, payload: Dict[str, Any]) -> str:
        """Cria um item/registro na data source e retorna seu ID.

        Args:
            data_source_id (str): Fonte de dados alvo.
            payload (dict[str, Any]): Dados do item.

        Returns:
            str: ID do item criado.
        """

    @abstractmethod
    def update_item(
        self, data_source_id: str, item_id: str, payload: Dict[str, Any]
    ) -> str:
        """Atualiza um item existente e retorna o ID da operação/versão.

        Args:
            data_source_id (str): Fonte de dados alvo.
            item_id (str): ID do item a ser atualizado.
            payload (dict[str, Any]): Campos atualizados.

        Returns:
            str: ID de confirmação da atualização (ex.: versão).
        """

    @abstractmethod
    def move_item(self, item_id: str, target_data_source_id: str) -> bool:
        """Move um item para outra fonte de dados (ex.: card para outra lista).

        Args:
            item_id (str): ID do item a ser movido.
            target_data_source_id (str): ID da fonte de dados de destino.

        Returns:
            bool: Verdadeiro se movido com sucesso.
        """

    @abstractmethod
    def add_relation_property(
        self, data_source_id: str, property_name: str, target_id: str
    ) -> str:
        """Cria propriedade de relação e retorna seu ID.

        Args:
            data_source_id (str): Fonte de dados alvo.
            property_name (str): Nome da propriedade de relação.
            target_id (str): ID do recurso alvo (ex.: outra tabela).

        Returns:
            str: ID da propriedade criada.
        """

    @abstractmethod
    def get_container(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do container, retornando dict ou None se não existir."""

    @abstractmethod
    def get_data_source(self, data_source_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados da fonte de dados, retornando dict ou None."""

    @abstractmethod
    def get_item(
        self, data_source_id: str, item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtém dados de um item, retornando dict ou None."""

    @abstractmethod
    def append_block(self, container_id: str, block: Dict[str, Any]) -> str:
        """Adiciona um bloco (ex.: texto) ao container e retorna o ID do bloco.

        Args:
            container_id (str): ID do container.
            block (dict[str, Any]): Estrutura do bloco.

        Returns:
            str: ID do bloco adicionado.
        """

    # ------------------------- Extensões de contrato ----------------------
    def register_webhook(
        self, model_id: str, callback_url: str, description: str
    ) -> str:
        """Registra webhook no provedor (board/list/item).

        Args:
            model_id (str): ID do recurso a observar.
            callback_url (str): URL pública para receber eventos.
            description (str): Descrição do webhook.

        Returns:
            str: ID do webhook criado.

        Comentário: implementação opcional por adapter. Por padrão, lança
        `NotImplementedError`.
        """
        raise NotImplementedError("register_webhook não implementado")

    def delete_webhook(self, webhook_id: str) -> bool:
        """Remove webhook existente no provedor.

        Args:
            webhook_id (str): ID do webhook.

        Returns:
            bool: Verdadeiro se removido com sucesso.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("delete_webhook não implementado")

    def search_items(
        self, board_id: str, query: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """Busca itens no provedor com filtros.

        Args:
            board_id (str): ID do container/board para escopo.
            query (dict[str, Any]): Parâmetros de consulta.

        Returns:
            list[dict[str, Any]]: Lista de itens encontrados.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("search_items não implementado")

    def ensure_custom_fields(
        self, board_id: str, fields: Dict[str, str]
    ) -> Dict[str, str]:
        """Garante a existência de custom fields e retorna seus IDs.

        Args:
            board_id (str): ID do container/board.
            fields (dict[str, str]): Mapa nome->tipo (ex.: "text").

        Returns:
            dict[str, str]: Mapa nome->id dos custom fields.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("ensure_custom_fields não implementado")

    def ensure_labels(
        self, board_id: str, labels: Dict[str, str]
    ) -> Dict[str, str]:
        """Garante a existência de labels no board e retorna seus IDs.

        Args:
            board_id (str): ID do board/container no provedor.
            labels (dict[str, str]): Mapa nome->cor (ex.: "alta": "red").

        Returns:
            dict[str, str]: Mapa nome->id das labels existentes/criadas.

        Comentário: implementação opcional por adapter. Alguns provedores
        podem não suportar criação de labels via API; nesse caso, o método
        deve apenas retornar labels existentes por nome.
        """
        raise NotImplementedError("ensure_labels não implementado")

    def list_items(self, data_source_id: str) -> list[Dict[str, Any]]:
        """Lista itens (cards) de um data source (lista).

        Returns:
            list[dict[str, Any]]: Lista de cards.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("list_items não implementado")

    def list_data_sources(self, container_id: str) -> list[Dict[str, Any]]:
        """Lista data sources (listas) de um container (board).

        Returns:
            list[dict[str, Any]]: Lista de listas do board.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("list_data_sources não implementado")

    def set_data_source_position(
        self, data_source_id: str, position: float | str
    ) -> bool:
        """Atualiza a posição de uma fonte de dados.

        Args:
            data_source_id (str): ID da fonte (ex.: lista Trello).
            position (float | str): Posição desejada (ex.: número, "top" ou
                "bottom" em provedores que suportem).

        Returns:
            bool: Verdadeiro se atualizado com sucesso.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("set_data_source_position não implementado")

    def archive_container(self, container_id: str) -> bool:
        """Arquiva o container no provedor externo (ex.: board Trello).

        Args:
            container_id (str): ID externo do container.

        Returns:
            bool: Verdadeiro se arquivado com sucesso.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("archive_container não implementado")

    def archive_data_source(self, data_source_id: str) -> bool:
        """Arquiva a fonte de dados (ex.: lista do Trello).

        Args:
            data_source_id (str): ID externo da fonte de dados.

        Returns:
            bool: Verdadeiro se arquivado com sucesso.

        Comentário: implementação opcional por adapter.
        """
        raise NotImplementedError("archive_data_source não implementado")
