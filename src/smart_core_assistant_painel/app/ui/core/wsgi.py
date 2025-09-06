"""Configuração WSGI para o projeto principal.

Este arquivo expõe o 'callable' WSGI como uma variável de nível de módulo
chamada ``application``.

Para mais informações sobre este arquivo, consulte a documentação do Django:
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_core_assistant_painel.app.ui.core.settings",
)

application = get_wsgi_application()
