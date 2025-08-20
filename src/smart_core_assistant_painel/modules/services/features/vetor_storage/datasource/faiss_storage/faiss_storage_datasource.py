from py_return_success_or_error import (
    NoParams,
)

from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import (
    FaissVetorStorage,
)
from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage,
)
from smart_core_assistant_painel.modules.services.utils.erros import (
    VetorStorageError,
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
            VetorStorageError: Se ocorrer um erro durante a instanciação do
                `FaissVetorStorage`.
        """
        try:
            return FaissVetorStorage()
        except Exception as e:  # noqa: BLE001
            # Propaga um erro de domínio específico para evitar ErrorGeneric
            # e manter rastreabilidade no fluxo de inicialização.
            msg = f"Erro ao instanciar FaissVetorStorage: {str(e)}"
            raise VetorStorageError(message=msg)
