"""Motor de regras de negócio do bot.

Este módulo contém a lógica para avaliar se o bot pode responder
automaticamente a um atendimento com base em regras de negócio.
"""

from typing import Optional, TYPE_CHECKING

from loguru import logger

from .interfaces import BotRulesEngineInterface

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Atendimento,
        TipoRemetente,
    )
    from smart_core_assistant_painel.app.ui.operacional.models import (
        Departamento,
    )


class BotRulesEngine(BotRulesEngineInterface):
    """Motor de regras de negócio do bot.

        Responsabilidades:
        - Avaliar se bot pode responder
        - Aplicar regras de negócio
        - Ver

    ificar interação humana
    """

    def can_bot_respond(self, attendance: Optional["Atendimento"]) -> bool:
        """Verifica se o bot pode responder automaticamente a um atendimento.

        Regras:
        - Somente responde quando o atendimento está no departamento "Atendimento"
        - Não responde se há interação humana (mensagens de atendente ou
          atendente humano atribuído)

        Args:
            attendance: Atendimento a ser verificado.

        Returns:
            True se o bot pode responder, False caso contrário.
        """
        if attendance is None:
            return False

        try:
            # Verifica departamento atual
            if not self._is_in_bot_department(attendance):
                return False

            # Verifica se há interação humana
            if self._has_human_interaction(attendance):
                return False

            return True

        except Exception as e:
            logger.error(f"Erro ao verificar se o bot pode responder: {e}")
            return False

        # return False

    def _is_in_bot_department(self, attendance: "Atendimento") -> bool:
        """Verifica se atendimento está no departamento do bot.

        Se não houver departamento definido, configura estrutura padrão
        e retorna True (permite bot responder).

        Args:
            attendance: Atendimento a verificar.

        Returns:
            True se está no departamento "Atendimento" ou sem departamento.
        """
        from smart_core_assistant_painel.app.ui.operacional.models import (
            Departamento,
        )

        dep_atual = getattr(attendance, "departamento", None)

        # Se for um departamento diferente de "Atendimento", bloqueia
        if isinstance(dep_atual, Departamento) and (
            getattr(dep_atual, "nome", None) != "Atendimento"
        ):
            return False

        # Se não houver departamento, configura estrutura padrão
        if dep_atual is None or not isinstance(dep_atual, Departamento):
            self._configure_default_attendance(attendance)
            return True

        return True

    def _has_human_interaction(self, attendance: "Atendimento") -> bool:
        """Verifica se há interação humana no atendimento.

        Args:
            attendance: Atendimento a verificar.

        Returns:
            True se há mensagens de atendente ou atendente atribuído.
        """
        from smart_core_assistant_painel.app.ui.atendimentos.models import (
            TipoRemetente,
        )

        # Verifica mensagens de atendente humano
        mensagens_manager = getattr(attendance, "mensagens", None)
        has_human_messages = False

        if mensagens_manager is not None:
            has_human_messages = mensagens_manager.filter(
                remetente=TipoRemetente.ATENDENTE_HUMANO
            ).exists()

        # Verifica se há atendente atribuído
        has_human_attendant = (
            getattr(attendance, "atendente_humano", None) is not None
        )

        return has_human_messages or has_human_attendant

    def _configure_default_attendance(self, attendance: "Atendimento") -> None:
        """Configura atendimento com estrutura padrão.

        Esta é uma função auxiliar que delega para o
        AttendanceStructureManager. Evita dependência circular
        importando apenas quando necessário.

        Args:
            attendance: Atendimento a configurar.
        """
        try:
            from .attendance_structure_manager import (
                AttendanceStructureManager,
            )

            manager = AttendanceStructureManager()
            manager.configure_default_attendance(attendance)

        except Exception as e:
            logger.error(f"Erro ao configurar atendimento padrão: {e}")
