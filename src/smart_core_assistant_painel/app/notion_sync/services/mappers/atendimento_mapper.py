import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smart_core_assistant_painel.app.notion_sync.models import (
        AtendimentoSync,
    )
    from smart_core_assistant_painel.app.ui.atendimentos.models import (
        Atendimento,
    )


class AtendimentoMapper:
    """
    Classe responsável por mapear e transformar dados do Atendimento.
    """

    @staticmethod
    def get_notion_schema() -> dict:
        """
