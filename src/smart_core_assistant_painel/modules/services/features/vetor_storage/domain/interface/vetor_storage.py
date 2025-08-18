"""Interface abstrata para um serviço de armazenamento de vetores.

Este módulo define o contrato que qualquer implementação de armazenamento de vetores
deve seguir, garantindo que funcionalidades essenciais como leitura, escrita e
remoção de documentos sejam padronizadas.

Classes:
    VetorStorage: Uma classe base abstrata para serviços de armazenamento de vetores.
"""
from abc import ABC, abstractmethod
from typing import List

from langchain.docstore.document import Document


class VetorStorage(ABC):
    """Define a interface abstrata para um serviço de armazenamento de vetores.

    Esta classe serve como um modelo para implementações concretas de armazenamento
    de vetores, exigindo que elas forneçam funcionalidades específicas para
    gerenciar documentos vetorizados.
    """

    @abstractmethod
    def read(self, query_vector: str, k: int = 5) -> List[Document]:
        """Lê vetores similares do armazenamento.

        Args:
            query_vector (str): O vetor de consulta para buscar.
            k (int): O número de documentos similares a serem retornados.

        Returns:
            List[Document]: Uma lista de documentos similares ao vetor de consulta.
        """
        pass

    @abstractmethod
    def write(self, documents: list[Document]) -> None:
        """Escreve uma lista de documentos no armazenamento.

        Args:
            documents (list[Document]): Os documentos a serem adicionados ao
                armazenamento de vetores.
        """
        pass

    @abstractmethod
    def remove_by_metadata(
        self,
        metadata_key: str,
        metadata_value: str,
    ) -> None:
        """Remove vetores do armazenamento com base em metadados.

        Args:
            metadata_key (str): A chave dos metadados para filtrar.
            metadata_value (str): O valor dos metadados a ser correspondido para
                remoção.
        """
        pass
