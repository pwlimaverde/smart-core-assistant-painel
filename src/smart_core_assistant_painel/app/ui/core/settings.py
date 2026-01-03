"""Configurações do Django para o projeto principal.


Gerado por 'django-admin startproject' usando Django 5.2.1.

Para mais informações sobre este arquivo, consulte:
https://docs.djangoproject.com/en/5.2/topics/settings/

Para a lista completa de configurações e seus valores, consulte:
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

from django.contrib.messages import constants
from dotenv import load_dotenv
from decouple import config

try:
    import django_stubs_ext
except ImportError:
    django_stubs_ext = None
else:
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


# Tenant Configuration
TENANT_BASE_DOMAIN = os.getenv("TENANT_BASE_DOMAIN", "").strip()
TENANT_RESERVED_SUBDOMAINS = [
    "www",
    "api",
    "admin",
    "mail",
    "smtp",
    "ftp",
    "backoffice",
]


def _get_allowed_hosts() -> list[str]:
    """Determina a lista de hosts permitidos com base no ambiente."""
    django_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "").strip()
    hosts = []

    if django_allowed_hosts:
        hosts.extend(
            [
                host.strip()
                for host in django_allowed_hosts.split(",")
                if host.strip()
            ]
        )

    if DEBUG:
        hosts.append("*")
    else:
        hosts.extend(
            [
                "django-app",
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "host.docker.internal",
            ]
        )

    # Adicionar wildcard para subdomínios em produção se configurado
    if TENANT_BASE_DOMAIN:
        hosts.append(TENANT_BASE_DOMAIN)
        hosts.append(f".{TENANT_BASE_DOMAIN}")

    return list(set(hosts))  # Remove duplicates


ALLOWED_HOSTS = _get_allowed_hosts()


# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "pgvector.django",
    "rolepermissions",
    "django_celery_beat",
    "django_celery_results",
    "rest_framework",
    "corsheaders",
    "smart_core_assistant_painel.app.ui.core",
    "smart_core_assistant_painel.app.ui.usuarios",
    # Usa AppConfig explícito para garantir execução do ready() e sinais
    "smart_core_assistant_painel.app.ui.operacional.apps.OperacionalConfig",
    "smart_core_assistant_painel.app.ui.clientes",
    "smart_core_assistant_painel.app.ui.atendimentos",
    "smart_core_assistant_painel.app.ui.treinamento",
    "smart_core_assistant_painel.app.tenants",
    # Integração Trello ativada
    "smart_core_assistant_painel.app.trello_sync",
    # Usa AppConfig explícito para garantir execução do ready() e sinais
    # "smart_core_assistant_painel.app.clickup_sync.apps.ClickupSyncConfig",
    "smart_core_assistant_painel.app.evolution_sync.apps.EvolutionSyncConfig",
    # Desabilitado temporariamente: sincronização com Notion e plataformas
    # externas. Removido para evitar conflitos durante nova integração.
    # "smart_core_assistant_painel.app.notion_sync",
    "smart_core_assistant_painel.app.settings_manager",
]

# Flag informativa de habilitação do módulo de sincronização Notion.
# Observação: usada apenas como documentação; verifique configs por app.
NOTION_SYNC_ENABLED: bool = False

# Controle do filtro do signal de criação de etapas padrão.
# Lista de nomes de departamentos permitidos (case-insensitive).
# Se vazio, aplica a todos os departamentos.
OPERACIONAL_AUTO_ETAPAS_ALLOWED_DEPARTAMENTOS: list[str] = []

ROLEPERMISSIONS_MODULE = "smart_core_assistant_painel.app.ui.core.roles"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "smart_core_assistant_painel.app.ui.core.middleware.AdminStaffRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware Multi-Tenant (SaaS) - ORDEM IMPORTA!
    "smart_core_assistant_painel.app.tenants.middleware.TenantMiddleware",
    "smart_core_assistant_painel.app.tenants.middleware.TenantConfigMiddleware",
]

ROOT_URLCONF = "smart_core_assistant_painel.app.ui.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "core", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "smart_core_assistant_painel.app.ui.core.context_processors.project_version",
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


DATABASE_ROUTERS = [
    "smart_core_assistant_painel.app.tenants.db_router.TenantDatabaseRouter",
]


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


# Auth Redirects
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/


STATIC_URL = "static/"
# Centraliza assets opcionais em core/static e permite AppDirectoriesFinder
STATICFILES_DIRS = (os.path.join(BASE_DIR, "core", "static"),)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR.parent, "media")
MEDIA_URL = "/media/"


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


MESSAGE_TAGS = {
    constants.SUCCESS: "bg-green-50 text-green-700",
    constants.ERROR: "bg-red-50 text-red-700",
}

ENCRYPTION_KEY = config("ENCRYPTION_KEY", default=None)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Configurações de serviços externos (ambiente_chat)
# Estas variáveis permitem que a aplicação Django consuma Evolution API e Ollama
# que rodam em outro ambiente Docker separado.
EVOLUTION_API_URL = os.getenv(
    "EVOLUTION_API_URL", "http://localhost:8080"
).strip()
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://192.168.3.127:11434"
).strip()

# Configurações DRF e JWT
REST_FRAMEWORK = {
    # Exige autenticação por JWT para endpoints protegidos do adapter
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Durações dos tokens JWT controladas por variáveis de ambiente
try:
    _jwt_access_min = int(os.getenv("JWT_ACCESS_EXPIRES_MIN", "15"))
    _jwt_refresh_min = int(os.getenv("JWT_REFRESH_EXPIRES_MIN", "60"))
except Exception:
    _jwt_access_min = 15
    _jwt_refresh_min = 60

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": __import__("datetime").timedelta(
        minutes=_jwt_access_min
    ),
    "REFRESH_TOKEN_LIFETIME": __import__("datetime").timedelta(
        minutes=_jwt_refresh_min
    ),
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# CORS configuration
def _get_cors_allowed_origins() -> list[str]:
    """Lista de origens permitidas para CORS.

    Lê da variável de ambiente `CORS_ALLOWED_ORIGINS` separada por vírgulas.
    Em desenvolvimento, libera localhost:4200 por padrão para o Flutter web.
    """
    origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if origins_env:
        return [o.strip() for o in origins_env.split(",") if o.strip()]
    # Defaults para ambiente de desenvolvimento
    return [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ]


CORS_ALLOWED_ORIGINS = _get_cors_allowed_origins()

# Adiciona domínio base para CORS quando configurado
if TENANT_BASE_DOMAIN:
    CORS_ALLOWED_ORIGINS.extend(
        [
            f"https://{TENANT_BASE_DOMAIN}",
            # Nota: CORS não suporta wildcard parcial, subdomínios específicos
            # devem ser adicionados via CORS_ALLOWED_ORIGINS ou usar regex
        ]
    )

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Em desenvolvimento, aceita qualquer origem

# Para eventuais POST vindos do frontend
# Para eventuais POST vindos do frontend e subdomínios
CSRF_TRUSTED_ORIGINS = [
    o.replace("http://", "https://") if o.startswith("http://") else o
    for o in CORS_ALLOWED_ORIGINS
]

if TENANT_BASE_DOMAIN:
    CSRF_TRUSTED_ORIGINS.extend(
        [
            f"https://{TENANT_BASE_DOMAIN}",
            f"https://*.{TENANT_BASE_DOMAIN}",
        ]
    )


JAZZMIN_SETTINGS = {
    "site_title": "Smart Core Assistant",
    "site_header": "Smart Core Assistant",
    "site_brand": "Smart Core Assistant",
    "site_logo": "img/logo_branca_smart_v2.png",
    "login_logo": "img/logo_branca_smart_v2.png",
    "login_logo_dark": "img/logo_branca_smart_v2.png",
    "site_logo_classes": "img-fluid",
    "site_icon": None,
    "welcome_sign": "Bem-vindo ao Smart Core Assistant",
    "copyright": "Smart Core Assistant",
    "search_model": ["ui_usuarios.User", "ui_clientes.Cliente"],
    "user_avatar": None,
    "topmenu_links": [
        {
            "name": "Website",
            "url": "/",
            "icon": "fas fa-home",
        },
        {
            "name": "Permissões",
            "url": "permissoes",
            "permissions": ["auth.view_user"],
        },
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["ui_atendimentos", "ui_clientes", "ui_usuarios"],
    "icons": {
        "auth": "fas fa-users-cog",
        "ui_usuarios.user": "fas fa-user-shield",
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        "atendimentos.Atendimento": "fas fa-headset",
        "atendimentos.Mensagem": "fas fa-comments",
        "clientes.Cliente": "fas fa-user-tie",
        "clientes.Contato": "fas fa-address-book",
        "trello_sync.TrelloBoard": "fab fa-trello",
        "trello_sync.TrelloList": "fas fa-list",
        "trello_sync.TrelloCard": "fas fa-clipboard-list",
        "trello_sync.TrelloMember": "fas fa-users",
        "trello_sync.TrelloWebhookEvent": "fas fa-satellite-dish",
        # Celery & Periodic Tasks
        "django_celery_beat.PeriodicTask": "fas fa-clock",
        "django_celery_beat.IntervalSchedule": "fas fa-stopwatch",
        "django_celery_beat.CrontabSchedule": "fas fa-calendar-alt",
        "django_celery_beat.SolarSchedule": "fas fa-sun",
        "django_celery_beat.ClockedSchedule": "fas fa-hourglass-half",
        "django_celery_results.TaskResult": "fas fa-tasks",
        "django_celery_results.GroupResult": "fas fa-layer-group",
        "evolution_sync.EvolutionContact": "fas fa-id-card",
        "evolution_sync.WhiteList": "fas fa-list-ul",
        "operacional.Departamento": "fas fa-building",
        "operacional.Atendente": "fas fa-user-check",
        "operacional.AppInstance": "fas fa-mobile-alt",
        "operacional.FluxoAtendimento": "fas fa-project-diagram",
        "operacional.EtapaFluxo": "fas fa-step-forward",
        "atendimentos.MovimentoFluxo": "fas fa-exchange-alt",
        "treinamento.Treinamento": "fas fa-graduation-cap",
        "treinamento.Documento": "fas fa-file-alt",
        "treinamento.QueryCompose": "fas fa-brain",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": "css/admin_custom_v3.css",
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# =============================================================================
# CELERY - Configuração para SaaS Multi-Tenant
# Dimensionado para Hostinger KVM 2 (2 vCPU, 8GB RAM, 10 clientes)
# =============================================================================
_redis_password = os.getenv("REDIS_PASSWORD", "")
_redis_auth = f":{_redis_password}@" if _redis_password else ""
CELERY_BROKER_URL = (
    f"redis://{_redis_auth}"
    f"{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/0"
)

CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"

# Serialização segura (sem pickle)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Timezone
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Concorrência otimizada para 2 vCPU
CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "3"))
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Melhor para tasks longas (IA)

# Timeouts alinhados com processamento de LLM
CELERY_TASK_SOFT_TIME_LIMIT = 120  # Aviso 2 min antes
CELERY_TASK_TIME_LIMIT = 300  # Hard kill 5 min

# Robustez
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Resultados
CELERY_RESULT_EXPIRES = 3600  # 1 hora
CELERY_RESULT_EXTENDED = True

# Beat Scheduler
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
