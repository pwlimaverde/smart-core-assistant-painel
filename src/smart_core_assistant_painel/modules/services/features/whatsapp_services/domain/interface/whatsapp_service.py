from abc import ABC, abstractmethod


class WhatsAppService(ABC):
    """Interface para o serviço de WhatsApp."""

    @abstractmethod
    def send_message(
        self,
        instance: str,
        api_key: str,
        number: str,
        text: str,
    ) -> None:
        pass

    @abstractmethod
    def _typing(
        self,
        typing: bool,
        instance: str,
        number: str,
        api_key: str,
    ) -> None:
        pass
