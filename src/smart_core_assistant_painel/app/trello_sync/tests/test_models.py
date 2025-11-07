from django.test import TestCase

from smart_core_assistant_painel.app.trello_sync.models import TrelloBoard


class ModelsStrTests(TestCase):
    def test_board_str(self) -> None:
        # Cria objeto in-memory (sem dependências de fluxo) para testar __str__
        board = TrelloBoard(
            id=1,
            external_id="b123",
            name="Board Test",
        )
        self.assertIn("Board Test", str(board))