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
    """Descriptografa uma string de forma segura.

    Se o valor não parecer um token Fernet (não começa com gAAAA),
    retorna o valor original para evitar erros de descriptografia em dados plain-text
    que foram marcados como criptografados por engano.
    """
    if not value or not isinstance(value, str):
        return value or ""

    # Verifica se o valor tem o prefixo padrão do Fernet
    if not value.strip().startswith("gAAAA"):
        return value

    try:
        f = get_fernet()
        return f.decrypt(value.strip().encode()).decode()
    except Exception as e:
        # Pega a chave para o log (apenas os 5 primeiros caracteres por segurança)
        key = getattr(settings, "ENCRYPTION_KEY", "MISSING")
        key_snippet = key[:5] if key else "NONE"
        val_snippet = value[:10] if value else "NONE"
        logger.error(
            f"Erro ao descriptografar valor Fernet (Key: {key_snippet}..., "
            f"Val: {val_snippet}...): {e}"
        )
        raise
