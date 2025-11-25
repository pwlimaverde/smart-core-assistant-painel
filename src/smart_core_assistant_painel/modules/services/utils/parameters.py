"""Define dataclasses para os parâmetros relacionados a serviços.

Este módulo contém dataclasses que estruturam os parâmetros necessários
para diferentes serviços, garantindo segurança de tipo e clareza.
"""

from dataclasses import dataclass
from typing import Any, Dict

from py_return_success_or_error import ParametersReturnResult

from .erros import (
    SetEnvironRemoteError,
    UnifieldDataServicesError,
    WhatsAppServiceError,
)


@dataclass
class SetEnvironRemoteParameters(ParametersReturnResult):
    """Parâmetros para configurar variáveis de ambiente remotas.

    Attributes:
        config_mapping (dict[str, str]): Um dicionário que mapeia os nomes
            das variáveis de ambiente para suas chaves correspondentes no
            serviço de configuração remota.
        error (SetEnvironRemoteError): O erro a ser levantado se a
            operação falhar.
    """

    config_mapping: dict[str, str]
    error: SetEnvironRemoteError

    def __str__(self) -> str:
        """Retorna uma representação em string do objeto."""
        return self.__repr__()


@dataclass
class WhatsAppMensagemParameters(ParametersReturnResult):
    """Parâmetros para o envio de mensagens via WhatsApp.

    Attributes:
        instance (str): O identificador da instância do WhatsApp.
        api_key (str): A chave de API para autenticação com o serviço.
        message_data (Dict[str, Any]): O payload da mensagem a ser enviada.
        error (WhatsAppServiceError): O erro a ser levantado se a
            operação falhar.
    """

    instance: str
    api_key: str
    message_data: Dict[str, Any]
    error: WhatsAppServiceError

    def __str__(self) -> str:
        """Retorna uma representação simplificada em string da instância."""
        return f"WhatsAppServiceParameters(instance={self.instance})"


@dataclass
class UnifieldDataServicesParameters(ParametersReturnResult):
    """Parâmetros para inicialização do serviço de dados unificado (UDS).

    Attributes:
        data_source_id (str): Identificador da fonte de dados principal
            a ser usada pelo serviço (ex.: tabela NotionGuideV2).
        provider (str): Nome do provedor/adaptador alvo. Mantém o serviço
            desacoplado e permite escolher o adapter (ex.: "notion").
        root_container_name (str): Nome padrão do container raiz onde
            páginas/itens podem ser criados.
        enable_observability (bool): Ativa logs mínimos para inspeção das
            operações.
        error (type[AppError]): Classe de erro para falhas do serviço.
    """

    data_source_id: str
    provider: str = "trello"
    root_container_name: str = "Unified Data Root"
    enable_observability: bool = False
    error: UnifieldDataServicesError

    def __str__(self) -> str:
        """Retorna uma representação simplificada em string dos parâmetros."""
        return (
            "UnifieldDataServicesParameters("
            f"data_source_id={self.data_source_id}, provider={self.provider}"
            ")"
        )
