from abc import ABC, abstractmethod

from smart_core_assistant_painel.modules.ai_engine.utils.parameters import (
    MessageParameters,
)


class WhatsappApi(ABC):
    def __init__(self, parameters: MessageParameters) -> None:
        self._parameters = parameters

    @abstractmethod
    def send_message(self) -> None:
        pass

    @abstractmethod
    def typing(self, typing: bool) -> None:
        pass
