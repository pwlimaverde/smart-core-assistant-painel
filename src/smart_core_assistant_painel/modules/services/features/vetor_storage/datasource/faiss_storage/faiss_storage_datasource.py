from py_return_success_or_error import (
    NoParams,
)

from smart_core_assistant_painel.modules.services.features.vetor_storage.datasource.faiss_storage.faiss_vetor_storage import (
    FaissVetorStorage, )
from smart_core_assistant_painel.modules.services.features.vetor_storage.domain.interface.vetor_storage import (
    VetorStorage, )
from smart_core_assistant_painel.modules.services.utils.types import VSData


class FaissStorageDatasource(VSData):

    def __call__(self, parameters: NoParams) -> VetorStorage:
        try:
            return FaissVetorStorage()
        except Exception as e:
            raise TypeError(
                f'Erro ao carregar variáveis de ambiente: {
                    str(e)}')
