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
            # Verifica se o Firebase está inicializado, se não, inicializa
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app()

            # Inicialize o template do Remote Config
            template = remote_config.init_server_template()

            # Carregue o template do backend (é necessário rodar em ambiente async)
            await template.load()

            # Avalie o template para obter os parâmetros atuais
            config = template.evaluate()

            for remote_key, env_key in config_mapping.items():
                try:
                    value = config.get_string(remote_key)
                    if value:
                        os.environ[env_key] = value
                except Exception as e:
                    raise TypeError(
                        f"Erro ao carregar variável de ambiente {remote_key}: {str(e)}"
                    )

        except Exception as e:
            logger.error(
                f"💥 Erro fatal no carregamento do Remote Config: {e}"
            )
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
