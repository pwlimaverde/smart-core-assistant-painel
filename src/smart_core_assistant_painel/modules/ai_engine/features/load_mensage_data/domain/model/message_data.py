"""Define o modelo de dados para uma mensagem normalizada.

Este módulo contém a dataclass que representa uma mensagem após ter sido
processada e normalizada a partir de um payload de webhook.

Classes:
    MessageData: A estrutura de dados para uma mensagem normalizada.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class MessageData:
    """Representa os dados normalizados de uma mensagem recebida.

    Attributes:
        instance (str): A instância da qual a mensagem se originou.
        api_key (str): A chave de API associada à instância.
        numero_telefone (str): O número de telefone do remetente.
        from_me (bool): True se a mensagem foi enviada pelo bot, False caso contrário.
        conteudo (str): O conteúdo principal da mensagem (texto, legenda, etc.).
        message_type (str): O tipo da mensagem (ex: 'conversation', 'imageMessage').
        message_id (str): O ID único da mensagem.
        metadados (Optional[dict[str, Any]]): Metadados adicionais
            (ex: URL de mídia, localização).
        nome_perfil_whatsapp (Optional[str]): O nome de perfil do remetente no WhatsApp.
    """

    instance: str
    api_key: str
    numero_telefone: str
    from_me: bool
    conteudo: str
    message_type: str
    message_id: str
    metadados: Optional[dict[str, Any]]
    nome_perfil_whatsapp: Optional[str]
