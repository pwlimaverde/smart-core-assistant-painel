import requests

from smart_core_assistant_painel.modules.ai_engine.features.whatsapp_services.domain.interfaces.whatsapp_api import (
    WhatsappApi,
)
from smart_core_assistant_painel.modules.services import SERVICEHUB


class WahaWhatsAppApi(WhatsappApi):
    def send_message(self) -> None:
        try:
            url = f"{SERVICEHUB.WHATSAPP_API_BASE_URL}/{SERVICEHUB.WHATSAPP_API_SEND_TEXT_URL}"
            headers = {
                "Content-Type": "application/json",
            }
            payload = {
                "session": self._parameters.session,
                "chatId": self._parameters.chat_id,
                "text": self._parameters.message,
            }
            requests.post(
                url=url,
                json=payload,
                headers=headers,
            )
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            raise e

    def typing(self, typing: bool) -> None:
        try:
            endpoint = (
                SERVICEHUB.WHATSAPP_API_START_TYPING_URL
                if typing
                else SERVICEHUB.WHATSAPP_API_STOP_TYPING_URL
            )
            url = f"{SERVICEHUB.WHATSAPP_API_BASE_URL}/{endpoint}"
            headers = {
                "Content-Type": "application/json",
            }
            payload = {
                "session": self._parameters.session,
                "chatId": self._parameters.chat_id,
            }
            requests.post(
                url=url,
                json=payload,
                headers=headers,
            )
        except Exception as e:
            print(f"Error starting typing: {str(e)}")
            raise e
