"""Este módulo é responsável por inicializar os serviços essenciais.

Garante que todos os serviços, como configuração de ambiente, armazenamento
de vetores e serviços de WhatsApp, sejam iniciados corretamente durante a
inicialização da aplicação.
"""

from loguru import logger

from .features.features_compose import FeaturesCompose


def start_services() -> None:
    """Inicia e configura os serviços essenciais da aplicação.

    Esta função orquestra a inicialização dos serviços necessários,
    incluindo a configuração de variáveis de ambiente remotas, a inicialização
    do armazenamento de vetores (VetorStorage) e a configuração do serviço
    de WhatsApp.

    Raises:
        Exception: Repassa qualquer exceção que ocorra durante a
            inicialização de um dos serviços, após registrar o erro.
    """
    try:
        FeaturesCompose.set_environ_remote()
        FeaturesCompose.vetor_storage()
        FeaturesCompose.whatsapp_service()

    except Exception as e:
        logger.error(f"Erro ao inicializar serviços: {e}")
        raise
