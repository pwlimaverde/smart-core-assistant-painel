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
    def add_data_source(self, container_id: str, data_source_id: str) -> str:
        """Adiciona uma fonte de dados ao container e retorna o ID do vínculo.

        Args:
            container_id (str): ID do container.
            data_source_id (str): Identificador da fonte (ex.: `data_source_id`).

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
