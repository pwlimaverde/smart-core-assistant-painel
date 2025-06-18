import asyncio
import os

from firebase_admin import remote_config

from smart_core_assistant_painel.app.ui.manage import start_app
from smart_core_assistant_painel.modules.initial_loading.start_initial_loading import (
    stard_initial_loading, )


async def load_remote_config_values():
    # Inicialize o template do Remote Config
    template = remote_config.init_server_template()

    # Carregue o template do backend (é necessário rodar em ambiente async)
    await template.load()

    # Avalie o template para obter os parâmetros atuais
    config = template.evaluate()

    config_mapping = {
        'secret_key_django': 'SECRET_KEY_DJANGO',
        'groq_api_key': 'GROQ_API_KEY',
        # 'whatsapp_api_base_url': 'WHATSAPP_API_BASE_URL',
        # 'database_url': 'DATABASE_URL',
        # 'api_key': 'API_KEY',
        # 'max_retries': 'MAX_RETRIES',
        # Adicione outros mapeamentos conforme necessário
    }

    # Atribuir valores às variáveis de ambiente
    for remote_key, env_key in config_mapping.items():
        try:
            value = config.get_string(remote_key)
            os.environ[env_key] = value
            print(f"✓ {env_key}: {value}")
        except Exception as e:
            print(f"✗ Erro ao carregar {remote_key}: {e}")

if __name__ == '__main__':
    if os.environ.get('RUN_MAIN') == 'true':
        stard_initial_loading()
        asyncio.run(load_remote_config_values())
    start_app()
