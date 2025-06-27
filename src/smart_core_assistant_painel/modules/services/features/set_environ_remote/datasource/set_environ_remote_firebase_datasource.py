

import asyncio
import os

from firebase_admin import remote_config
from loguru import logger

from smart_core_assistant_painel.modules.services.utils.parameters import (
    SetEnvironRemoteParameters,
)
from smart_core_assistant_painel.modules.services.utils.types import SERData


class SetEnvironRemoteFirebaseDatasource(SERData):

    @staticmethod
    async def _load_remote_config_values(config_mapping: dict[str, str]):
        # Inicialize o template do Remote Config
        template = remote_config.init_server_template()

        # Carregue o template do backend (é necessário rodar em ambiente async)
        await template.load()

        # Avalie o template para obter os parâmetros atuais
        config = template.evaluate()

        for remote_key, env_key in config_mapping.items():
            try:
                value = config.get_string(remote_key)
                os.environ[env_key] = value
            except Exception as e:
                logger.error(f"✗ Erro ao carregar {remote_key}: {e}")
                raise TypeError(
                    f'Erro ao carregar variável de ambiente {remote_key}: {
                        str(e)}')

    def __call__(self, parameters: SetEnvironRemoteParameters) -> bool:
        try:
            asyncio.run(
                self._load_remote_config_values(
                    parameters.config_mapping))
            return True
        except Exception as e:
            raise TypeError(
                f'Erro ao carregar variáveis de ambiente: {
                    str(e)}')
