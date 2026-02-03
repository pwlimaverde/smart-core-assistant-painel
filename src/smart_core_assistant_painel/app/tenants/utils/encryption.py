import logging

from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)


def get_fernet() -> Fernet:
    """Retorna instância do Fernet usando a chave configurada."""
    key = getattr(settings, "ENCRYPTION_KEY", None)
    if not key:
        raise ValueError("ENCRYPTION_KEY não está definida nas configurações.")
    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Criptografa uma string."""
    if not value:
        return ""
    try:
        f = get_fernet()
        return f.encrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Erro ao criptografar valor: {e}")
        raise


def decrypt_value(value: str) -> str:
    """Descriptografa uma string."""
    if not value:
        return ""
    try:
        f = get_fernet()
        return f.decrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Erro ao descriptografar valor: {e}")
        # Em caso de erro, retorna string vazia ou levanta erro dependendo da criticidade
        # Aqui optamos por levantar para não retornar lixo ou falhar silenciosamente em conexões
        raise
