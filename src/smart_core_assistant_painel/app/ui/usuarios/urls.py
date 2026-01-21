"""Configuração de URLs para o aplicativo de usuários.

Este arquivo define as rotas de URL para as views do aplicativo de usuários,
mapeando cada caminho para sua respectiva função de view.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import CustomPasswordResetForm

urlpatterns = [
    path("cadastro/", views.cadastro, name="cadastro"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # Password Reset
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="usuarios/password_reset_form.html",
            email_template_name="usuarios/password_reset_email.html",
            html_email_template_name="usuarios/password_reset_email.html",
            subject_template_name="usuarios/password_reset_subject.txt",
            form_class=CustomPasswordResetForm,
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="usuarios/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="usuarios/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="usuarios/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("permissoes/", views.permissoes, name="permissoes"),
    path(
        "tornar_gerente/<int:id>", views.tornar_gerente, name="tornar_gerente"
    ),
    path(
        "dashboard-gerente/", views.dashboard_gerente, name="dashboard_gerente"
    ),
]
