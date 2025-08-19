"""Inicializa os serviços essenciais da aplicação.

Este módulo garante que todos os serviços principais, como configuração de
ambiente, armazenamento de vetores (vector storage) e serviços de WhatsApp,
sejam iniciados corretamente quando a aplicação é lançada.
"""

from loguru import logger

from .features.features_compose import FeaturesCompose

# Variável global para controlar se os serviços já foram inicializados
_services_initialized = False


def start_services() -> None:
    """Inicia e configura os serviços essenciais da aplicação.

    Esta função orquestra a inicialização dos serviços necessários,
    incluindo a configuração de variáveis de ambiente remotas, a inicialização
    do armazenamento de vetores (VetorStorage) e a configuração do serviço
    de WhatsApp.

    Implementa proteção contra inicialização dupla para evitar problemas
    quando chamada tanto pelo main.py quanto pelo Django apps.py.

    Raises:
        Exception: Repassa qualquer exceção que ocorra durante a
            inicialização de um dos serviços, após registrar o erro.
    """
    global _services_initialized
    
    # Evita inicialização dupla dos serviços
    if _services_initialized:
        logger.debug("Serviços já foram inicializados, pulando inicialização")
        return
    
    try:
        logger.info("Iniciando serviços essenciais da aplicação...")
        FeaturesCompose.set_environ_remote()
        FeaturesCompose.vetor_storage()
        FeaturesCompose.whatsapp_service()
        
        _services_initialized = True
        logger.info("Serviços inicializados com sucesso")

    except Exception as e:
        logger.error(f"Erro ao inicializar serviços: {e}")
        raise
