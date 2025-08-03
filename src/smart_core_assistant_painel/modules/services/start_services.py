import os
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
        # Verifica se está em modo DEBUG para pular Firebase Remote Config
        django_debug = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
        
        if not django_debug:
            # Carrega variáveis de ambiente remotas apenas em produção
            logger.info("Carregando variáveis de ambiente remotas do Firebase...")
            FeaturesCompose.set_environ_remote()
        else:
            logger.info("Modo DEBUG ativo - pulando carregamento do Firebase Remote Config")

        # Configura VetorStorage usando o método do FeaturesCompose
        FeaturesCompose.vetor_storage()

    except Exception as e:
        logger.error(f"Erro ao inicializar serviços: {e}")
        raise
