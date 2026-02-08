"""Motor de regras de negócio do bot.

Este módulo contém a lógica para avaliar se o bot pode responder
automaticamente a um atendimento com base em regras de negócio.
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger

from .interfaces import BotRulesEngineInterface

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.atendimentos.models import (
        Atendimento,
    )


class BotRulesEngine(BotRulesEngineInterface):
    """[ATD-LIF-003] Motor de regras de negócio do bot.

    Responsabilidades:
    - Avaliar se bot pode responder
    - Aplicar regras de negócio
    - Verificar interação humana
    """

    def can_bot_respond(
        self,
        attendance: Optional["Atendimento"],
        api_key: Optional[str] = None,
    ) -> bool:
        """Verifica se o bot pode responder automaticamente a um atendimento.

        Regras:
        - Verifica permissão da instância (AppInstance.resposta_bot)
        - Não responde se a flag `bot_pode_atender` for False
        - Não responde se há interação humana (legado/redundante, mas mantido por segurança)

        Args:
            attendance: Atendimento a ser verificado.
            api_key: Chave de API da instância que recebeu a mensagem.

        Returns:
            True se o bot pode responder, False caso contrário.
        """
        if not attendance:
            return False

        # 0. Nova Regra: Verifica se a instância permite resposta do bot.
        # Se api_key fornecida e instância disable, return False IMEDIATAMENTE.
        if api_key and not self._is_instance_bot_enabled(api_key):
            logger.info(
                f"Bot não pode responder atendimento {attendance.id}: "
                f"instância da api_key={api_key[:8]}... bloqueada (resposta_bot=False)"
            )
            return False

        # 1. Prioridade máxima: Se houve interação humana, o bot NÃO responde.
        # Isso bloqueia permanentemente o bot após intervenção humana.
        if self._has_human_interaction(attendance):
            logger.info(
                f"Bot não pode responder atendimento {attendance.id}: interação humana detectada"
            )
            return False

        # 2. Flag explícita: Se True, permite resposta (ignorando departamento).
        if attendance.bot_pode_atender:
            return True

        # 3. Se a flag for False, bloqueia.
        if not attendance.bot_pode_atender:
            logger.info(
                f"Bot não pode responder atendimento {attendance.id}: bot_pode_atender=False"
            )
            return False

        return True

    def _is_instance_bot_enabled(self, api_key: str) -> bool:
        """Verifica se a instância permite resposta automática do bot.

        Args:
            api_key: Chave de API da instância.

        Returns:
            True se permitido (ou se instância não encontrada - fail-safe),
            False se bloqueado explicitamente.
        """
        try:
            from smart_core_assistant_painel.app.operacional.models import (
                AppInstance,
            )

            instance = AppInstance.objects.filter(
                api_key=api_key, active=True
            ).first()

            if not instance:
                logger.warning(
                    f"AppInstance não encontrada para api_key={api_key[:8]}..."
                )
                return True  # Fail-safe: permite se não encontrar instância

            return instance.resposta_bot

        except Exception as e:
            logger.error(f"Erro ao verificar resposta_bot da instância: {e}")
            return True  # Fail-safe: permite em caso de erro

    def _has_human_interaction(self, attendance: "Atendimento") -> bool:
        """Verifica se há interação humana no atendimento.

        Args:
            attendance: Atendimento a verificar.

        Returns:
            True se há mensagens de atendente ou atendente atribuído.
        """
        from smart_core_assistant_painel.app.atendimentos.models import (
            TipoRemetente,
        )

        # Verifica mensagens de atendente humano
        mensagens_manager = getattr(attendance, "mensagens", None)
        has_human_messages = False

        if mensagens_manager is not None:
            has_human_messages = mensagens_manager.filter(
                remetente=TipoRemetente.ATENDENTE_HUMANO
            ).exists()

        return has_human_messages

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
