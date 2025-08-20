#!/usr/bin/env python
"""Utilitário de linha de comando do Django para tarefas administrativas."""

import os
import sys
from venv import logger


def start_app() -> None:
    """Executa tarefas administrativas."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.ui.core.settings"
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Você tem certeza de que ele está "
            "instalado e disponível na sua variável de ambiente PYTHONPATH? Você "
            "esqueceu de ativar um ambiente virtual?"
        ) from exc
    execute_from_command_line(sys.argv)
    _log_environment_variables()

@staticmethod
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


if __name__ == "__main__":
    start_app()
