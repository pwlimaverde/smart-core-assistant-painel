"""Configurações do Django para o projeto principal.


Gerado por 'django-admin startproject' usando Django 5.2.1.

Para mais informações sobre este arquivo, consulte:
https://docs.djangoproject.com/en/5.2/topics/settings/

Para a lista completa de configurações e seus valores, consulte:
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

import django_stubs_ext
from django.contrib.messages import constants
from dotenv import load_dotenv

django_stubs_ext.monkeypatch()
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY_DJANGO")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


def _get_allowed_hosts() -> list[str]:
    """Determina a lista de hosts permitidos com base no ambiente."""
    django_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "").strip()
    if django_allowed_hosts:
        return [
            host.strip()
            for host in django_allowed_hosts.split(",")
            if host.strip()
        ]

    if DEBUG:
        return ["*"]

    return [
        "django-app",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "host.docker.internal",
    ]


ALLOWED_HOSTS = _get_allowed_hosts()


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "pgvector.django",
    "rolepermissions",
    "django_q",
    "smart_core_assistant_painel.app.ui.usuarios",
    "smart_core_assistant_painel.app.ui.oraculo",
]

ROLEPERMISSIONS_MODULE = "smart_core_assistant_painel.app.ui.core.roles"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "smart_core_assistant_painel.app.ui.core.middleware.AdminStaffRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "smart_core_assistant_painel.app.ui.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "smart_core_assistant_painel.app.ui.core.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "smart_core_db"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres123"),
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "OPTIONS": {
            # Define o modo de SSL via variável de ambiente; desabilita por padrão
            # pois a conexão direta bem-sucedida ocorreu apenas com sslmode=disable.
            "sslmode": os.getenv("POSTGRES_SSLMODE", "disable"),
            # Define tempo máximo de tentativa de conexão (em segundos)
            "connect_timeout": os.getenv("POSTGRES_CONNECT_TIMEOUT", "5"),
        },
    }
}


# Cache configuration
# https://docs.djangoproject.com/en/5.2/ref/settings/#caches

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 300,  # 5 minutos como padrão
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/


STATIC_URL = "static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "templates/static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR.parent, "media")
MEDIA_URL = "/media/"

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


MESSAGE_TAGS = {
    constants.SUCCESS: "bg-green-50 text-green-700",
    constants.ERROR: "bg-red-50 text-red-700",
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

Q_CLUSTER = {
    "name": "smart_core_cluster",
    "workers": 2,
    "timeout": 300,
    "retry": 300,
    "queue_limit": 200,
    "orm": "default",
    "secret_key": SECRET_KEY,  # Garante que Q Cluster use a mesma SECRET_KEY
    # Configuração do Redis broker
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": 0,
        "password": os.getenv("REDIS_PASSWORD", None),
    },
}

# Configurações de serviços externos (ambiente_chat)
# Estas variáveis permitem que a aplicação Django consuma Evolution API e Ollama
# que rodam em outro ambiente Docker separado.
EVOLUTION_API_URL = os.getenv(
    "EVOLUTION_API_URL", "http://localhost:8080"
).strip()
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://192.168.3.127:11434"
).strip()
