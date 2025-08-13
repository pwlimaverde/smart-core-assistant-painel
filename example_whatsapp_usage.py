"""
Exemplo de uso do serviço de envio de mensagens WhatsApp.
"""

from smart_core_assistant_painel.modules.services.features.whatsapp_services.send_message_service import (
    send_whatsapp_message,
)
from py_return_success_or_error import SuccessReturn, ErrorReturn


def main():
    """Exemplo de envio de mensagem."""
    # Dados da mensagem
    message_data = {
        "number": "5588921729550",  # Número de destino
        "textMessage": {
            "text": "Olá! Esta é uma mensagem de teste do Smart Core Assistant."
        }
    }
    
    # Envia a mensagem
    result = send_whatsapp_message(
        instance="5588921729550",  # Instância
        api_key="B6D711FCDE4D4FD5936544120E713976",  # Chave de API
        message_data=message_data
    )
    
    # Trata o resultado
    if isinstance(result, SuccessReturn):
        print("Mensagem enviada com sucesso!")
        print(f"Status code: {result.result.status_code}")
        print(f"Resposta: {result.result.text}")
    elif isinstance(result, ErrorReturn):
        print("Erro ao enviar mensagem:")
        print(result.result)


if __name__ == "__main__":
    main()