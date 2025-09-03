"""Fonte de dados para definir variáveis de ambiente a partir do Firebase Remote Config.

Este módulo fornece uma fonte de dados que se conecta ao Firebase, busca valores de
configuração do Remote Config e os define como variáveis de ambiente na sessão
atual da aplicação. Ele lida com a natureza assíncrona do carregamento do
template de configuração.

Classes:
    SetEnvironRemoteFirebaseDatasource: A classe principal para esta fonte de dados.
"""

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
    """Carrega configurações do Firebase Remote Config para variáveis de ambiente.

    Esta fonte de dados é responsável por inicializar o app Firebase (se ainda não
    estiver inicializado), carregar o template do servidor do Remote Config e mapear
    as chaves remotas especificadas para variáveis de ambiente locais.
    """

    @staticmethod
    async def _load_remote_config_values(
        config_mapping: dict[str, str],
    ) -> None:
        """Carrega e define variáveis de ambiente a partir do Firebase Remote Config.

        Inicializa a conexão com o Firebase, busca o template de configuração remota
        mais recente e itera sobre o mapeamento fornecido para definir cada
        variável de ambiente com seu valor remoto correspondente.

        Args:
            config_mapping (dict[str, str]): Um dicionário onde as chaves são os
                nomes dos parâmetros no Firebase Remote Config e os valores são os
                nomes das variáveis de ambiente a serem definidas.

        Raises:
            TypeError: Se ocorrer um erro ao carregar uma variável de ambiente
                       específica da configuração remota.
            Exception: Propaga qualquer outra exceção que ocorra durante a
                       inicialização do Firebase ou o processo de carregamento do template.
        """
        try:
            logger.info(
                "🔧 Iniciando carregamento do Firebase Remote Config..."
            )

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

            # Log detalhado do estado do template
            logger.info(f"📊 Estado do template: {type(config)}")

            # Tentar listar todos os parâmetros disponíveis no Remote Config
            try:
                all_params = config.get_all()
                logger.info(
                    f"📋 Parâmetros disponíveis no Remote Config: {list(all_params.keys()) if all_params else 'Nenhum'}"
                )
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível listar parâmetros: {e}")

            logger.info(
                f"🔑 Carregando {len(config_mapping)} variáveis de ambiente..."
            )
            loaded_count = 0

            for remote_key, env_key in config_mapping.items():
                try:
                    logger.info(
                        f"📝 Tentando carregar {remote_key} -> {env_key}"
                    )
                    value = config.get_string(remote_key)
                    logger.info(
                        f"🔍 Valor obtido para {remote_key}: {'[DEFINIDO]' if value else '[VAZIO/NULO]'}"
                    )
                    if value:
                        os.environ[env_key] = value
                        loaded_count += 1
                        logger.info(f"✅ {remote_key}: carregado com sucesso")
                    else:
                        logger.warning(f"⚠️  {remote_key}: valor vazio ou nulo")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar {remote_key}: {e}")
                    import traceback

                    logger.error(
                        f"📋 Traceback detalhado: {traceback.format_exc()}"
                    )
                    raise TypeError(
                        f"Erro ao carregar variável de ambiente {remote_key}: {str(e)}"
                    )

            logger.info(
                f"🎉 {loaded_count}/{len(config_mapping)} variáveis carregadas com sucesso!"
            )

        except Exception as e:
            logger.error(
                f"💥 Erro fatal no carregamento do Remote Config: {e}"
            )
            import traceback

            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            raise

    def __call__(self, parameters: SetEnvironRemoteParameters) -> bool:
        """Executa a fonte de dados para carregar as variáveis de ambiente.

        Este método serve como ponto de entrada para a fonte de dados, executando o
        método assíncrono `_load_remote_config_values` para realizar a lógica principal.

        Args:
            parameters (SetEnvironRemoteParameters): Um objeto contendo o
                dicionário `config_mapping`.

        Returns:
            bool: True se a operação for concluída com sucesso.

        Raises:
            TypeError: Se ocorrer uma exceção durante o processo de carregamento
                       das variáveis de ambiente.
        """
        try:
            logger.info("🚀 Iniciando SetEnvironRemoteFirebaseDatasource...")
            asyncio.run(
                self._load_remote_config_values(parameters.config_mapping)
            )
            logger.info(
                "✅ SetEnvironRemoteFirebaseDatasource concluído com sucesso!"
            )
            return True
        except Exception as e:
            logger.error(f"❌ Erro em SetEnvironRemoteFirebaseDatasource: {e}")
            raise TypeError(
                f"Erro ao carregar variáveis de ambiente: {str(e)}"
            )
