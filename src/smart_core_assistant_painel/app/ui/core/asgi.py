"""Configuração ASGI para o projeto principal.

Este arquivo expõe o 'callable' ASGI como uma variável de nível de módulo
chamada ``application``.

Para mais informações sobre este arquivo, consulte a documentação do Django:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.ui.core.settings"
)

application = get_asgi_application()
