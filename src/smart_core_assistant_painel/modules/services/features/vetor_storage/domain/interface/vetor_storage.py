from abc import ABC, abstractmethod
from typing import List

from langchain.docstore.document import Document


class VetorStorage(ABC):
    """
    Interface para o armazenamento de vetores.
    Define os métodos necessários para interagir com o armazenamento de vetores.
    """

    @abstractmethod
    def read(self,
             query_vector: str,
             k: int = 5) -> List[Document]:
        """
        Ler um vetor do armazenamento.

        :param vector: Vetor a ser adicionado.
        :param metadata: Metadados associados ao vetor.
        """
        pass

    @abstractmethod
    def write(self, documents: list[Document]) -> None:
        """
        Adiciona um vetor ao armazenamento.

        :param vector: Vetor a ser adicionado.
        :param metadata: Metadados associados ao vetor.
        """
        pass

    @abstractmethod
    def remove_by_metadata(
        self,
        metadata_key: str,
        metadata_value: str,
    ) -> None:
        """
        Remove um vetor do armazenamento.

        :param vector_id: ID do vetor a ser removido.
        """
        pass
