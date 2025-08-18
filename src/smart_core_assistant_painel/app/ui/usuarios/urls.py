"""Configuração de URLs para o aplicativo de usuários.

Este arquivo define as rotas de URL para as views do aplicativo de usuários,
mapeando cada caminho para sua respectiva função de view.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("cadastro/", views.cadastro, name="cadastro"),
    path("login/", views.login, name="login"),
    path("permissoes/", views.permissoes, name="permissoes"),
    path("tornar_gerente/<int:id>", views.tornar_gerente, name="tornar_gerente"),
]
