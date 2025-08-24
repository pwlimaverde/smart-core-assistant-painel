"""Configurações Django específicas para testes."""

from typing import Any, Dict

# Importar configurações básicas PRIMEIRO
from .settings import *  # noqa: F403, F401, E402

# Configurações específicas para testes (substituem as importadas)
DEBUG = False
TESTING = True

# Usa SQLite em memória para testes mais rápidos (substitui a configuração importada)
DATABASES: Dict[str, Dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

# Desabilita Django Q para testes (substitui a configuração importada)
Q_CLUSTER: Dict[str, Any] = {
    "name": "test_cluster",
    "workers": 1,
    "timeout": 30,
    "retry": 60,
    "queue_limit": 50,
    "bulk": 10,
    "orm": "default",
    "sync": True,  # Executa tarefas sincronamente nos testes
}

# Configurações de cache para testes
CACHES: Dict[str, Dict[str, Any]] = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": 120,
    }
}

# Desabilita logging durante os testes
LOGGING: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "propagate": False,
        },
        "smart_core_assistant_painel": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}

# Desabilita autenticação de email para testes
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Configurações de segurança relaxadas para testes
SECRET_KEY = "test-secret-key-for-testing-only-not-for-production"
ALLOWED_HOSTS = ["*"]

# Desabilita CSRF para testes
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Configurações específicas para testes do projeto
DISABLE_FIREBASE = True
DISABLE_EXTERNAL_SERVICES = True

# Configurações de timezone para testes
USE_TZ = True
TIME_ZONE = "UTC"

# Configurações de arquivos estáticos para testes
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# Configurações de password hashers mais rápidas para testes
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
