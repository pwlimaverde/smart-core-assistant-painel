"""Interfaces para os serviços do app Atendimentos.

Este módulo define os contratos (interfaces) que os serviços devem seguir,
garantindo baixo acoplamento e alta testabilidade através de injeção de
dependências.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.atendimentos.models import (
        Atendimento,
        Mensagem,
    )
    from smart_core_assistant_painel.app.operacional.models import (
        Departamento,
        FluxoAtendimento,
    )


class MessageAnalyzerInterface(ABC):
    """Interface para análise de mensagens.

    Responsável por detectar intenções, extrair entidades e processar
    informações de contato a partir de mensagens.
    """

    @abstractmethod
    def analyze_message_content(self, message_id: int) -> dict[str, Any]:
        """Analisa o conteúdo da mensagem para detectar intenção e entidades.

        Args:
            message_id: ID da mensagem a ser analisada.

        Returns:
            Dicionário com intenções e entidades detectadas.
        """
        pass

    @abstractmethod
    def process_contact_entities(
        self,
        message: "Mensagem",
        entity_types: list[dict[str, Any]],
    ) -> None:
        """Processa entidades extraídas para atualizar dados do contato.

        Args:
            message: Mensagem contendo as entidades.
            entity_types: Lista de tipos de entidades a processar.
        """
        pass


class AttendanceStructureManagerInterface(ABC):
    """Interface para gerenciamento de estrutura de atendimento.

    Responsável por garantir a existência de departamentos, fluxos e
    etapas necessários para o funcionamento do sistema.
    """

    @abstractmethod
    def ensure_default_structure(
        self,
    ) -> tuple["Departamento", "FluxoAtendimento"]:
        """Garante que exista a estrutura padrão de atendimento.

        Cria o departamento 'Atendimento' e o fluxo 'Atendimento Inicial'
        se não existirem.

        Returns:
            Tupla com (departamento, fluxo) criados ou existentes.
        """
        pass

    @abstractmethod
    def get_available_flows(self) -> dict[str, str]:
        """Retorna fluxos de atendimento disponíveis.

        Returns:
            Dicionário no formato {"nome_fluxo - nome_departamento": "descrição"}.
        """
        pass

    @abstractmethod
    def configure_default_attendance(self, attendance: "Atendimento") -> None:
        """Configura um atendimento para usar a estrutura padrão.

        Args:
            attendance: Atendimento a ser configurado.
        """
        pass


class BotRulesEngineInterface(ABC):
    """Interface para motor de regras de negócio do bot.

    Responsável por avaliar regras de negócio e determinar
    comportamentos do bot.
    """

    @abstractmethod
    def can_bot_respond(
        self,
        attendance: Optional["Atendimento"],
        api_key: Optional[str] = None,
    ) -> bool:
        """Verifica se o bot pode responder automaticamente a um atendimento.

        Regras:
        - Verifica permissão da instância (AppInstance.resposta_bot)
        - Somente responde quando o atendimento está no departamento "Atendimento"
        - Não responde se há interação humana

        Args:
            attendance: Atendimento a ser verificado.
            api_key: Chave de API da instância que recebeu a mensagem.

        Returns:
            True se o bot pode responder, False caso contrário.
        """
        pass


class AttendanceOrchestratorInterface(ABC):
    """Interface para orquestração de processamento de atendimentos.

    Coordena o fluxo completo de processamento de mensagens agendadas,
    integrando todos os services para criar/atualizar atendimentos e
    gerar respostas do bot.
    """

    @abstractmethod
    def process_contact_response(
        self,
        contact_id: int,
        api_key: Optional[str] = None,
    ) -> None:
        """Processa resposta para um contato a partir de mensagens agendadas.

        Fluxo:
        1. Obtém mensagens do buffer
        2. Cria ou obtém atendimento
        3. Processa cada mensagem
        4. Gera resposta do bot (se aplicável)
        5. Envia resposta via WhatsApp
        6. Limpa buffer

        Args:
            contact_id: ID do contato a processar.
            api_key: Chave de API para envio de mensagens (opcional).
        """
        pass
