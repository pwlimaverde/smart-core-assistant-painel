from dataclasses import dataclass
from typing import Optional

@dataclass
class MessageData:
    numero_telefone: str
    from_me: bool
    conteudo: str
    message_type: str
    message_id: str
    metadados: Optional[dict]
    nome_perfil_whatsapp: Optional[str]