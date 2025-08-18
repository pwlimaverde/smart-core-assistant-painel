"""Views para o aplicativo de usuários.

Este módulo contém as views para o gerenciamento de usuários, incluindo
cadastro, login e atribuição de permissões.
"""
from django.contrib import auth, messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from rolepermissions.roles import assign_role


def cadastro(request: HttpRequest) -> HttpResponse:
    """Realiza o cadastro de um novo usuário.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    if request.method == "GET":
        return render(request, "cadastro.html")
    elif request.method == "POST":
        username = request.POST.get("username")
        senha = request.POST.get("senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        if not senha == confirmar_senha:
            messages.add_message(request, constants.ERROR, "As senhas não coincidem.")
            return redirect("/usuarios/cadastro/")
        if len(senha or "") < 6:
            messages.add_message(request, constants.ERROR, "A senha deve ter pelo menos 6 caracteres.")
            return redirect("/usuarios/cadastro/")
        if User.objects.filter(username=username).exists():
            messages.add_message(request, constants.ERROR, "Este nome de usuário já existe.")
            return redirect("/usuarios/cadastro/")
        if not username or not senha:
            messages.add_message(request, constants.ERROR, "Nome de usuário e senha são obrigatórios.")
            return redirect("/usuarios/cadastro/")

        User.objects.create_user(username=username, password=senha)
        return redirect("/usuarios/login")
    return redirect("/usuarios/cadastro/")


def login(request: HttpRequest) -> HttpResponse:
    """Realiza o login de um usuário.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP.
    """
    if request.method == "GET":
        return render(request, "login.html")
    elif request.method == "POST":
        username = request.POST.get("username")
        senha = request.POST.get("senha")
        user = authenticate(request, username=username or "", password=senha or "")
        if user:
            auth.login(request, user)
            return redirect("treinar_ia")
        messages.add_message(request, constants.ERROR, "Nome de usuário ou senha inválidos.")
        return redirect("login")
    return redirect("login")


def permissoes(request: HttpRequest) -> HttpResponse:
    """Exibe a página de gerenciamento de permissões.

    Args:
        request (HttpRequest): O objeto de requisição.

    Returns:
        HttpResponse: A resposta HTTP com a lista de usuários.
    """
    users = User.objects.filter(is_superuser=False)
    return render(request, "permissoes.html", {"users": users})


def tornar_gerente(request: HttpRequest, id: int) -> HttpResponseRedirect:
    """Atribui a função de gerente a um usuário.

    Args:
        request (HttpRequest): O objeto de requisição.
        id (int): O ID do usuário.

    Returns:
        HttpResponseRedirect: Redireciona para a página de permissões.
    """
    user = User.objects.get(id=id)
    assign_role(user, "gerente")
    return redirect("permissoes")
