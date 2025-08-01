from loguru import logger

from smart_core_assistant_painel.modules.services.features.features_compose import (
    FeaturesCompose,
)


def start_services() -> None:
    """
    Inicia todos os serviços necessários da aplicação.
    Garante que o VetorStorage seja configurado desde o início.
    """
    try:
        # Carrega variáveis de ambiente remotas
        FeaturesCompose.set_environ_remote()

        # Configura VetorStorage usando o método do FeaturesCompose
        FeaturesCompose.vetor_storage()

    except Exception as e:
        logger.error(f"Erro ao inicializar serviços: {e}")
        raise
