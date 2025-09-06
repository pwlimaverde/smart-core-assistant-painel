"""Configuração de URL para o projeto principal.

A lista `urlpatterns` roteia URLs para views. Para mais informações, consulte:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Exemplos:
    Function views
        1. Adicione uma importação:  from my_app import views
        2. Adicione uma URL a urlpatterns:  path('', views.home, name='home')
    Class-based views
        1. Adicione uma importação:  from other_app.views import Home
        2. Adicione uma URL a urlpatterns:  path('', Home.as_view(), name='home')
    Including another URLconf
        1. Importe a função include(): from django.urls import include, path
        2. Adicione uma URL a urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path(
        "usuarios/",
        include("smart_core_assistant_painel.app.ui.usuarios.urls"),
    ),
    path(
        "oraculo/",
        include(
            "smart_core_assistant_painel.app.ui.oraculo.urls",
            namespace="oraculo",
        ),
    ),
]
