"""Serviços do app Atendimentos.

Este módulo centraliza a lógica de negócio para processamento
de mensagens e orquestração de atendimentos.
"""

from loguru import logger

from .attendance_orchestrator import (
    AttendanceOrchestrator,
)
from .attendance_structure_manager import AttendanceStructureManager
from .bot_rules_engine import BotRulesEngine
from .interfaces import (
    AttendanceOrchestratorInterface,
    AttendanceStructureManagerInterface,
    BotRulesEngineInterface,
    MessageAnalyzerInterface,
)
from .message_analyzer import MessageAnalyzer

__all__ = [
    # Interfaces
    "MessageAnalyzerInterface",
    "AttendanceStructureManagerInterface",
    "BotRulesEngineInterface",
    "AttendanceOrchestratorInterface",
    # Implementations
    "MessageAnalyzer",
    "AttendanceStructureManager",
    "BotRulesEngine",
    "AttendanceOrchestrator",
    # Tasks/Factories
    "create_orchestrator",
]


def create_orchestrator() -> AttendanceOrchestrator:
    """Cria orquestrador com todas as dependências injetadas.

    Factory function para facilitar criação do orquestrador
    com todas as dependências corretamente configuradas.

    Returns:
        Instância configurada do AttendanceOrchestrator.
    """
    message_analyzer = MessageAnalyzer()
    structure_manager = AttendanceStructureManager()
    rules_engine = BotRulesEngine()

    return AttendanceOrchestrator(
        message_analyzer=message_analyzer,
        structure_manager=structure_manager,
        rules_engine=rules_engine,
    )
