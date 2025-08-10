from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class MessageData:
    numero_telefone: str
    from_me: bool
    conteudo: str
    message_type: str
    message_id: str
    metadados: Optional[dict[str, Any]]
    nome_perfil_whatsapp: Optional[str]