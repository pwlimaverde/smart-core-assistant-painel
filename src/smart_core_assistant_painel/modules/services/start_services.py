"""Inicializa os serviços essenciais da aplicação.

Este módulo garante que todos os serviços principais, como configuração de
ambiente, armazenamento de vetores (vector storage) e serviços de WhatsApp,
sejam iniciados corretamente quando a aplicação é lançada.
"""

import os
from loguru import logger

from .features.features_compose import FeaturesCompose

# Variável global para controlar se os serviços já foram inicializados
_services_initialized = False


def _log_environment_variables() -> None:
    """Loga as variáveis de ambiente configuradas no config_mapping.
    
    Esta função exibe todas as variáveis de ambiente que foram carregadas
    do Firebase Remote Config e estão sendo utilizadas pela aplicação.
    """
    # Mapeamento das variáveis de ambiente conforme definido em FeaturesCompose
    config_mapping = {
        # Api_Keys
        "groq_api_key": "GROQ_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "huggingface_api_key": "HUGGINGFACE_API_KEY",
        # LLM
        "llm_class": "LLM_CLASS",
        "model": "MODEL",
        "llm_temperature": "LLM_TEMPERATURE",
        # Prompts
        "prompt_system_analise_conteudo": "PROMPT_SYSTEM_ANALISE_CONTEUDO",
        "prompt_human_analise_conteudo": "PROMPT_HUMAN_ANALISE_CONTEUDO",
        "prompt_system_melhoria_conteudo": "PROMPT_SYSTEM_MELHORIA_CONTEUDO",
        "prompt_human_melhoria_conteudo": "PROMPT_HUMAN_MELHORIA_CONTEUDO",
        "prompt_human_analise_previa_mensagem": "PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM",
        "prompt_system_analise_previa_mensagem": "PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM",
        # Embeddings
        "chunk_overlap": "CHUNK_OVERLAP",
        "chunk_size": "CHUNK_SIZE",
        "embeddings_model": "EMBEDDINGS_MODEL",
        "embeddings_class": "EMBEDDINGS_CLASS",
        # Whatsapp
        "whatsapp_api_base_url": "WHATSAPP_API_BASE_URL",
        "whatsapp_api_send_text_url": "WHATSAPP_API_SEND_TEXT_URL",
        "whatsapp_api_start_typing_url": "WHATSAPP_API_START_TYPING_URL",
        "whatsapp_api_stop_typing_url": "WHATSAPP_API_STOP_TYPING_URL",
        # Utilitarios
        "valid_entity_types": "VALID_ENTITY_TYPES",
        "valid_intent_types": "VALID_INTENT_TYPES",
        "time_cache": "TIME_CACHE",
    }
    
    logger.info("=== VARIÁVEIS DE AMBIENTE CARREGADAS ===")
    
    for key, env_var in config_mapping.items():
        value = os.environ.get(env_var, "[NÃO DEFINIDA]")
        
        # Mascarar chaves de API por segurança
        if "api_key" in key.lower() and value != "[NÃO DEFINIDA]":
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            logger.info(f"{env_var}: {masked_value}")
        else:
            # Truncar valores muito longos (como prompts)
            if len(str(value)) > 100:
                truncated_value = f"{str(value)[:97]}..."
                logger.info(f"{env_var}: {truncated_value}")
            else:
                logger.info(f"{env_var}: {value}")
    
    logger.info("=== FIM DAS VARIÁVEIS DE AMBIENTE ===")

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
        FeaturesCompose.whatsapp_service()
        
        _services_initialized = True
        logger.info("Serviços inicializados com sucesso")
        
        # Log das variáveis de ambiente após carregamento do Firebase Remote Config
        _log_environment_variables()


    except Exception as e:
        logger.error(f"Erro ao inicializar serviços: {e}")
        raise
