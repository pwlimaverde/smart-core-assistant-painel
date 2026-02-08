"""Configurações específicas para execução de testes.

Este módulo importa todas as configurações padrão e sobrescreve algumas
opções para tornar os testes mais rápidos e isolados, sem alterar o
comportamento funcional esperado da aplicação.
"""

from .settings import *  # noqa: F401,F403

# Ativa debug durante os testes
DEBUG = True

# Hash de senha mais rápido para acelerar criação de usuários em testes
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Backend de e-mail em memória para evitar I/O externo
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Cache em memória para isolamento e performance em testes
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Hosts permitidos durante os testes (inclui testserver do Django)
ALLOWED_HOSTS = ["*", "testserver", "localhost", "127.0.0.1"]

# Mantemos DATABASES do settings base (PostgreSQL),
# garantindo compatibilidade com campos específicos como VectorField (pgvector).
