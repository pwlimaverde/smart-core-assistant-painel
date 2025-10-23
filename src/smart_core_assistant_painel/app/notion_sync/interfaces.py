"""
Interface abstrata para serviços de sincronização externa.

Este módulo define o contrato que qualquer serviço de sincronização
com plataformas externas (Notion, Airtable, etc) deve implementar.
"""

from abc import ABC, abstractmethod
from typing import Any


class ExternalSyncServiceInterface(ABC):
    """
    Interface abstrata para serviços de sincronização com plataformas externas.

    Esta interface define o contrato que qualquer implementação de serviço
    de sincronização deve seguir, garantindo que o sistema possa trocar
    de plataforma (Notion → Airtable, por exemplo) sem alterar o código core.

    Padrão de Design: Strategy + Adapter
    """

    @abstractmethod
    def create_record(
        self,
        model_name: str,
        django_id: int,
        data: dict[str, Any],
    ) -> str:
        """
        Cria um novo registro na plataforma externa.

        Este método deve:
        1. Mapear os dados do Django para o formato da plataforma
        2. Criar o registro via API
        3. Retornar o ID do registro criado na plataforma externa

        Args:
            model_name: Nome do modelo Django (ex: "Cliente", "Contato").
            django_id: ID do registro no Django.
            data: Dados do registro em formato Django.

        Returns:
            ID do registro criado na plataforma externa (ex: page_id do Notion).

        Raises:
            SyncError: Erro genérico de sincronização.
            NotionSyncError: Erro específico da plataforma.
            MappingError: Erro no mapeamento de dados.
        """
        pass

    @abstractmethod
    def update_record(
        self,
        model_name: str,
        external_id: str,
        django_id: int,
        data: dict[str, Any],
    ) -> bool:
        """
        Atualiza um registro existente na plataforma externa.

        Este método deve:
        1. Mapear os dados do Django para o formato da plataforma
        2. Atualizar o registro via API
        3. Retornar True se atualização foi bem-sucedida

        Args:
            model_name: Nome do modelo Django (ex: "Cliente", "Contato").
            external_id: ID do registro na plataforma externa.
            django_id: ID do registro no Django.
            data: Dados atualizados do registro em formato Django.

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário.

        Raises:
            SyncError: Erro genérico de sincronização.
            NotionSyncError: Erro específico da plataforma.
            MappingError: Erro no mapeamento de dados.
        """
        pass

    @abstractmethod
    def delete_record(
        self,
        model_name: str,
        external_id: str,
    ) -> bool:
        """
        Deleta (ou arquiva) um registro na plataforma externa.

        Nota: Algumas plataformas não permitem deleção real, apenas arquivamento.

        Args:
            model_name: Nome do modelo Django (ex: "Cliente", "Contato").
            external_id: ID do registro na plataforma externa.

        Returns:
            True se a deleção/arquivamento foi bem-sucedida.

        Raises:
            SyncError: Erro genérico de sincronização.
            NotionSyncError: Erro específico da plataforma.
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Valida se a conexão com a plataforma externa está funcionando.

        Este método deve:
        1. Testar credenciais (token, API key, etc)
        2. Verificar se os databases/tabelas necessários existem
        3. Retornar True se tudo estiver OK

        Returns:
            True se a conexão está válida e funcional.

        Raises:
            SyncConfigError: Erro de configuração (token ausente, etc).
            SyncError: Erro genérico de conexão.
        """
        pass

    @abstractmethod
    def handle_webhook(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """
        Processa um webhook recebido da plataforma externa.

        Este método deve:
        1. Validar assinatura do webhook (se aplicável)
        2. Extrair dados relevantes do payload
        3. Retornar dados normalizados para atualizar o Django

        Args:
            payload: Corpo da requisição do webhook (JSON).
            headers: Cabeçalhos HTTP da requisição.

        Returns:
            Dicionário com dados normalizados:
            {
                "model_name": "Cliente",
                "django_id": 123,
                "external_id": "abc-123",
                "action": "update",  # ou "delete", "create"
                "data": {...}  # dados no formato Django
            }

        Raises:
            WebhookValidationError: Falha na validação da assinatura.
            SyncError: Erro genérico no processamento.
        """
        pass

    @abstractmethod
    def sync_existing_records(
        self,
        model_name: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Sincroniza registros existentes em lote (batch).

        Usado para sincronização inicial ou re-sincronização completa.

        Args:
            model_name: Nome do modelo Django (ex: "Cliente", "Contato").
            records: Lista de registros para sincronizar, cada um contendo:
                {
                    "django_id": int,
                    "external_id": str | None,
                    "data": dict
                }

        Returns:
            Estatísticas da sincronização:
            {
                "total": int,
                "created": int,
                "updated": int,
                "failed": int,
                "errors": list[dict]
            }

        Raises:
            SyncError: Erro genérico de sincronização.
        """
        pass

    @abstractmethod
    def get_database_id(self, model_name: str) -> str | None:
        """
        Retorna o ID do database/tabela na plataforma externa para o modelo.

        Args:
            model_name: Nome do modelo Django (ex: "Cliente", "Contato").

        Returns:
            ID do database/tabela na plataforma externa, ou None se não configurado.

        Raises:
            SyncConfigError: Erro de configuração.
        """
        pass

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """
        Verifica o estado de saúde da integração.

        Returns:
            Dicionário com informações de saúde:
            {
                "status": "healthy" | "degraded" | "down",
                "api_reachable": bool,
                "rate_limit_remaining": int | None,
                "last_sync_timestamp": str | None,
                "errors_last_hour": int,
                "message": str | None
            }
        """
        pass
