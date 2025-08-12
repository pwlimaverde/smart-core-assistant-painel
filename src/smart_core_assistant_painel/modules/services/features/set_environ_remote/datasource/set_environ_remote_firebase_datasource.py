import asyncio
import os

import firebase_admin
from firebase_admin import remote_config
from loguru import logger

from smart_core_assistant_painel.modules.services.utils.parameters import (
    SetEnvironRemoteParameters,
)
from smart_core_assistant_painel.modules.services.utils.types import SERData


class SetEnvironRemoteFirebaseDatasource(SERData):
    @staticmethod
    async def _load_remote_config_values(config_mapping: dict[str, str]) -> None:
        try:
            logger.info("🔧 Iniciando carregamento do Firebase Remote Config...")

            # Verifica se o Firebase está inicializado, se não, inicializa
            try:
                firebase_admin.get_app()
                logger.info("✅ Firebase já inicializado")
            except ValueError:
                logger.info("🔥 Inicializando Firebase...")
                firebase_admin.initialize_app()
                logger.info("✅ Firebase inicializado com sucesso")

            # Inicialize o template do Remote Config
            logger.info("📋 Criando template do Remote Config...")
            template = remote_config.init_server_template()
            logger.info("✅ Template criado com sucesso")

            # Carregue o template do backend (é necessário rodar em ambiente async)
            logger.info("📥 Carregando template do backend...")
            await template.load()
            logger.info("✅ Template carregado com sucesso")

            # Avalie o template para obter os parâmetros atuais
            logger.info("🔍 Avaliando template...")
            config = template.evaluate()
            logger.info("✅ Template avaliado com sucesso")

            logger.info(f"🔑 Carregando {len(config_mapping)} variáveis de ambiente...")
            loaded_count = 0

            for remote_key, env_key in config_mapping.items():
                try:
                    logger.debug(f"📝 Carregando {remote_key} -> {env_key}")
                    value = config.get_string(remote_key)
                    if value:
                        os.environ[env_key] = value
                        loaded_count += 1
                        logger.debug(f"✅ {remote_key}: carregado com sucesso")
                    else:
                        logger.warning(f"⚠️  {remote_key}: valor vazio")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar {remote_key}: {e}")
                    raise TypeError(
                        f"Erro ao carregar variável de ambiente {remote_key}: {str(e)}"
                    )

            logger.info(
                f"🎉 {loaded_count}/{len(config_mapping)} variáveis carregadas com sucesso!"
            )

        except Exception as e:
            logger.error(f"💥 Erro fatal no carregamento do Remote Config: {e}")
            import traceback

            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise

    def __call__(self, parameters: SetEnvironRemoteParameters) -> bool:
        try:
            logger.info("🚀 Iniciando SetEnvironRemoteFirebaseDatasource...")
            asyncio.run(self._load_remote_config_values(parameters.config_mapping))
            logger.info("✅ SetEnvironRemoteFirebaseDatasource concluído com sucesso!")
            return True
        except Exception as e:
            logger.error(f"❌ Erro em SetEnvironRemoteFirebaseDatasource: {e}")
            raise TypeError(f"Erro ao carregar variáveis de ambiente: {str(e)}")
