from py_return_success_or_error import (
    NoParams,
)

from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import (
    FaissVetorStorage,
)
from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage,
)
from smart_core_assistant_painel.modules.services.utils.types import VSData


class FaissStorageDatasource(VSData):
    """Datasource para instanciar o serviço de armazenamento vetorial Faiss.

    Esta classe é responsável por criar e retornar uma instância concreta
    do `FaissVetorStorage`.
    """

    def __call__(self, parameters: NoParams) -> VetorStorage:
        """Cria e retorna a instância do FaissVetorStorage.

        Args:
            parameters (NoParams): Nenhum parâmetro é esperado.

        Returns:
            VetorStorage: Uma instância do serviço de armazenamento vetorial.

        Raises:
            TypeError: Se ocorrer um erro durante a instanciação do
                       `FaissVetorStorage`.
        """
        try:
            return FaissVetorStorage()
        except Exception as e:
            raise TypeError(f"Erro ao carregar variáveis de ambiente: {str(e)}")
