"""Configuração de URLs para o aplicativo Oráculo.

Este arquivo define as rotas de URL para as views do aplicativo Oráculo,
mapeando cada caminho para sua respectiva função de view.
"""

from django.urls import path

from . import views

app_name = "oraculo"

urlpatterns = [
    path("treinar_ia", views.treinar_ia, name="treinar_ia"),
    path(
        "pre-processamento/<int:id>/", views.pre_processamento, name="pre_processamento"
    ),
    path("webhook_whatsapp/", views.webhook_whatsapp, name="webhook_whatsapp"),
]
